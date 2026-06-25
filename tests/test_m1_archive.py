"""M1 — núcleo archivo-primero. Tests escritos ANTES de la implementación.

Cubren los 5 criterios de éxito de docs/milestone-1-archive.md. Sin red ni LLM:
el proveedor de ClaimReview se mockea para que los tests sean deterministas.
"""

from __future__ import annotations

import pytest

from linterna.archive import ArchiveVerifier, RawReview
from linterna.archive.cache import InMemoryCache
from linterna.types import Light, Source, Verdict
from linterna.validation import FabricatedCitation, assert_all_recovered


class FakeProvider:
    """Proveedor de ClaimReview controlable y que cuenta sus llamadas."""

    def __init__(self, results: dict[str, list[RawReview]]) -> None:
        self._results = results
        self.calls = 0

    def search(self, claim: str) -> list[RawReview]:
        self.calls += 1
        return self._results.get(claim, [])


_SOURCE = Source(
    url="https://chequeado.com/x",
    title="No, la vacuna no contiene microchips",
    publisher="Chequeado",
    reviewed_at="2024-03-01",
)


# --- Criterio 1: hit de archivo -------------------------------------------------

def test_archive_hit_returns_verdict_and_sources() -> None:
    claim = "La vacuna contiene microchips"
    provider = FakeProvider({claim: [RawReview(claim, "Falso", _SOURCE)]})
    verifier = ArchiveVerifier(provider=provider, cache=InMemoryCache())

    result = verifier.verify(claim)

    assert result.verdict is Verdict.FALSE
    assert result.light is Light.RED
    assert _SOURCE in result.sources


def test_unrelated_claimreview_does_not_apply_its_verdict() -> None:
    # El archivo devolvió una verificación de OTRA afirmación (proximidad de búsqueda).
    # No debe aplicarse su veredicto -> abstención (cae al agente en el pipeline).
    claim = "La Tierra gira alrededor del Sol"
    otra = RawReview(
        "La Tierra está en su punto más alejado del Sol y por eso hace más frío",
        "Falso",
        Source(url="https://x/y", title="Falso: clima y distancia al Sol", publisher="Univision"),
    )
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [otra]}), cache=InMemoryCache())
    assert verifier.verify(claim).verdict is Verdict.INSUFFICIENT


def test_bulo_rating_maps_to_false() -> None:
    claim = "El agua con limón en ayunas cura el cáncer"
    review = RawReview(claim, "Bulo", _SOURCE)
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    result = verifier.verify(claim)
    assert result.verdict is Verdict.FALSE
    assert result.light is Light.RED


# --- Criterio 2: miss -> abstención --------------------------------------------

def test_archive_miss_abstains() -> None:
    provider = FakeProvider({})  # sin verificaciones previas
    verifier = ArchiveVerifier(provider=provider, cache=InMemoryCache())

    result = verifier.verify("Afirmación nunca antes verificada")

    assert result.verdict is Verdict.INSUFFICIENT
    assert result.light is Light.GREY
    assert result.sources == ()


# --- Criterio 3: cita inventada = rechazada ------------------------------------

def test_fabricated_citation_is_rejected() -> None:
    recovered = (_SOURCE,)
    invented = Source(url="https://no-recuperada.example/falsa", title="x", publisher="y")

    with pytest.raises(FabricatedCitation):
        assert_all_recovered((invented,), recovered)


def test_validator_passes_recovered_sources() -> None:
    assert_all_recovered((_SOURCE,), (_SOURCE,)) == (_SOURCE,)


# --- Criterio 4: caché ----------------------------------------------------------

def test_cache_avoids_second_provider_call() -> None:
    claim = "La tierra es plana"
    provider = FakeProvider({claim: [RawReview(claim, "Falso", _SOURCE)]})
    verifier = ArchiveVerifier(provider=provider, cache=InMemoryCache())

    first = verifier.verify(claim)
    second = verifier.verify(claim)

    assert first == second
    assert provider.calls == 1  # la segunda consulta salió de caché


# --- Criterio 5: sin PII --------------------------------------------------------

def test_cache_persists_only_claim_and_result_no_pii() -> None:
    claim = "El dólar va a $2000"
    cache = InMemoryCache()
    provider = FakeProvider({claim: [RawReview(claim, "Engañoso", _SOURCE)]})
    verifier = ArchiveVerifier(provider=provider, cache=cache)

    verifier.verify(claim)

    # Lo persistido es {clave normalizada de la afirmación -> VerificationResult}.
    # No hay lugar para identidad del usuario en la firma ni en el almacenamiento.
    (stored_key,) = cache.keys()
    assert isinstance(stored_key, str)
    assert "$2000" in stored_key or "2000" in stored_key
