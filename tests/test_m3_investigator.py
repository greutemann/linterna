"""M3 — agente investigador (rediseño). El agente APORTA evidencia, no sentencia.

Cubre: descarte de fuentes marginales, no emitir TRUE/FALSE, lean por confiabilidad
(respaldado fuerte exige fuente de alta confianza), validación de citas y abstención.
Incluye la reproducción del incidente (afirmación dañina con fuentes fringe).
"""

from __future__ import annotations

from linterna.evidence import Evidence
from linterna.evidence.investigator import InvestigatorAgent
from linterna.router import LLMResult, Message
from linterna.types import Light, Verdict


class FakeRetriever:
    def __init__(self, evidence: list[Evidence]) -> None:
        self._evidence = evidence
        self.calls = 0

    def retrieve(self, claim: str) -> list[Evidence]:
        self.calls += 1
        return self._evidence


class FakeLLM:
    def __init__(self, text: str) -> None:
        self._text = text
        self.last_messages: list[Message] | None = None
        self.calls = 0
        self.json_mode: bool | None = None
        self.temperature: float | None = None

    def complete(
        self,
        task: str,
        messages: list[Message],
        *,
        max_tokens: int,
        json_mode: bool = False,
        temperature: float | None = None,
    ) -> LLMResult:
        self.calls += 1
        self.last_messages = messages
        self.json_mode = json_mode
        self.temperature = temperature
        return LLMResult(text=self._text, effective_model="fake", tokens=10, estimated_cost_usd=0.0)


def _ev(id_: str, url: str) -> Evidence:
    return Evidence(id=id_, url=url, title="t", publisher="P", snippet="s")


_HIGH = _ev("e1", "https://www.who.int/dengue")        # alta confiabilidad
_UNKNOWN = _ev("e2", "https://un-blog-cualquiera.com")  # desconocida
_DENY = _ev("e3", "https://www.infowars.com/x")         # descartada


def _agent(evidence: list[Evidence], llm_text: str) -> tuple[InvestigatorAgent, FakeRetriever, FakeLLM]:
    r, llm = FakeRetriever(evidence), FakeLLM(llm_text)
    return InvestigatorAgent(retriever=r, llm=llm), r, llm


def _json(stance: str, ids: list[str], pct: int = 50) -> str:
    import json
    return json.dumps({"stance": stance, "support_pct": pct, "explanation": "resumen", "cited_source_ids": ids})


# --- abstención -----------------------------------------------------------------

def test_no_evidence_abstains_without_calling_llm() -> None:
    agent, _r, llm = _agent([], "{}")
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT
    assert llm.calls == 0


def test_only_fringe_sources_are_discarded_and_abstains() -> None:
    # INCIDENTE: afirmación dañina cuya "evidencia" son solo fuentes fringe.
    agent, _r, llm = _agent([_DENY], _json("supports", ["e3"], 95))
    result = agent.investigate("afirmación pseudocientífica dañina")
    assert result.verdict is Verdict.INSUFFICIENT  # nunca "verdadero"
    assert llm.calls == 0  # ni se razona sobre fuentes descartadas


# --- no sentencia (nunca TRUE/FALSE) -------------------------------------------

def test_agent_never_returns_authoritative_verdict() -> None:
    agent, _r, _llm = _agent([_HIGH], _json("supports", ["e1"], 80))
    v = agent.investigate("algo").verdict
    assert v not in {Verdict.TRUE, Verdict.FALSE, Verdict.MISLEADING}
    assert v is Verdict.EVIDENCE_SUPPORTS


def test_reliable_sources_refuting_yields_evidence_refutes() -> None:
    # El caso del incidente, BIEN resuelto: fuentes confiables contradicen -> rojo.
    agent, _r, _llm = _agent([_HIGH], _json("refutes", ["e1"], 8))
    result = agent.investigate("la afirmación X")
    assert result.verdict is Verdict.EVIDENCE_REFUTES
    assert result.light is Light.RED
    assert result.support_pct == 8
    assert result.kind == "evidencia"


# --- un lean fuerte exige fuente de alta confiabilidad -------------------------

def test_strong_support_without_high_trust_is_downgraded_to_mixed() -> None:
    # El modelo dice "supports" pero solo cita una fuente desconocida -> dividida.
    agent, _r, _llm = _agent([_UNKNOWN], _json("supports", ["e2"], 90))
    assert agent.investigate("x").verdict is Verdict.EVIDENCE_MIXED


def test_support_with_high_trust_stays_supported() -> None:
    agent, _r, _llm = _agent([_HIGH], _json("supports", ["e1"], 85))
    result = agent.investigate("x")
    assert result.verdict is Verdict.EVIDENCE_SUPPORTS
    assert result.support_pct == 85


# --- validación de citas / parseo ----------------------------------------------

def test_fabricated_citation_abstains() -> None:
    agent, _r, _llm = _agent([_HIGH], _json("refutes", ["e99"], 5))
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


def test_unparseable_response_abstains() -> None:
    agent, _r, _llm = _agent([_HIGH], "no puedo responder")
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


def test_insufficient_stance_abstains() -> None:
    agent, _r, _llm = _agent([_HIGH], _json("insufficient", []))
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


# --- prompt y parámetros --------------------------------------------------------

def test_prompt_weighs_reliability_and_forbids_sentencing() -> None:
    agent, _r, llm = _agent([_HIGH], _json("supports", ["e1"], 70))
    agent.investigate("x")
    prompt = "\n".join(m.content for m in llm.last_messages or [])
    assert "confiabilidad" in prompt.lower()
    assert "no declares" in prompt.lower() or "no sos un oráculo" in prompt.lower()


def test_agent_uses_json_mode_and_zero_temperature() -> None:
    agent, _r, llm = _agent([_HIGH], _json("supports", ["e1"], 70))
    agent.investigate("x")
    assert llm.json_mode is True
    assert llm.temperature == 0.0
