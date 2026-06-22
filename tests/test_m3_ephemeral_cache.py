"""Caché efímero del retriever de evidencia (decisión de gris: solo en memoria, TTL corto).

COMPLIANCE Brave: NO persiste a disco, TTL corto, tamaño acotado. Es deduplicación de
búsquedas en una ventana breve — no un corpus. El reinicio del proceso lo vacía.
"""

from __future__ import annotations

from linterna.evidence import Evidence
from linterna.evidence.cache import EphemeralCachingRetriever


class CountingRetriever:
    def __init__(self) -> None:
        self.calls = 0

    def retrieve(self, claim: str) -> list[Evidence]:
        self.calls += 1
        return [Evidence(id="b1", url=f"https://x/{claim}", title="t", publisher="P", snippet="s")]


def test_hit_within_ttl_does_not_research() -> None:
    inner = CountingRetriever()
    clock = iter([0.0, 1.0, 2.0])  # todos dentro del TTL
    retriever = EphemeralCachingRetriever(inner, ttl_s=600, clock=lambda: next(clock))

    first = retriever.retrieve("dengue")
    second = retriever.retrieve("dengue")

    assert first == second
    assert inner.calls == 1  # la segunda salió del caché en memoria


def test_expiry_triggers_research() -> None:
    inner = CountingRetriever()
    clock = iter([0.0, 700.0])  # la segunda consulta ya pasó el TTL (600)
    retriever = EphemeralCachingRetriever(inner, ttl_s=600, clock=lambda: next(clock))

    retriever.retrieve("dengue")
    retriever.retrieve("dengue")

    assert inner.calls == 2  # caché expirado -> vuelve a buscar


def test_distinct_claims_each_search() -> None:
    inner = CountingRetriever()
    clock = iter([0.0, 1.0])
    retriever = EphemeralCachingRetriever(inner, ttl_s=600, clock=lambda: next(clock))

    retriever.retrieve("a")
    retriever.retrieve("b")

    assert inner.calls == 2


def test_lru_bound_evicts_oldest() -> None:
    inner = CountingRetriever()
    times = iter(float(i) for i in range(100))
    retriever = EphemeralCachingRetriever(
        inner, ttl_s=10_000, max_entries=2, clock=lambda: next(times)
    )

    retriever.retrieve("a")  # store a
    retriever.retrieve("b")  # store b
    retriever.retrieve("c")  # store c -> evicta a (el más viejo)
    retriever.retrieve("a")  # a fue evictado -> re-busca

    assert inner.calls == 4
