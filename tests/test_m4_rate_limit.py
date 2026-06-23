"""Rate limiting por IP en /api/verify. Protege las keys de abuso (gasto de terceros).

Reloj inyectable: la ventana de tiempo se controla, sin sleeps.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
from fastapi.testclient import TestClient

from linterna.types import Light, Source, Verdict, VerificationResult
from linterna.web.app import create_app


class StubPipeline:
    def verify(self, claim: str) -> VerificationResult:
        return VerificationResult(
            verdict=Verdict.FALSE, light=Light.RED, explanation="x",
            sources=(Source(url="https://x/y", title="t", publisher="P"),),
        )


def _client(rate_limit: int, clock: Callable[[], float]) -> TestClient:
    return TestClient(create_app(StubPipeline(), rate_limit=rate_limit, rate_window_s=60.0, clock=clock))


def _post(client: TestClient, ip: str = "1.2.3.4") -> httpx.Response:
    resp: httpx.Response = client.post(
        "/api/verify", json={"claim": "una afirmación"}, headers={"X-Forwarded-For": ip}
    )
    return resp


def test_under_limit_passes() -> None:
    client = _client(rate_limit=3, clock=lambda: 0.0)
    for _ in range(3):
        assert _post(client).status_code == 200


def test_over_limit_returns_429() -> None:
    client = _client(rate_limit=3, clock=lambda: 0.0)
    for _ in range(3):
        _post(client)
    assert _post(client).status_code == 429


def test_distinct_ips_counted_separately() -> None:
    client = _client(rate_limit=1, clock=lambda: 0.0)
    assert _post(client, ip="10.0.0.1").status_code == 200
    assert _post(client, ip="10.0.0.2").status_code == 200  # otra IP, su propio cupo
    assert _post(client, ip="10.0.0.1").status_code == 429   # la primera ya se pasó


def test_window_resets_over_time() -> None:
    now = {"t": 0.0}
    client = _client(rate_limit=1, clock=lambda: now["t"])

    assert _post(client).status_code == 200
    assert _post(client).status_code == 429   # mismo minuto
    now["t"] = 61.0                            # pasó la ventana
    assert _post(client).status_code == 200    # cupo renovado
