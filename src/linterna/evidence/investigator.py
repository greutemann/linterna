"""Agente investigador (M3): aporta evidencia de fuentes confiables, sin sentenciar.

Tras el incidente de afirmaciones dañinas estampadas como "verdadero", el agente NO emite
veredictos de verdad. Su trabajo es:
  1. recuperar evidencia y descartar fuentes marginales/desinformantes (reliability),
  2. dejar que el modelo razone SOLO sobre la evidencia confiable (invariante 2),
     con temperatura 0 para fidelidad,
  3. resumir qué dicen las fuentes y con qué fuerza (lean + % de apoyo), sin tomar partido,
  4. validar que cada cita sea real y recuperada (invariante 3),
  5. abstenerse si no hay evidencia confiable (invariante 4).

Un "respaldado/contradicho" fuerte exige al menos una fuente de alta confiabilidad; si solo
hay fuentes desconocidas, se degrada a "dividida". Así no se presenta un blog marginal como
si fuera evidencia sólida.
"""

from __future__ import annotations

import json
import re
from typing import Any

from linterna.evidence import Evidence, EvidenceRetriever
from linterna.evidence.reliability import Tier, tier_of
from linterna.router import LLMClient, Message
from linterna.types import Source, VerificationResult, Verdict, light_for
from linterna.validation import FabricatedCitation, assert_all_recovered

_STANCE_TO_VERDICT: dict[str, Verdict] = {
    "supports": Verdict.EVIDENCE_SUPPORTS,
    "refutes": Verdict.EVIDENCE_REFUTES,
    "mixed": Verdict.EVIDENCE_MIXED,
}

_STRONG = {Verdict.EVIDENCE_SUPPORTS, Verdict.EVIDENCE_REFUTES}

_SYSTEM_PROMPT = (
    "Sos un asistente de investigación. NO sos un oráculo: no declares si una afirmación es "
    "verdadera o falsa. Razoná ÚNICAMENTE sobre la evidencia provista (no uses conocimiento "
    "propio ni inventes datos) y resumí qué dicen las fuentes, ponderando su confiabilidad: "
    "las de confiabilidad 'alta' pesan; las 'desconocida' son contexto, no prueba.\n"
    "Reglas para no confirmar de más:\n"
    "- Distinguí entre que EXISTA un dato o correlación y que la afirmación, TAL COMO está "
    "formulada, sea correcta. Si las fuentes confiables aportan contexto, causas o matices "
    "que la afirmación omite o tergiversa (por ejemplo, atribuir a causas innatas o genéticas "
    "algo que las fuentes explican por factores ambientales, sociales o metodológicos), eso "
    "NO es 'supports': es 'refutes' o 'mixed'.\n"
    "- Para afirmaciones sobre características inherentes de grupos (raza, etnia, género, "
    "religión, nacionalidad u origen), las fuentes serias suelen rechazar la interpretación "
    "esencialista aunque mencionen diferencias observadas; en esos casos no la respaldes.\n"
    "- Si la evidencia confiable es escasa, contradictoria o no aborda la afirmación, usá "
    "'insufficient' o 'mixed'.\n"
    "- La explicación debe incluir el contexto o matiz clave, no un dato aislado.\n"
    'Respondé SOLO con un JSON: {"stance": "supports|refutes|mixed|insufficient", '
    '"support_pct": <0-100, % de la evidencia confiable que respalda la afirmación tal como '
    'está formulada>, "explanation": "<resumen breve y fiel, con el matiz clave>", '
    '"cited_source_ids": ["<id>", ...]}. Citá solo ids de la evidencia provista.'
)


