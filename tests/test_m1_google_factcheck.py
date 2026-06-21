"""Adaptador a Google Fact Check Tools API. Tests primero, sin red.

El transporte HTTP se inyecta: los tests le pasan un JSON canónico (con la forma real
de la respuesta de la API) y verifican el parseo a RawReview. Ninguna prueba sale a
internet ni necesita API key real.
"""

from __future__ import annotations

from typing import Any

import pytest

from linterna.archive import ArchiveVerifier, RawReview
from linterna.archive.cache import InMemoryCache
from linterna.archive.google_factcheck import GoogleFactCheckProvider
from linterna.types import Verdict


# Forma real (recortada) de la respuesta de claims:search.
_API_RESPONSE = {
    "claims": [
        {
            "text": "La vacuna contiene microchips",
            "claimant": "Cadena de WhatsApp",
            "claimReview": [
                {
                    "publisher": {"name": "Chequeado", "site": "chequeado.com"},
                    "url": "https://chequeado.com/falso-microchips",
                    "title": "No, la vacuna no contiene microchips",
                    "reviewDate": "2024-03-01T00:00:00Z",
                    "textualRating": "Falso",
                    "languageCode": "es",
                }
            ],
        }
    ]
}


class FakeTransport:
    """Transporte HTTP controlable: registra la URL pedida y devuelve JSON canónico."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.last_url: str | None = None

    def __call__(self, url: str, *, timeout_s: float) -> dict[str, Any]:
        self.last_url = url
        return self.payload


def test_parses_claimreview_into_rawreview() -> None:
    transport = FakeTransport(_API_RESPONSE)
    provider = GoogleFactCheckProvider(api_key="k", transport=transport)

    reviews = provider.search("La vacuna contiene microchips")

    assert len(reviews) == 1
    review = reviews[0]
    assert isinstance(review, RawReview)
    assert review.textual_rating == "Falso"
    assert review.source.publisher == "Chequeado"
    assert review.source.url == "https://chequeado.com/falso-microchips"
    assert review.source.reviewed_at == "2024-03-01T00:00:00Z"


def test_request_includes_key_query_and_language() -> None:
    transport = FakeTransport(_API_RESPONSE)
    provider = GoogleFactCheckProvider(api_key="secret-key", language_code="es", transport=transport)

    provider.search("dólar a $2000")

    assert transport.last_url is not None
    assert "key=secret-key" in transport.last_url
    assert "languageCode=es" in transport.last_url
    assert "query=d%C3%B3lar" in transport.last_url  # URL-encoded


def test_no_claims_yields_empty_list() -> None:
    provider = GoogleFactCheckProvider(api_key="k", transport=FakeTransport({}))
    assert provider.search("algo nunca verificado") == []


def test_claim_without_review_is_skipped() -> None:
    payload = {"claims": [{"text": "x", "claimReview": []}]}
    provider = GoogleFactCheckProvider(api_key="k", transport=FakeTransport(payload))
    assert provider.search("x") == []


def test_missing_optional_fields_do_not_crash() -> None:
    payload = {
        "claims": [
            {
                "text": "y",
                "claimReview": [
                    {"publisher": {"name": "X"}, "url": "https://x.test", "textualRating": "Verdadero"}
                ],
            }
        ]
    }
    provider = GoogleFactCheckProvider(api_key="k", transport=FakeTransport(payload))
    (review,) = provider.search("y")
    assert review.source.title == ""
    assert review.source.reviewed_at is None


def test_empty_api_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        GoogleFactCheckProvider(api_key="", transport=FakeTransport({}))


def test_integrates_with_archive_verifier() -> None:
    # El adaptador real encaja en el pipeline sin tocar ArchiveVerifier.
    provider = GoogleFactCheckProvider(api_key="k", transport=FakeTransport(_API_RESPONSE))
    verifier = ArchiveVerifier(provider=provider, cache=InMemoryCache())

    result = verifier.verify("La vacuna contiene microchips")

    assert result.verdict is Verdict.FALSE
    assert result.sources[0].publisher == "Chequeado"
