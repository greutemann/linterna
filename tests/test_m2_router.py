"""M2 — router de modelos con fallback. Tests primero (los 6 criterios del doc).

El cliente real usa LiteLLM, pero acá se inyecta un `completion_fn` falso: los tests
son deterministas y no tocan la red ni necesitan keys. Cubre swap por config, fallback,
corte duro de presupuesto, ruteo por tarea, sin PII en logs y timeout/reintentos.
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from linterna.router import BudgetExceeded, Message, ProviderUnavailable
from linterna.router.config import RouterConfig
from linterna.router.router import RouterClient

# --- dobles de prueba ----------------------------------------------------------


def _fake_response(model: str, text: str = "ok", tokens: int = 42) -> SimpleNamespace:
    """Imita la forma mínima de una respuesta de litellm que el router consume."""
    message = SimpleNamespace(content=text)
    choice = SimpleNamespace(message=message)
    usage = SimpleNamespace(total_tokens=tokens)
    return SimpleNamespace(choices=[choice], usage=usage, model=model)


class RecordingCompletion:
    """completion_fn que registra llamadas y devuelve una respuesta canónica."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, *, model: str, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        self.calls.append({"model": model, "messages": messages, **kwargs})
        return _fake_response(model)


def _cost_fn(_response: Any) -> float:
    return 0.001  # costo fijo y conocido para tests deterministas


def _write_config(tmp_path: Path, *, primary: str, fallback: list[str] | None = None,
                  cap: float = 5.0, retries: int = 2, timeout: int = 30,
                  extraction_primary: str = "gemini/flash-lite") -> RouterConfig:
    fb = "\n".join(f"      - {m}" for m in (fallback or [])) or "      []"
    yaml = f"""
budget:
  daily_usd_hard_cap: {cap}
routing:
  claim_extraction:
    primary: {extraction_primary}
    fallback: []
  synthesis:
    primary: {primary}
    fallback:
{fb}
limits:
  request_timeout_s: {timeout}
  max_retries: {retries}
observability:
  log_pii: false
"""
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "router.yaml"
    path.write_text(yaml, encoding="utf-8")
    return RouterConfig.from_yaml(path)


_MESSAGES = [Message(role="user", content="¿La afirmación X es verdadera?")]


# --- Criterio 1: swap por config ----------------------------------------------

def test_swap_primary_model_by_config_only(tmp_path: Path) -> None:
    fake = RecordingCompletion()

    cfg_a = _write_config(tmp_path / "a", primary="gemini/modelo-A")
    client_a = RouterClient(cfg_a, completion_fn=fake, cost_fn=_cost_fn)
    res_a = client_a.complete("synthesis", _MESSAGES, max_tokens=100)

    cfg_b = _write_config(tmp_path / "b", primary="gemini/modelo-B")
    client_b = RouterClient(cfg_b, completion_fn=fake, cost_fn=_cost_fn)
    res_b = client_b.complete("synthesis", _MESSAGES, max_tokens=100)

    # Misma lógica, distinto modelo efectivo — sin tocar código.
    assert res_a.effective_model == "gemini/modelo-A"
    assert res_b.effective_model == "gemini/modelo-B"


# --- Criterio 2: fallback automático ------------------------------------------

