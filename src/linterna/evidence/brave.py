"""Adaptador de evidencia sobre Brave Search API (índice web independiente).

Implementa ``EvidenceRetriever`` para M3. Se eligió Brave por su índice propio y
auditable (no un reempaquetador de terceros), alineado con el invariante 7. Como Brave
no tiene corte de gasto, se envuelve en un ``SearchBudget`` con tope duro en código.

Sin dependencias externas: ``urllib`` de la stdlib. El transporte se inyecta para testear
el parseo sin red ni API key real.

Docs: https://api-dashboard.search.brave.com/app/documentation/web-search/get-started
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Protocol

from . import Evidence
from .budget import SearchBudget

_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchError(Exception):
    """La búsqueda en Brave falló (red/HTTP)."""


class Transport(Protocol):
    """Capa HTTP inyectable. La key viaja en headers, nunca en la URL."""

    def __call__(self, url: str, *, headers: dict[str, str], timeout_s: float) -> dict[str, Any]: ...


def _urllib_transport(url: str, *, headers: dict[str, str], timeout_s: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 (URL fija)
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        return data


class BraveRetriever:
    """Recupera evidencia fresca desde el índice independiente de Brave."""

    def __init__(
        self,
        *,
        api_key: str,
        max_results: int = 5,
        timeout_s: float = 10.0,
        transport: Transport | None = None,
        budget: SearchBudget | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Se requiere una API key de Brave Search.")
        self._api_key = api_key
        self._max_results = max_results
        self._timeout_s = timeout_s
        self._transport = transport or _urllib_transport
        self._budget = budget

    def retrieve(self, claim: str) -> list[Evidence]:
        if self._budget is not None:
            self._budget.ensure_within_cap()  # corte duro ANTES de gastar

        url = self._build_url(claim)
        headers = {"X-Subscription-Token": self._api_key, "Accept": "application/json"}
        try:
            payload = self._transport(url, headers=headers, timeout_s=self._timeout_s)
        except Exception as exc:  # noqa: BLE001 (cualquier fallo de red/HTTP)
            raise BraveSearchError(f"Brave Search no respondió: {exc}") from exc

        if self._budget is not None:
            self._budget.charge()
        return self._parse(payload)

    def _build_url(self, claim: str) -> str:
        params = urllib.parse.urlencode({"q": claim, "count": self._max_results})
        return f"{_ENDPOINT}?{params}"

    def _parse(self, payload: dict[str, Any]) -> list[Evidence]:
        results = payload.get("web", {}).get("results", [])[: self._max_results]
        evidence: list[Evidence] = []
        for i, r in enumerate(results, start=1):
            url = r.get("url")
            if not url:
                continue
            evidence.append(
                Evidence(
                    id=f"b{i}",
                    url=url,
                    title=r.get("title", ""),
                    publisher=_publisher_of(r),
                    snippet=r.get("description", ""),
                    published_at=r.get("age"),
                )
            )
        return evidence


def _publisher_of(result: dict[str, Any]) -> str:
    profile = result.get("profile") or {}
    if profile.get("name"):
        return str(profile["name"])
    meta = result.get("meta_url") or {}
    return str(meta.get("hostname", ""))


__all__ = ["BraveRetriever", "BraveSearchError"]
