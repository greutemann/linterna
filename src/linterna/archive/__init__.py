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


# Mapeo de calificaciones textuales -> veredicto. Determinístico y auditable.
# Las claves se comparan ya normalizadas (sin acentos, minúsculas).
_RATING_TO_VERDICT: dict[str, Verdict] = {
    "falso": Verdict.FALSE,
    "false": Verdict.FALSE,
    "verdadero": Verdict.TRUE,
    "true": Verdict.TRUE,
    "enganoso": Verdict.MISLEADING,
    "misleading": Verdict.MISLEADING,
    "disputado": Verdict.DISPUTED,
}

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
    # Calificación no reconocida: hay evidencia humana pero no la clasificamos a
    # ciegas. Se muestra como DISPUTADO (amarillo) para que la persona juzgue.
    return _RATING_TO_VERDICT.get(_normalize(textual_rating), Verdict.DISPUTED)


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
        result = self._build_result(reviews)
        self._cache.set(key, result)
        return result

    def _build_result(self, reviews: list[RawReview]) -> VerificationResult:
        if not reviews:
            return self._abstain()

        recovered = tuple(r.source for r in reviews)
        # Validación determinística: toda fuente de salida debe estar recuperada.
        sources = assert_all_recovered(recovered, recovered)

        verdict = _rating_to_verdict(reviews[0].textual_rating)
        return VerificationResult(
            verdict=verdict,
            light=_VERDICT_TO_LIGHT[verdict],
            explanation=self._explain(reviews[0]),
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
        return f"{src.publisher} calificó esta afirmación como «{review.textual_rating}»{fecha}."


__all__ = ["ArchiveVerifier", "ClaimReviewProvider", "RawReview"]
