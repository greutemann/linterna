"""Router: errores reintentables vs fatales.

Un timeout o un 503 son transitorios -> reintentar (acotado). Un 401/400 es fatal
(key inválida, request mal armada) -> no reintentar en ese modelo, pasar al fallback.
Así no se malgastan reintentos en errores que no se van a resolver solos.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from linterna.router import Message, ProviderUnavailable
from linterna.router.config import RouterConfig
from linterna.router.router import RouterClient


def _cfg(tmp_path: Path, *, primary: str, fallback: list[str], retries: int = 2) -> RouterConfig:
    fb = "\n".join(f"      - {m}" for m in fallback) or "      []"
    yaml = f"""
budget:
  daily_usd_hard_cap: 5.0
routing:
  claim_extraction:
    primary: x
    fallback: []
  synthesis:
    primary: {primary}
    fallback:
{fb}
limits:
  request_timeout_s: 30
  max_retries: {retries}
observability:
  log_pii: false
"""
    path = tmp_path / "router.yaml"
    path.write_text(yaml, encoding="utf-8")
    return RouterConfig.from_yaml(path)


def _ok(model: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
        usage=SimpleNamespace(total_tokens=1),
        model=model,
    )


class Httpish(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


_MSG = [Message(role="user", content="hola")]


def test_fatal_error_skips_retries_and_falls_back(tmp_path: Path) -> None:
    calls: list[str] = []

    def completion(*, model: str, **_kw: Any) -> Any:
        calls.append(model)
        if model == "gemini/primary":
            raise Httpish(401)  # fatal: no se reintenta
        return _ok(model)

    cfg = _cfg(tmp_path, primary="gemini/primary", fallback=["gemini/backup"])
    client = RouterClient(cfg, completion_fn=completion, cost_fn=lambda _r: 0.0)

    result = client.complete("synthesis", _MSG, max_tokens=10)

    assert result.effective_model == "gemini/backup"
    # primary se intentó UNA sola vez (sin reintentos), luego backup.
    assert calls == ["gemini/primary", "gemini/backup"]


def test_retryable_error_is_retried_then_falls_back(tmp_path: Path) -> None:
    calls: list[str] = []

    def completion(*, model: str, **_kw: Any) -> Any:
        calls.append(model)
        if model == "gemini/primary":
            raise Httpish(503)  # transitorio: se reintenta
        return _ok(model)

    cfg = _cfg(tmp_path, primary="gemini/primary", fallback=["gemini/backup"], retries=2)
    client = RouterClient(cfg, completion_fn=completion, cost_fn=lambda _r: 0.0)

    result = client.complete("synthesis", _MSG, max_tokens=10)

    assert result.effective_model == "gemini/backup"
    # primary: 1 intento + 2 reintentos = 3, luego backup.
    assert calls == ["gemini/primary", "gemini/primary", "gemini/primary", "gemini/backup"]


def test_fatal_on_whole_chain_raises_unavailable(tmp_path: Path) -> None:
    def completion(*, model: str, **_kw: Any) -> Any:
        raise Httpish(400)

    cfg = _cfg(tmp_path, primary="gemini/a", fallback=["gemini/b"])
    client = RouterClient(cfg, completion_fn=completion, cost_fn=lambda _r: 0.0)

    with pytest.raises(ProviderUnavailable):
        client.complete("synthesis", _MSG, max_tokens=10)