class InvestigatorAgent:
    """Recupera evidencia confiable y describe su lean, sin emitir veredictos de verdad."""

    def __init__(
        self,
        *,
        retriever: EvidenceRetriever,
        llm: LLMClient,
        max_tokens: int = 3072,
        synthesize: bool = False,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._max_tokens = max_tokens
        # synthesize=False (default SEGURO): no se pide veredicto/lean al modelo; se ofrecen
        # fuentes confiables como puntos de partida. La síntesis (lean + %) sobre evidencia
        # web puede confirmar de más afirmaciones cargadas (p. ej. presentar como "respaldado"
        # una brecha que las fuentes atribuyen a factores ambientales). Hasta resolver eso de
        # forma robusta, queda detrás de este flag. Ver docs/milestone-3-agent.md.
        self._synthesize = synthesize

    def investigate(self, claim: str) -> VerificationResult:
        # Descarta fuentes marginales/desinformantes antes de razonar.
        evidence = [e for e in self._retriever.retrieve(claim) if tier_of(e.url) is not Tier.DENY]
        if not evidence:
            return _abstain("No se recuperó evidencia de fuentes confiables.")

        if not self._synthesize:
            return _leads(evidence)

        messages = self._build_messages(claim, evidence)
        result = self._llm.complete(
            "synthesis", messages, max_tokens=self._max_tokens, json_mode=True, temperature=0.0
        )

        parsed = _parse_response(result.text)
        if parsed is None:
            return _abstain("La respuesta del modelo no se pudo interpretar.")

        stance = str(parsed.get("stance", "")).strip().lower()
        if stance == "insufficient" or stance not in _STANCE_TO_VERDICT:
            return _abstain("La evidencia confiable no alcanza para un resumen claro.")

        cited_ids = parsed.get("cited_source_ids") or []
        sources = self._resolve_citations(cited_ids, evidence)
        if sources is None or not sources:
            return _abstain("Las citas no se validaron contra la evidencia recuperada.")

        verdict = _STANCE_TO_VERDICT[stance]
        # Un lean fuerte exige al menos una fuente de alta confiabilidad.
        if verdict in _STRONG and not any(tier_of(s.url) is Tier.HIGH for s in sources):
            verdict = Verdict.EVIDENCE_MIXED

        support_pct = _clamp_pct(parsed.get("support_pct"))
        return VerificationResult(
            verdict=verdict,
            light=light_for(verdict),
            explanation=str(parsed.get("explanation", "")).strip(),
            sources=sources,
            kind="evidencia",
            support_pct=support_pct,
        )

    def _build_messages(self, claim: str, evidence: list[Evidence]) -> list[Message]:
        bloques = "\n\n".join(
            f"[{e.id}] (confiabilidad: {tier_of(e.url).value}) {e.publisher} — {e.title}\n"
            f"{e.snippet}\n({e.url})"
            for e in evidence
        )
        user = f"Afirmación a investigar:\n{claim}\n\nEvidencia recuperada:\n{bloques}"
        return [Message(role="system", content=_SYSTEM_PROMPT), Message(role="user", content=user)]

    @staticmethod
    def _resolve_citations(
        cited_ids: list[Any], evidence: list[Evidence]
    ) -> tuple[Source, ...] | None:
        by_id = {e.id: e for e in evidence}
        retrieved = tuple(e.as_source() for e in evidence)
        try:
            cited = tuple(by_id[str(cid)].as_source() for cid in cited_ids)
        except KeyError:
            return None  # citó un id no recuperado -> cita inventada
        try:
            return assert_all_recovered(cited, retrieved)
        except FabricatedCitation:
            return None


def _clamp_pct(value: Any) -> int | None:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return None


def _parse_response(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _leads(evidence: list[Evidence]) -> VerificationResult:
    """Modo seguro: sin veredicto ni síntesis del modelo. Ofrece fuentes confiables como
    puntos de partida. Si hay fuentes de alta confiabilidad, muestra SOLO esas (mejor que
    mezclar con foros/desconocidas); si no, ofrece hasta 3 desconocidas como punto de inicio."""
    high = [e for e in evidence if tier_of(e.url) is Tier.HIGH]
    chosen = high[:5] if high else evidence[:3]
    sources = tuple(e.as_source() for e in chosen)
    return VerificationResult(
        verdict=Verdict.INSUFFICIENT,
        light=light_for(Verdict.INSUFFICIENT),
        explanation=(
            "No encontramos una verificación humana de esta afirmación. No emitimos una "
            "conclusión propia: estas fuentes pueden ayudarte a investigarla con tu criterio."
        ),
        sources=sources,
        kind="evidencia",
    )


def _abstain(reason: str) -> VerificationResult:
    return VerificationResult(
        verdict=Verdict.INSUFFICIENT,
        light=light_for(Verdict.INSUFFICIENT),
        explanation=f"{reason} Sin evidencia confiable validada no se emite resumen.",
        sources=(),
        kind="evidencia",
    )
