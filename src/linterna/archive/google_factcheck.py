"""Adaptador a Google Fact Check Tools API (claims:search).

Implementación concreta de ``ClaimReviewProvider`` para M1. Consulta verificaciones
humanas previas publicadas como ClaimReview e indexadas por Google.

Sin dependencias externas: usa ``urllib`` de la stdlib (principio de simplicidad). El
transporte HTTP se inyecta para poder testear el parseo sin red ni API key real.

Docs de la API: https://developers.google.com/fact-check/tools/api
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Protocol

from linterna.types import Source

from . import RawReview

_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


class Transport(Protocol):
    """Capa HTTP inyectable. Recibe una URL y devuelve el JSON ya parseado."""

    def __call__(self, url: str, *, timeout_s: float) -> dict[str, Any]: ...


def _urllib_transport(url: str, *, timeout_s: float) -> dict[str, Any]:
    """Transporte por defecto: GET con urllib y parseo de JSON."""
    with urllib.request.urlopen(url, timeout=timeout_s) as response:  # noqa: S310 (URL fija)
        data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        return data


class GoogleFactCheckProvider:
    """Proveedor de ClaimReview respaldado por Google Fact Check Tools API."""

    def __init__(
        self,
        *,
        api_key: str,
        language_code: str = "es",
        timeout_s: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Se requiere una API key de Google Fact Check Tools.")
        self._api_key = api_key
        self._language_code = language_code
        self._timeout_s = timeout_s
        self._transport = transport or _urllib_transport

    def search(self, claim: str) -> list[RawReview]:
        url = self._build_url(claim)
        payload = self._transport(url, timeout_s=self._timeout_s)
        return self._parse(payload)

    def _build_url(self, claim: str) -> str:
        params = urllib.parse.urlencode(
            {
                "query": claim,
                "languageCode": self._language_code,
                "key": self._api_key,
            }
        )
        return f"{_ENDPOINT}?{params}"

    @staticmethod
    def _parse(payload: dict[str, Any]) -> list[RawReview]:
        reviews: list[RawReview] = []
        for claim in payload.get("claims", []):
            matched_claim = claim.get("text", "")
            for review in claim.get("claimReview", []):
                rating = review.get("textualRating")
                url = review.get("url")
                if not rating or not url:
                    continue  # sin calificación o sin enlace no es una cita validable
                publisher = review.get("publisher", {})
                reviews.append(
                    RawReview(
                        matched_claim=matched_claim,
                        textual_rating=rating,
                        source=Source(
                            url=url,
                            title=review.get("title", ""),
                            publisher=publisher.get("name", ""),
                            reviewed_at=review.get("reviewDate"),
                        ),
                    )
                )
        return reviews


__all__ = ["GoogleFactCheckProvider", "Transport"]
