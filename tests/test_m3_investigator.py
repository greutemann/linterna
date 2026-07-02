"""M3 — agente investigador (rediseño). El agente APORTA evidencia, no sentencia.

Cubre: descarte de fuentes marginales, no emitir TRUE/FALSE, lean por confiabilidad
(respaldado fuerte exige fuente de alta confianza), validación de citas y abstención.
Incluye la reproducción del incidente (afirmación dañina con fuentes fringe).
"""

from __future__ import annotations

from linterna.evidence import Evidence
from linterna.evidence.budget import SearchBudgetExceeded
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
    # synthesize=True para ejercitar el motor de síntesis (lean + %).
    r, llm = FakeRetriever(evidence), FakeLLM(llm_text)
    return InvestigatorAgent(retriever=r, llm=llm, synthesize=True), r, llm


def _json(stance: str, ids: list[str], pct: int = 50) -> str:
    import json
    return json.dumps({"stance": stance, "support_pct": pct, "explanation": "resumen", "cited_source_ids": ids})


# --- abstención -----------------------------------------------------------------

def test_no_evidence_abstains_without_calling_llm() -> None:
    agent, _r, llm = _agent([], "{}")
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT
    assert llm.calls == 0


def test_search_budget_exceeded_returns_graceful_message() -> None:
    # Alcanzado el tope: corta amable (no rompe con 500) y no llama al modelo.
    class BrokeRetriever:
        def retrieve(self, claim: str) -> list[Evidence]:
            raise SearchBudgetExceeded("tope")

    llm = FakeLLM("{}")
    agent = InvestigatorAgent(retriever=BrokeRetriever(), llm=llm, synthesize=True)
    result = agent.investigate("x")

    assert result.verdict is Verdict.INSUFFICIENT
    assert "límite de consultas" in result.explanation.lower()
    assert llm.calls == 0


def test_only_fringe_sources_are_discarded_and_abstains() -> None:
    # INCIDENTE: afirmación dañina cuya "evidencia" son solo fuentes fringe.
    agent, _r, llm = _agent([_DENY], _json("supports", ["e3"], 95))
    result = agent.investigate("afirmación pseudocientífica dañina")
    assert result.verdict is Verdict.INSUFFICIENT  # nunca "verdadero"
    assert llm.calls == 0  # ni se razona sobre fuentes descartadas


# --- cautela asimétrica: desmiente (rojo), nunca afirma (verde) ----------------

def test_reliable_sources_refuting_yields_evidence_refutes() -> None:
    # Desmentir con fuentes confiables -> rojo. Acá vuelve la utilidad (ej. "todos los
    # loros son verdes" -> falso con un contraejemplo confiable).
    agent, _r, _llm = _agent([_HIGH], _json("refutes", ["e1"], 8))
    result = agent.investigate("la afirmación X")
    assert result.verdict is Verdict.EVIDENCE_REFUTES
    assert result.light is Light.RED
    assert result.support_pct == 8
    assert result.kind == "evidencia"


def test_supports_is_never_affirmed_falls_back_to_leads() -> None:
    # Aunque el modelo diga "supports" con fuente confiable, NO se afirma (verde): se
    # ofrecen fuentes-guía. Afirmar desde evidencia web es el riesgo (caso raza/IQ).
    agent, _r, _llm = _agent([_HIGH], _json("supports", ["e1"], 95))
    result = agent.investigate("una afirmación cargada")
    assert result.verdict is Verdict.INSUFFICIENT  # sin luz verde
    assert result.support_pct is None
    assert len(result.sources) >= 1  # pero ofrece fuentes para investigar


def test_mixed_stance_falls_back_to_leads() -> None:
    agent, _r, _llm = _agent([_HIGH], _json("mixed", ["e1"], 50))
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


def test_refute_without_high_trust_falls_back_to_leads() -> None:
    # No desmentimos con fuentes no confiables: caemos a fuentes-guía (sin rojo).
    agent, _r, _llm = _agent([_UNKNOWN], _json("refutes", ["e2"], 5))
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


# --- validación de citas / parseo (caen a fuentes-guía, no inventan veredicto) -

def test_fabricated_citation_falls_back_to_leads() -> None:
    agent, _r, _llm = _agent([_HIGH], _json("refutes", ["e99"], 5))
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


def test_unparseable_response_falls_back_to_leads() -> None:
    agent, _r, _llm = _agent([_HIGH], "no puedo responder")
    assert agent.investigate("x").verdict is Verdict.INSUFFICIENT


def test_insufficient_stance_falls_back_to_leads() -> None:
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


# --- modo seguro por defecto (synthesize=False): fuentes como leads, sin veredicto ------

def test_safe_mode_offers_sources_without_model_verdict() -> None:
    high2 = _ev("e9", "https://www.bbc.com/mundo/x")
    r, llm = FakeRetriever([_HIGH, high2]), FakeLLM(_json("supports", ["e1"], 99))
    agent = InvestigatorAgent(retriever=r, llm=llm)  # synthesize=False por defecto

    result = agent.investigate("una afirmación cualquiera")

    assert llm.calls == 0  # NO se le pide veredicto/síntesis al modelo
    assert result.verdict is Verdict.INSUFFICIENT  # sin luz verde/roja
    assert result.support_pct is None
    assert len(result.sources) == 2  # ofrece las fuentes confiables como puntos de partida


def test_safe_mode_shows_only_high_trust_when_available() -> None:
    r, llm = FakeRetriever([_UNKNOWN, _DENY, _HIGH]), FakeLLM("{}")
    agent = InvestigatorAgent(retriever=r, llm=llm)

    urls = [s.url for s in agent.investigate("x").sources]
    assert urls == ["https://www.who.int/dengue"]  # solo la de alta confiabilidad


def test_safe_mode_falls_back_to_unknown_when_no_high_trust() -> None:
    r, llm = FakeRetriever([_UNKNOWN, _DENY]), FakeLLM("{}")
    agent = InvestigatorAgent(retriever=r, llm=llm)

    urls = [s.url for s in agent.investigate("x").sources]
    assert "https://www.infowars.com/x" not in urls  # fringe descartada igual
    assert "https://un-blog-cualquiera.com" in urls   # desconocida como punto de inicio
