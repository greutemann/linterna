"""Resiliencia del provider de Google Fact Check: retry acotado y errores claros.

Un fallo de infraestructura NO debe disfrazarse de abstención (eso ocultaría el error
y violaría el espíritu del invariante 4). El provider reintenta lo transitorio
(429/5xx/red) de forma acotada y, si persiste, lanza ArchiveProviderError.
"""

from __future__ import annotations

import urllib.error
from typing import Any

import pytest

from linterna.archive.google_factcheck import ArchiveProviderError, GoogleFactCheckProvider


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://x", code, "msg", hdrs=None, fp=None)  # type: ignore[arg-type]


class FlakyTransport:
    """Falla las primeras `fail_times` veces con `exc`, luego devuelve `payload`."""

    def __init__(self, exc: Exception, fail_times: int, payload: dict[str, Any] | None = None) -> None:
        self._exc = exc
        self._fail_times = fail_times
        self._payload = payload or {"claims": []}
        self.calls = 0

    def __call__(self, url: str, *, timeout_s: float) -> dict[str, Any]:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._exc
        return self._payload


def _provider(transport: Any, **kw: Any) -> GoogleFactCheckProvider:
    # sleeper no-op para no dormir en tests.
    return GoogleFactCheckProvider(
        api_key="k", transport=transport, max_retries=2, sleeper=lambda _s: None, **kw
    )


def test_retries_transient_then_succeeds() -> None:
    transport = FlakyTransport(_http_error(503), fail_times=2)
    provider = _provider(transport)

    result = provider.search("algo")

    assert result == []
    assert transport.calls == 3  # 2 fallos + 1 éxito


def test_rate_limit_429_is_retried() -> None:
    transport = FlakyTransport(_http_error(429), fail_times=1)
    provider = _provider(transport)

    provider.search("algo")
    assert transport.calls == 2


def test_transient_failure_exhausts_and_raises() -> None:
    transport = FlakyTransport(_http_error(500), fail_times=99)
    provider = _provider(transport)

    with pytest.raises(ArchiveProviderError):
        provider.search("algo")
    assert transport.calls == 3  # 1 intento + 2 reintentos, ni uno más


def test_network_error_is_retried_then_raises() -> None:
    transport = FlakyTransport(urllib.error.URLError("sin red"), fail_times=99)
    provider = _provider(transport)

    with pytest.raises(ArchiveProviderError):
        provider.search("algo")
    assert transport.calls == 3


def test_client_error_4xx_is_fatal_no_retry() -> None:
    # 400/401/403: error del lado nuestro (key inválida, request mal armada). No se reintenta.
    transport = FlakyTransport(_http_error(401), fail_times=99)
    provider = _provider(transport)

    with pytest.raises(ArchiveProviderError):
        provider.search("algo")
    assert transport.calls == 1  # sin reintentos
