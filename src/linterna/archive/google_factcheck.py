"""Adaptador a Google Fact Check Tools API (claims:search).

Implementación concreta de ``ClaimReviewProvider`` para M1. Consulta verificaciones
humanas previas publicadas como ClaimReview e indexadas por Google.

Sin dependencias externas: usa ``urllib`` de la stdlib (principio de simplicidad). El
transporte HTTP se inyecta para poder testear el parseo sin red ni API key real.

Docs de la API: https://developers.google.com/fact-check/tools/api
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from linterna.types import Source

from . import RawReview

_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# Códigos HTTP que vale la pena reintentar (transitorios). El resto (4xx) es fatal:
# request mal armada o key inválida — reintentar no ayuda.
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class ArchiveProviderError(Exception):
    """El proveedor de archivo falló (red/HTTP). NO es una abstención: es un fallo de infra."""


class Transport(Protocol):
    """Capa HTTP inyectable. Recibe una URL y devuelve el JSON ya parseado."""

    def __call__(self, url: str, *, timeout_s: float) -> dict[str, Any]: ...


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _RETRYABLE_STATUS
    # URLError sin code = problema de red (DNS, conexión) -> transitorio.
    return isinstance(exc, urllib.error.URLError)


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
        max_retries: int = 2,
        backoff_s: float = 0.5,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise ValueError("Se requiere una API key de Google Fact Check Tools.")
        self._api_key = api_key
        self._language_code = language_code
        self._timeout_s = timeout_s
        self._transport = transport or _urllib_transport
        self._max_retries = max_retries
        self._backoff_s = backoff_s
        self._sleeper = sleeper

    def search(self, claim: str) -> list[RawReview]:
        url = self._build_url(claim)
        payload = self._fetch_with_retries(url)
        return self._parse(payload)

    def _fetch_with_retries(self, url: str) -> dict[str, Any]:
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            try:
                return self._transport(url, timeout_s=self._timeout_s)
            except Exception as exc:  # noqa: BLE001 (clasificamos abajo)
                if not _is_retryable(exc) or attempt == attempts - 1:
                    raise ArchiveProviderError(
                        f"Google Fact Check no respondió tras {attempt + 1} intento(s)."
                    ) from exc
                # Backoff exponencial simple antes de reintentar.
                self._sleeper(self._backoff_s * (2**attempt))
        raise AssertionError("inalcanzable")  # pragma: no cover

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
