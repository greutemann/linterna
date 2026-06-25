"""JSON mode: el router pide salida estructurada y el agente la usa.

Sube la confiabilidad del formato sin tocar la validación de citas (invariante 3).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from linterna.evidence import Evidence
from linterna.evidence.investigator import InvestigatorAgent
from linterna.router import LLMResult, Message
from linterna.router.config import RouterConfig
from linterna.router.router import RouterClient


def _ok(model: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"verdict":"falso","explanation":"x","cited_source_ids":["e1"]}'))],
        usage=SimpleNamespace(total_tokens=5),
        model=model,
    )


def _cfg(tmp_path: Path) -> RouterConfig:
    yaml = """
budget:
  daily_usd_hard_cap: 5.0
routing:
  claim_extraction:
    primary: gemini/x
    fallback: []
  synthesis:
    primary: gemini/synth
    fallback: []
limits:
  request_timeout_s: 30
  max_retries: 1
observability:
  log_pii: false
"""
    path = tmp_path / "router.yaml"
    path.write_text(yaml, encoding="utf-8")
    return RouterConfig.from_yaml(path)


def test_router_forwards_json_mode_to_provider(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def completion(*, model: str, **kwargs: Any) -> Any:
        captured.update(kwargs)
        return _ok(model)

    client = RouterClient(_cfg(tmp_path), completion_fn=completion, cost_fn=lambda _r: 0.0)
    client.complete("synthesis", [Message(role="user", content="hola")], max_tokens=50, json_mode=True)

    assert captured.get("response_format") == {"type": "json_object"}


def test_router_forwards_temperature(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def completion(*, model: str, **kwargs: Any) -> Any:
        captured.update(kwargs)
        return _ok(model)

    client = RouterClient(_cfg(tmp_path), completion_fn=completion, cost_fn=lambda _r: 0.0)
    client.complete("synthesis", [Message(role="user", content="hola")], max_tokens=50, temperature=0.0)

    assert captured.get("temperature") == 0.0


def test_router_omits_json_mode_by_default(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def completion(*, model: str, **kwargs: Any) -> Any:
        captured.update(kwargs)
        return _ok(model)

    client = RouterClient(_cfg(tmp_path), completion_fn=completion, cost_fn=lambda _r: 0.0)
    client.complete("synthesis", [Message(role="user", content="hola")], max_tokens=50)

    assert "response_format" not in captured


class RecordingLLM:
    def __init__(self) -> None:
        self.json_mode_seen: bool | None = None

    def complete(
        self,
        task: str,
        messages: list[Message],
        *,
        max_tokens: int,
        json_mode: bool = False,
        temperature: float | None = None,
    ) -> LLMResult:
        self.json_mode_seen = json_mode
        return LLMResult(
            text='{"stance":"refutes","support_pct":10,"explanation":"x","cited_source_ids":["e1"]}',
            effective_model="fake", tokens=5, estimated_cost_usd=0.0,
        )


def test_agent_requests_json_mode() -> None:
    llm = RecordingLLM()
    evidence = [Evidence(id="e1", url="https://x/y", title="t", publisher="P", snippet="s")]

    class R:
        def retrieve(self, claim: str) -> list[Evidence]:
            return evidence

    agent = InvestigatorAgent(retriever=R(), llm=llm)
    agent.investigate("algo")

    assert llm.json_mode_seen is True  # el agente pide JSON estructurado
