"""Pipeline integrado de Linterna: archivo-primero (M1) y agente investigador (M3).

Orden sagrado (hoja de ruta + invariante 4): primero se consulta el archivo de
verificaciones humanas. Solo si el archivo se abstiene (`INSUFICIENTE`) se delega al
agente, que recupera evidencia fresca y razona con validación estricta de citas.

COMPLIANCE (términos de Brave Search): la evidencia del agente NUNCA se persiste a disco.
La caché persistente (`JsonFileCache`) es solo para el camino de archivo (ClaimReview,
datos públicos). El camino del agente puede usar, como decisión deliberada de gris
permitible, un caché EFÍMERO en memoria con TTL corto (`EphemeralCachingRetriever`) para
deduplicar búsquedas en una ventana breve — nunca un corpus persistente. El test
`test_agent_result_is_not_cached` blinda que la caché de disco no contenga datos de Brave.
"""

from __future__ import annotations

from typing import Protocol

from linterna.types import Verdict, VerificationResult


class _Verifier(Protocol):
    def verify(self, claim: str) -> VerificationResult: ...


class _Investigator(Protocol):
    def investigate(self, claim: str) -> VerificationResult: ...


class LinternaPipeline:
    """Encadena archivo-primero y agente investigador con abstención como default."""

    def __init__(self, *, archive: _Verifier, investigator: _Investigator) -> None:
        self._archive = archive
        self._investigator = investigator

    def verify(self, claim: str) -> VerificationResult:
        archived = self._archive.verify(claim)
        if archived.verdict is not Verdict.INSUFFICIENT:
            return archived  # ya lo verificó un humano: no se molesta al agente
        return self._investigator.investigate(claim)
