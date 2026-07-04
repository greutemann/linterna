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


def test_opposite_polarity_inverts_the_verdict() -> None:
    # El caso real: verificaron "el viaje a la Luna fue un montaje" → Falso. La consulta es
    # la afirmación OPUESTA (verdadera). Desmentir lo contrario ES confirmar la consulta:
    # veredicto invertido determinísticamente → Verdadero (verde), citando la misma fuente.
    claim = "El hombre llegó a la Luna en 1969"
    review = RawReview(
        "El viaje del hombre a la Luna en 1969 fue un montaje",
        "Falso",
        Source(url="https://maldita.es/x", title="Montaje lunar", publisher="Maldita.es"),
    )
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    result = verifier.verify(claim)

    assert result.verdict is Verdict.TRUE  # 🟢 (jamás el Falso invertido)
    assert result.light is Light.GREEN
    assert len(result.sources) == 1
    # Transparencia: la explicación muestra la afirmación contraria verificada y su rating.
    assert "contraria" in result.explanation.lower()
    assert "montaje" in result.explanation.lower()


def test_negation_polarity_inverts_too() -> None:
    # "las vacunas NO causan autismo" vs verificación de "las vacunas causan autismo" (Falso)
    # -> la consulta (negada) queda confirmada: Verdadero.
    claim = "Las vacunas no causan autismo"
    review = RawReview("Las vacunas causan autismo", "Falso", _SOURCE)
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    assert verifier.verify(claim).verdict is Verdict.TRUE


def test_same_negative_polarity_applies_verdict_directly() -> None:
    # Caso real de producción: la consulta YA es la versión negada ("nunca llegó") y la
    # verificación compuesta también niega («fue falso y nunca llegó» → Falso). MISMA
    # polaridad (ambas negativas, aunque usen marcadores distintos) -> el Falso se aplica
    # directo, NO se invierte.
    claim = "El hombre nunca llegó a la Luna"
    review = RawReview(
        "Stanley Kubrick confiesa que el alunizaje fue falso y el hombre nunca llegó a la Luna",
        "Falso",
        Source(url="https://maldita.es/k", title="Kubrick alunizaje", publisher="Maldita.es"),
    )
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    result = verifier.verify(claim)
    assert result.verdict is Verdict.FALSE  # nunca "Verdadero" por doble inversión
    assert result.light is Light.RED


def test_opposite_polarity_true_inverts_to_false() -> None:
    # Confirmaron la afirmación contraria -> la consulta es falsa.
    claim = "El hombre nunca llegó a la Luna"
    review = RawReview("El hombre llegó a la Luna", "Verdadero", _SOURCE)
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    result = verifier.verify(claim)
    assert result.verdict is Verdict.FALSE
    assert result.light is Light.RED


def test_opposite_polarity_with_nuanced_rating_stays_related() -> None:
    # Engañoso/Disputado no se invierten (el matiz no sobrevive una negación) -> gris.
    claim = "El hombre llegó a la Luna en 1969"
    review = RawReview(
        "El viaje del hombre a la Luna en 1969 fue un montaje", "Engañoso", _SOURCE
    )
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    result = verifier.verify(claim)
    assert result.verdict is Verdict.INSUFFICIENT
    assert result.light is Light.GREY
    assert len(result.sources) == 1  # igual muestra la verificación relacionada


def test_same_polarity_still_applies_verdict() -> None:
    # Sin marcadores de polaridad, el veredicto se aplica normal.
    claim = "La Tierra es plana"
    review = RawReview("La Tierra es plana", "Falso", _SOURCE)
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    assert verifier.verify(claim).verdict is Verdict.FALSE


def test_explanation_shows_verified_claim() -> None:
    claim = "La vacuna contiene microchips"
    review = RawReview("La vacuna contiene microchips", "Falso", _SOURCE)
    verifier = ArchiveVerifier(provider=FakeProvider({claim: [review]}), cache=InMemoryCache())
    # Transparencia: la explicación muestra la afirmación exacta que se verificó.
    assert "La vacuna contiene microchips" in verifier.verify(claim).explanation


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
