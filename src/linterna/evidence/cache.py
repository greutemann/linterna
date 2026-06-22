"""Caché efímero del retriever de evidencia (solo en memoria, TTL corto).

Decisión consciente de "gris permitible" frente a los términos de Brave: un caché
chico, en RAM y de vida corta es deduplicación de búsquedas en una ventana breve, no
almacenamiento persistente ni un corpus reutilizable. NUNCA toca disco; el reinicio del
proceso lo vacía. Probablemente fuera del espíritu de la restricción de Brave (proteger
su índice / evitar reventa), pero conviene mantener TTL y tamaño chicos.

Para el archivo (ClaimReview público) se usa la caché persistente en disco; esto es solo
para el camino del agente (evidencia de Brave).
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable

from . import Evidence, EvidenceRetriever


class EphemeralCachingRetriever:
    """Envuelve un `EvidenceRetriever` con un caché en memoria, con TTL y cota LRU."""

    def __init__(
        self,
        inner: EvidenceRetriever,
        *,
        ttl_s: float = 600.0,
        max_entries: int = 256,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._inner = inner
        self._ttl_s = ttl_s
        self._max_entries = max_entries
        self._clock = clock
        self._store: OrderedDict[str, tuple[float, list[Evidence]]] = OrderedDict()

    def retrieve(self, claim: str) -> list[Evidence]:
        key = claim.strip().lower()
        now = self._clock()

        cached = self._store.get(key)
        if cached is not None and now - cached[0] < self._ttl_s:
            self._store.move_to_end(key)  # marca como recién usado (LRU)
            return cached[1]

        evidence = self._inner.retrieve(claim)
        self._store[key] = (now, evidence)
        self._store.move_to_end(key)
        self._evict()
        return evidence

    def _evict(self) -> None:
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)  # descarta el menos usado


__all__ = ["EphemeralCachingRetriever"]
