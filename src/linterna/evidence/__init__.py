"""M3 — Recuperación de evidencia y agente investigador (RAG sobre evidencia fresca).

Define el contrato `EvidenceRetriever` (inyectable) y el tipo `Evidence`. El adaptador
concreto de búsqueda se enchufa después sin tocar la lógica del agente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from linterna.types import Source


@dataclass(frozen=True)
class Evidence:
    """Una pieza de evidencia recuperada. `id` es estable para que el modelo la cite."""

    id: str
    url: str
    title: str
    publisher: str
    snippet: str
    published_at: str | None = None

    def as_source(self) -> Source:
        """Proyecta la evidencia a una `Source` citable en el resultado final."""
        return Source(
            url=self.url,
            title=self.title,
            publisher=self.publisher,
            reviewed_at=self.published_at,
        )


class EvidenceRetriever(Protocol):
    """Recupera evidencia fresca para una afirmación (buscador, fuentes curadas, etc.)."""

    def retrieve(self, claim: str) -> list[Evidence]: ...


__all__ = ["Evidence", "EvidenceRetriever"]
