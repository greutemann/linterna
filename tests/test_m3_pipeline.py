"""M3 — pipeline integrado: archivo-primero (M1) y, si se abstiene, el agente (M3).

Criterio 7: un hit de archivo NO invoca al agente; un miss SÍ lo delega.
"""

from __future__ import annotations

from linterna.archive import ArchiveVerifier, RawReview
from linterna.archive.cache import InMemoryCache
from linterna.evidence import Evidence
from linterna.pipeline import LinternaPipeline
from linterna.types import Light, Source, Verdict, VerificationResult


class StubInvestigator:
    """Doble del agente: registra si se lo invocó."""

    def __init__(self, result: VerificationResult) -> None:
        self._result = result
        self.calls = 0

    def investigate(self, claim: str) -> VerificationResult:
        self.calls += 1
        return self._result


_AGENT_RESULT = VerificationResult(
    verdict=Verdict.TRUE,
    light=Light.GREEN,
    explanation="del agente",
    sources=(Evidence("e1", "https://x/y", "t", "OMS", "snip").as_source(),),
)


class ArchiveProvider:
    def __init__(self, reviews: list[RawReview]) -> None:
        self._reviews = reviews

    def search(self, claim: str) -> list[RawReview]:
        return self._reviews


def test_archive_hit_does_not_call_agent() -> None:
    source = Source(url="https://chequeado/x", title="t", publisher="Chequeado", reviewed_at=None)
    verifier = ArchiveVerifier(
        provider=ArchiveProvider([RawReview("c", "Falso", source)]), cache=InMemoryCache()
    )
    agent = StubInvestigator(_AGENT_RESULT)
    pipeline = LinternaPipeline(archive=verifier, investigator=agent)

    result = pipeline.verify("una afirmación ya verificada")

    assert result.verdict is Verdict.FALSE  # vino del archivo
    assert agent.calls == 0  # el agente no se invocó


def test_archive_miss_delegates_to_agent() -> None:
    verifier = ArchiveVerifier(provider=ArchiveProvider([]), cache=InMemoryCache())
    agent = StubInvestigator(_AGENT_RESULT)
    pipeline = LinternaPipeline(archive=verifier, investigator=agent)

    result = pipeline.verify("afirmación sin verificación previa")

    assert result.verdict is Verdict.TRUE  # vino del agente
    assert agent.calls == 1


def test_agent_result_is_not_cached() -> None:
    # COMPLIANCE Brave: la evidencia del agente NO debe persistirse en la caché.
    cache = InMemoryCache()
    verifier = ArchiveVerifier(provider=ArchiveProvider([]), cache=cache)
    agent = StubInvestigator(_AGENT_RESULT)
    pipeline = LinternaPipeline(archive=verifier, investigator=agent)

    pipeline.verify("afirmación nueva que va al agente")

    # La caché puede tener la abstención del archivo, pero NUNCA las fuentes del agente.
    cached_results = [cache.get(k) for k in cache.keys()]
    for result in cached_results:
        assert result is not None
        for source in result.sources:
            assert source.url != "https://x/y"  # url derivada del retriever
        assert result.verdict is Verdict.INSUFFICIENT  # solo la abstención del archivo
