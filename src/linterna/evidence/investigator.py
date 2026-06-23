"""Agente investigador (M3): RAG sobre evidencia fresca con validación estricta.

Orquesta: recuperar evidencia → pedirle al LLM que razone SOLO sobre ella → parsear su
salida estructurada → validar que cada cita apunte a evidencia recuperada → emitir
veredicto o abstenerse. El modelo nunca aporta hechos propios (invariante 2); el código
—no el modelo— decide si las citas son legítimas (invariante 3).
"""

from __future__ import annotations

import json
import re
from typing import Any

from linterna.evidence import Evidence, EvidenceRetriever
from linterna.router import LLMClient, Message
from linterna.types import Source, VerificationResult, Verdict, light_for
from linterna.validation import FabricatedCitation, assert_all_recovered

# Etiquetas de veredicto que el agente acepta del modelo. Cualquier otra → abstención.
_VERDICT_LABELS: dict[str, Verdict] = {
    "verdadero": Verdict.TRUE,
    "falso": Verdict.FALSE,
    "enganoso": Verdict.MISLEADING,
    "engañoso": Verdict.MISLEADING,
    "disputado": Verdict.DISPUTED,
}

_SYSTEM_PROMPT = (
    "Sos un asistente de verificación. Razoná ÚNICAMENTE sobre la evidencia provista "
    "abajo; no uses conocimiento propio ni inventes datos. Si la evidencia no alcanza, "
    "decílo. Respondé SOLO con un JSON: "
    '{"verdict": "verdadero|falso|enganoso|disputado", "explanation": "...", '
    '"cited_source_ids": ["id", ...]}. Citá solo ids de la evidencia provista.'
)


class InvestigatorAgent:
    """Recupera evidencia y razona sobre ella con validación estricta de citas."""

    def __init__(self, *, retriever: EvidenceRetriever, llm: LLMClient, max_tokens: int = 800) -> None:
        self._retriever = retriever
        self._llm = llm
        self._max_tokens = max_tokens

    def investigate(self, claim: str) -> VerificationResult:
        evidence = self._retriever.retrieve(claim)
        if not evidence:
            return _abstain("No se recuperó evidencia para esta afirmación.")

        messages = self._build_messages(claim, evidence)
        # json_mode: pedimos salida estructurada para que la respuesta sea parseable de
        # forma confiable. La validación de citas (invariante 3) sigue determinística.
        result = self._llm.complete(
            "synthesis", messages, max_tokens=self._max_tokens, json_mode=True
        )

        parsed = _parse_response(result.text)
        if parsed is None:
            return _abstain("La respuesta del modelo no se pudo interpretar.")

        verdict = _VERDICT_LABELS.get(_normalize(parsed.get("verdict", "")))
        if verdict is None:
            return _abstain("El modelo no entregó un veredicto reconocible.")

        cited_ids = parsed.get("cited_source_ids") or []
        sources = self._resolve_citations(cited_ids, evidence)
        if sources is None or not sources:
            # Cita inventada o ausencia de citas: sin evidencia validada, no hay veredicto.
            return _abstain("Las citas del modelo no se validaron contra la evidencia.")

        return VerificationResult(
            verdict=verdict,
            light=light_for(verdict),
            explanation=str(parsed.get("explanation", "")).strip(),
            sources=sources,
        )

    def _build_messages(self, claim: str, evidence: list[Evidence]) -> list[Message]:
        bloques = "\n\n".join(
            f"[{e.id}] {e.publisher} — {e.title}\n{e.snippet}\n({e.url})" for e in evidence
        )
        user = f"Afirmación a verificar:\n{claim}\n\nEvidencia recuperada:\n{bloques}"
        return [Message(role="system", content=_SYSTEM_PROMPT), Message(role="user", content=user)]

    @staticmethod
    def _resolve_citations(
        cited_ids: list[Any], evidence: list[Evidence]
    ) -> tuple[Source, ...] | None:
        by_id = {e.id: e for e in evidence}
        retrieved = tuple(e.as_source() for e in evidence)
        try:
            # Un id no recuperado lanza KeyError -> lo tratamos como cita inventada.
            cited = tuple(by_id[str(cid)].as_source() for cid in cited_ids)
        except KeyError:
            return None
        try:
            return assert_all_recovered(cited, retrieved)
        except FabricatedCitation:
            return None


def _normalize(text: str) -> str:
    return text.strip().lower()


def _parse_response(text: str) -> dict[str, Any] | None:
    """Extrae el objeto JSON de la salida del modelo (tolera ```fences``` y texto extra)."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _abstain(reason: str) -> VerificationResult:
    return VerificationResult(
        verdict=Verdict.INSUFFICIENT,
        light=light_for(Verdict.INSUFFICIENT),
        explanation=f"{reason} Sin evidencia validada no se emite veredicto.",
        sources=(),
    )
