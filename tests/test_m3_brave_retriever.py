"""Adaptador de evidencia Brave Search + tope duro propio. Tests primero, sin red.

El transporte HTTP se inyecta (JSON canónico con la forma real de Brave). El SearchBudget
es nuestra defensa: Brave no tiene corte de gasto, así que lo ponemos en código.
"""

from __future__ import annotations

from typing import Any

import pytest

from linterna.evidence import Evidence
from linterna.evidence.brave import BraveRetriever, BraveSearchError
from linterna.evidence.budget import SearchBudget, SearchBudgetExceeded

# Forma real (recortada) de la respuesta de Brave web/search.
_BRAVE_RESPONSE = {
    "web": {
        "results": [
            {
                "title": "Brote de dengue 2026",
                "url": "https://oms.org/dengue",
                "description": "Los casos de dengue aumentaron un 30% este año.",
                "profile": {"name": "OMS"},
                "age": "2026-03-01",
            },
            {
                "title": "Parte epidemiológico",
                "url": "https://salud.gob/dengue",
                "description": "Focos confirmados en tres provincias.",
                "meta_url": {"hostname": "salud.gob"},
            },
        ]
    }
}


class FakeTransport:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.last_url: str | None = None
        self.last_headers: dict[str, str] | None = None
        self.calls = 0

    def __call__(self, url: str, *, headers: dict[str, str], timeout_s: float) -> dict[str, Any]:
        self.calls += 1
        self.last_url = url
        self.last_headers = headers
        return self.payload


def test_parses_results_into_evidence() -> None:
    transport = FakeTransport(_BRAVE_RESPONSE)
    retriever = BraveRetriever(api_key="k", transport=transport)

    evidence = retriever.retrieve("dengue 2026")

    assert len(evidence) == 2
    assert all(isinstance(e, Evidence) for e in evidence)
    assert evidence[0].publisher == "OMS"
    assert evidence[0].url == "https://oms.org/dengue"
    assert "30%" in evidence[0].snippet
    assert evidence[0].published_at == "2026-03-01"
    # ids estables y únicos para que el modelo los cite.
    assert len({e.id for e in evidence}) == 2


def test_publisher_falls_back_to_hostname() -> None:
    retriever = BraveRetriever(api_key="k", transport=FakeTransport(_BRAVE_RESPONSE))
    evidence = retriever.retrieve("x")
    assert evidence[1].publisher == "salud.gob"  # sin profile.name -> hostname


def test_api_key_goes_in_header_not_url() -> None:
    transport = FakeTransport(_BRAVE_RESPONSE)
    retriever = BraveRetriever(api_key="secret-token", transport=transport)

    retriever.retrieve("una consulta")

    assert transport.last_headers is not None
    assert transport.last_headers.get("X-Subscription-Token") == "secret-token"
    assert "secret-token" not in (transport.last_url or "")  # nunca en la URL
    assert "q=una+consulta" in (transport.last_url or "") or "q=una%20consulta" in (transport.last_url or "")


def test_empty_results() -> None:
    retriever = BraveRetriever(api_key="k", transport=FakeTransport({"web": {"results": []}}))
    assert retriever.retrieve("nada") == []


def test_transport_error_raises_brave_error() -> None:
    class Boom:
        def __call__(self, url: str, *, headers: dict[str, str], timeout_s: float) -> Any:
            raise RuntimeError("red caída")

    retriever = BraveRetriever(api_key="k", transport=Boom())
    with pytest.raises(BraveSearchError):
        retriever.retrieve("x")


def test_max_results_is_respected() -> None:
    transport = FakeTransport(_BRAVE_RESPONSE)
    retriever = BraveRetriever(api_key="k", transport=transport, max_results=1)
    assert len(retriever.retrieve("x")) == 1
    assert "count=1" in (transport.last_url or "")


# --- tope duro propio ----------------------------------------------------------

def test_search_budget_hard_cap_blocks_call() -> None:
    transport = FakeTransport(_BRAVE_RESPONSE)
    budget = SearchBudget(max_searches=2)
    retriever = BraveRetriever(api_key="k", transport=transport, budget=budget)

    retriever.retrieve("a")
    retriever.retrieve("b")
    with pytest.raises(SearchBudgetExceeded):
        retriever.retrieve("c")  # tercera supera el tope

    assert transport.calls == 2  # la tercera NO llegó a llamar a Brave


def test_search_budget_resets_per_period() -> None:
    # period_of() lo consumen: constructor, ensure, charge, ensure (último ya es otro período).
    periods = iter(["2026-06", "2026-06", "2026-06", "2026-07"])
    budget = SearchBudget(max_searches=1, period_of=lambda: next(periods))

    budget.ensure_within_cap()
    budget.charge()
    # mismo período -> cortaría; pero avanza al siguiente -> resetea.
    budget.ensure_within_cap()  # no lanza: nuevo período
