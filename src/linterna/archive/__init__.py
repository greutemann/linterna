"""M1 — Núcleo "archivo-primero" (sin LLM).

Resuelve verificaciones consultando primero el archivo de verificaciones humanas
previas (ClaimReview / Google Fact Check) + caché. Sin razonamiento generativo: si no
hay verificación previa validada, se abstiene (`INSUFICIENTE`).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from linterna.types import Light, Source, VerificationResult, Verdict
from linterna.validation import assert_all_recovered

from .cache import Cache


@dataclass(frozen=True)
class RawReview:
    """Una verificación previa cruda devuelta por un proveedor de ClaimReview."""

    matched_claim: str
    textual_rating: str
    source: Source


class ClaimReviewProvider(Protocol):
    """Proveedor de verificaciones humanas previas (p. ej. Google Fact Check Tools)."""

    def search(self, claim: str) -> list[RawReview]: ...


# Calificaciones -> veredicto por palabras clave (las calificaciones reales son frases:
# "Bulo", "Falso porque...", "Verdad a medias", etc.). Se evalúan en orden sobre el texto
# normalizado (sin acentos, minúsculas). Determinístico y auditable.
_RATING_KEYWORDS: tuple[tuple[tuple[str, ...], Verdict], ...] = (
    (("engañoso", "enganoso", "misleading", "a medias", "media verdad", "verdad a medias",
      "impreciso", "exagerado", "fuera de contexto", "sin contexto"), Verdict.MISLEADING),
    (("falso", "false", "bulo", "fake", "mentira", "incorrecto", "enganos", "no es cierto",
      "desinformacion", "pseudociencia"), Verdict.FALSE),
    (("verdadero", "true", "correcto", "cierto", "real"), Verdict.TRUE),
    (("disputado", "discutido", "en disputa", "debate"), Verdict.DISPUTED),
)

# Palabras vacías para comparar similitud de afirmaciones (es/en).
_STOPWORDS = frozenset(
    "el la los las un una unos unas de del que en y a es son por con se su sus al lo como "
    "mas para o u e ni si no the of to and in is are for on".split()
)
# Umbral de solapamiento (coeficiente sobre el conjunto menor) para considerar que el
# ClaimReview habla de la MISMA afirmación que la consulta.
_SIMILARITY_THRESHOLD = 0.6

# Marcadores de polaridad: si aparecen en la afirmación verificada pero NO en la consulta
# (o viceversa), es probable que el veredicto tenga sentido OPUESTO al de la consulta
# (ej. verificaron "el viaje a la luna fue un montaje"→Falso, pero consultaste que SÍ llegó).
# La comparación por palabras no detecta negaciones; esto sí, de forma acotada.
_NEGATION_WORDS = frozenset({"no", "nunca", "jamas", "tampoco", "ningun", "ninguna", "ningún"})
_HOAX_MARKERS = (
    "montaje", "farsa", "invento", "inventada", "bulo", "fake", "hoax", "conspiracion",
    "mentira", "engano", "enganos", "falso", "falsa", "ficticio", "ficticia",
)

_VERDICT_TO_LIGHT: dict[Verdict, Light] = {
    Verdict.TRUE: Light.GREEN,
    Verdict.FALSE: Light.RED,
    Verdict.MISLEADING: Light.YELLOW,
    Verdict.DISPUTED: Light.YELLOW,
    Verdict.INSUFFICIENT: Light.GREY,
}


def _normalize(text: str) -> str:
    """Normaliza para comparar/cachear: sin acentos, minúsculas, espacios colapsados."""
    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents).strip().lower()


def _rating_to_verdict(textual_rating: str) -> Verdict:
    r = _normalize(textual_rating)
    for keywords, verdict in _RATING_KEYWORDS:
        if any(k in r for k in keywords):
            return verdict
    # Calificación no reconocida: hay evidencia humana pero no la clasificamos a
    # ciegas. Se muestra como DISPUTADO (amarillo) para que la persona juzgue.
    return Verdict.DISPUTED


def _content_words(text: str) -> set[str]:
    return {w for w in _normalize(text).split() if w not in _STOPWORDS and len(w) > 2}


def _same_claim(claim: str, matched: str) -> bool:
    """¿El ClaimReview habla de la misma afirmación? Evita aplicar el veredicto de una
    verificación que Google devolvió por proximidad pero es de otro tema."""
    a, b = _content_words(claim), _content_words(matched)
    if not a or not b:
        return False
    overlap = len(a & b) / min(len(a), len(b))
    return overlap >= _SIMILARITY_THRESHOLD


def _is_negated(text: str) -> bool:
    """¿El texto tiene polaridad negativa? (negación o marco de 'bulo/montaje')."""
    tn = _normalize(text)
    words = set(tn.split())
    return any(w in words for w in _NEGATION_WORDS) or any(m in tn for m in _HOAX_MARKERS)


def _polarity_mismatch(claim: str, matched: str) -> bool:
    """¿La afirmación verificada tiene polaridad OPUESTA a la consulta?

    La polaridad de un texto es BINARIA (¿tiene algún marcador de negación/bulo?), no
    por-palabra: una afirmación compuesta («el alunizaje fue falso y nunca llegó») usa
    varios marcadores para UNA sola negación. Comparar marcador por marcador invertía mal
    cuando ambos lados negaban con palabras distintas."""
    return _is_negated(claim) != _is_negated(matched)


class ArchiveVerifier:
    """Pipeline archivo-primero: caché -> proveedor -> validación -> veredicto/abstención."""

    def __init__(self, *, provider: ClaimReviewProvider, cache: Cache) -> None:
        self._provider = provider
        self._cache = cache

    def verify(self, claim: str) -> VerificationResult:
        key = _normalize(claim)

        cached = self._cache.get(key)
        if cached is not None:
            return cached

        reviews = self._provider.search(claim)
        result = self._build_result(claim, reviews)
        self._cache.set(key, result)
        return result

    def _build_result(self, claim: str, reviews: list[RawReview]) -> VerificationResult:
        # Solo conservamos verificaciones que hablan de la MISMA afirmación (compara con
        # el texto verificado, o el título como respaldo). Evita el mislabeling de aplicar
        # el veredicto de un ClaimReview vecino pero de otro tema.
        relevant = [
            r for r in reviews
            if _same_claim(claim, r.matched_claim) or _same_claim(claim, r.source.title)
        ]
        if not relevant:
            return self._abstain()

        recovered = tuple(r.source for r in relevant)
        # Validación determinística: toda fuente de salida debe estar recuperada.
        sources = assert_all_recovered(recovered, recovered)

        top = relevant[0]
        # Polaridad opuesta (ej. verificaron "fue un montaje"→Falso, consultaste que SÍ pasó):
        # el veredicto se INVIERTE por lógica proposicional (¬A falsa ⟹ A verdadera). Es
        # determinístico y transparente: la explicación muestra la afirmación contraria y su
        # calificación original. Ver docs/proposal-polaridad.md.
        if _polarity_mismatch(claim, top.matched_claim):
            return self._inverted_or_related(top, sources)

        verdict = _rating_to_verdict(top.textual_rating)
        return VerificationResult(
            verdict=verdict,
            light=_VERDICT_TO_LIGHT[verdict],
            explanation=self._explain(top),
            sources=sources,
        )

    @staticmethod
    def _inverted_or_related(review: RawReview, sources: tuple[Source, ...]) -> VerificationResult:
        original = _rating_to_verdict(review.textual_rating)
        # Solo se invierten los veredictos nítidos; Engañoso/Disputado no sobreviven una
        # negación con su matiz intacto -> se muestran como verificación relacionada.
        inverted = {Verdict.FALSE: Verdict.TRUE, Verdict.TRUE: Verdict.FALSE}.get(original)
        if inverted is None:
            return VerificationResult(
                verdict=Verdict.INSUFFICIENT,
                light=Light.GREY,
                explanation=(
                    f"{review.source.publisher} verificó una afirmación relacionada "
                    f"(«{review.matched_claim}» → «{review.textual_rating}»), pero puede tener "
                    "sentido OPUESTO a tu consulta. No emitimos veredicto: leé la fuente y juzgá."
                ),
                sources=sources,
            )

        accion = "desmintió" if original is Verdict.FALSE else "confirmó"
        return VerificationResult(
            verdict=inverted,
            light=_VERDICT_TO_LIGHT[inverted],
            explanation=(
                f"{review.source.publisher} {accion} la afirmación contraria "
                f"(«{review.matched_claim}» → «{review.textual_rating}»), lo que "
                f"{'respalda' if inverted is Verdict.TRUE else 'contradice'} tu consulta."
            ),
            sources=sources,
        )

    @staticmethod
    def _abstain() -> VerificationResult:
        return VerificationResult(
            verdict=Verdict.INSUFFICIENT,
            light=Light.GREY,
            explanation=(
                "No se encontraron verificaciones previas para esta afirmación. "
                "Sin evidencia validada no se emite veredicto."
            ),
            sources=(),
        )

    @staticmethod
    def _explain(review: RawReview) -> str:
        src = review.source
        fecha = f" (revisado {src.reviewed_at})" if src.reviewed_at else ""
        # Mostramos la afirmación EXACTA que se verificó (transparencia): así, si difiere
        # de la consulta, la persona lo ve.
        verificada = f" «{review.matched_claim}»" if review.matched_claim else " esta afirmación"
        return f"{src.publisher} verificó{verificada} y la calificó «{review.textual_rating}»{fecha}."


__all__ = ["ArchiveVerifier", "ClaimReviewProvider", "RawReview"]