class FlakyCompletion:
    """Falla para el/los modelos en `down`, responde para el resto."""

    def __init__(self, down: set[str]) -> None:
        self.down = down
        self.calls: list[str] = []

    def __call__(self, *, model: str, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        self.calls.append(model)
        if model in self.down:
            raise RuntimeError(f"proveedor caído: {model}")
        return _fake_response(model)


def test_fallback_when_primary_down(tmp_path: Path) -> None:
    fake = FlakyCompletion(down={"gemini/primary"})
    cfg = _write_config(tmp_path, primary="gemini/primary", fallback=["gemini/backup"])
    client = RouterClient(cfg, completion_fn=fake, cost_fn=_cost_fn)

    result = client.complete("synthesis", _MESSAGES, max_tokens=100)

    assert result.effective_model == "gemini/backup"
    assert "gemini/primary" in fake.calls and "gemini/backup" in fake.calls


def test_provider_unavailable_when_whole_chain_down(tmp_path: Path) -> None:
    fake = FlakyCompletion(down={"gemini/primary", "gemini/backup"})
    cfg = _write_config(tmp_path, primary="gemini/primary", fallback=["gemini/backup"])
    client = RouterClient(cfg, completion_fn=fake, cost_fn=_cost_fn)

    with pytest.raises(ProviderUnavailable):
        client.complete("synthesis", _MESSAGES, max_tokens=100)


# --- Criterio 3: corte duro de presupuesto ------------------------------------

def test_budget_hard_cap_blocks_call(tmp_path: Path) -> None:
    fake = RecordingCompletion()
    cfg = _write_config(tmp_path, primary="gemini/x", cap=0.001)
    client = RouterClient(cfg, completion_fn=fake, cost_fn=_cost_fn)

    # Primera llamada consume hasta el tope (costo 0.001 == cap).
    client.complete("synthesis", _MESSAGES, max_tokens=100)
    calls_after_first = len(fake.calls)

    # La segunda debe cortar ANTES de llamar al proveedor.
    with pytest.raises(BudgetExceeded):
        client.complete("synthesis", _MESSAGES, max_tokens=100)
    assert len(fake.calls) == calls_after_first  # no hubo nueva llamada


# --- Criterio 4: ruteo por tarea ----------------------------------------------

def test_routing_per_task(tmp_path: Path) -> None:
    fake = RecordingCompletion()
    cfg = _write_config(
        tmp_path, primary="gemini/synth-model", extraction_primary="gemini/cheap-model"
    )
    client = RouterClient(cfg, completion_fn=fake, cost_fn=_cost_fn)

    extraction = client.complete("claim_extraction", _MESSAGES, max_tokens=50)
    synthesis = client.complete("synthesis", _MESSAGES, max_tokens=200)

    assert extraction.effective_model == "gemini/cheap-model"
    assert synthesis.effective_model == "gemini/synth-model"


# --- Criterio 5: sin PII en logs ----------------------------------------------

def test_no_pii_in_logs(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    fake = RecordingCompletion()
    cfg = _write_config(tmp_path, primary="gemini/x")
    client = RouterClient(cfg, completion_fn=fake, cost_fn=_cost_fn)

    secret = "DATO_IDENTIFICABLE_DEL_USUARIO_12345"
    with caplog.at_level(logging.DEBUG, logger="linterna.router"):
        client.complete("synthesis", [Message(role="user", content=secret)], max_tokens=10)

    assert caplog.records, "el router debería loguear al menos la metadata de la llamada"
    for record in caplog.records:
        assert secret not in record.getMessage()


# --- Criterio 6: timeout / reintentos acotados --------------------------------

class TimingOutCompletion:
    """Siempre falla (simula timeout). Registra el timeout recibido."""

    def __init__(self) -> None:
        self.calls = 0
        self.timeouts: list[Any] = []

    def __call__(self, *, model: str, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        self.calls += 1
        self.timeouts.append(kwargs.get("timeout"))
        raise TimeoutError("colgada")


def test_retries_are_bounded_and_timeout_is_passed(tmp_path: Path) -> None:
    fake = TimingOutCompletion()
    cfg = _write_config(tmp_path, primary="gemini/only", retries=2, timeout=30)
    client = RouterClient(cfg, completion_fn=fake, cost_fn=_cost_fn)

    with pytest.raises(ProviderUnavailable):
        client.complete("synthesis", _MESSAGES, max_tokens=10)

    # 1 intento + 2 reintentos = 3 llamadas, ni una más. Y se pasó el timeout configurado.
    assert fake.calls == 3
    assert all(t == 30 for t in fake.timeouts)
