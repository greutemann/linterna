"""M3 — agente investigador. Tests primero (7 criterios de docs/milestone-3-agent.md).

Retriever y LLM mockeados: deterministas, sin red ni keys. El LLM falso devuelve un
LLMResult con el texto que cada test controla (simulando la salida estructurada).
"""

from __future__ import annotations


from linterna.evidence import Evidence
from linterna.evidence.investigator import InvestigatorAgent
from linterna.router import LLMResult, Message
from linterna.types import Verdict


class FakeRetriever:
    def __init__(self, evidence: list[Evidence]) -> None:
        self._evidence = evidence
        self.calls = 0

    def retrieve(self, claim: str) -> list[Evidence]:
        self.calls += 1
        return self._evidence


class FakeLLM:
    """LLMClient falso: devuelve un texto fijo y registra el prompt recibido."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.last_messages: list[Message] | None = None
        self.calls = 0

    def complete(
        self, task: str, messages: list[Message], *, max_tokens: int, json_mode: bool = False
    ) -> LLMResult:
        self.calls += 1
        self.last_messages = messages
        return LLMResult(
            text=self._text, effective_model="fake", tokens=10, estimated_cost_usd=0.0
        )


_EVIDENCE = [
    Evidence(
        id="e1",
        url="https://oms.org/dengue",
        title="Brote de dengue 2026",
        publisher="OMS",
        snippet="Los casos de dengue aumentaron un 30% respecto al año anterior.",
    ),
    Evidence(
        id="e2",
        url="https://min-salud.gob/dengue",
        title="Parte epidemiológico",
        publisher="Ministerio de Salud",
        snippet="Se confirmaron focos en tres provincias.",
    ),
]


def _agent(evidence: list[Evidence], llm_text: str) -> tuple[InvestigatorAgent, FakeRetriever, FakeLLM]:
    retriever = FakeRetriever(evidence)
    llm = FakeLLM(llm_text)
    return InvestigatorAgent(retriever=retriever, llm=llm), retriever, llm


# --- Criterio 1: sin evidencia → abstención -----------------------------------

def test_no_evidence_abstains_without_calling_llm() -> None:
    agent, _retriever, llm = _agent([], "{}")
    result = agent.investigate("afirmación sin evidencia")

    assert result.verdict is Verdict.INSUFFICIENT
    assert result.sources == ()
    assert llm.calls == 0  # ni se molesta en llamar al modelo


# --- Criterio 2: evidencia + cita válida → veredicto --------------------------

def test_valid_citation_yields_verdict_with_sources() -> None:
    text = '{"verdict": "verdadero", "explanation": "La OMS lo confirma.", "cited_source_ids": ["e1"]}'
    agent, _r, _llm = _agent(_EVIDENCE, text)

    result = agent.investigate("El dengue aumentó en 2026")

    assert result.verdict is Verdict.TRUE
    assert len(result.sources) == 1
    assert result.sources[0].url == "https://oms.org/dengue"
    assert result.sources[0].publisher == "OMS"


# --- Criterio 3: cita inventada → rechazada → abstención ----------------------

def test_fabricated_citation_is_rejected_and_abstains() -> None:
    # El modelo cita "e99", que no fue recuperado.
    text = '{"verdict": "falso", "explanation": "x", "cited_source_ids": ["e99"]}'
    agent, _r, _llm = _agent(_EVIDENCE, text)

    result = agent.investigate("algo")

    assert result.verdict is Verdict.INSUFFICIENT
    assert result.sources == ()


def test_no_citations_abstains() -> None:
    text = '{"verdict": "falso", "explanation": "x", "cited_source_ids": []}'
    agent, _r, _llm = _agent(_EVIDENCE, text)
    assert agent.investigate("algo").verdict is Verdict.INSUFFICIENT


# --- Criterio 4: el modelo solo razona sobre evidencia recuperada -------------

def test_prompt_contains_evidence_and_constraint() -> None:
    text = '{"verdict": "verdadero", "explanation": "x", "cited_source_ids": ["e1"]}'
    agent, _r, llm = _agent(_EVIDENCE, text)

    agent.investigate("El dengue aumentó")

    assert llm.last_messages is not None
    prompt = "\n".join(m.content for m in llm.last_messages)
    # La evidencia recuperada está en el prompt...
    assert "e1" in prompt and "dengue aumentaron un 30%" in prompt
    # ...y se le prohíbe usar conocimiento propio (invariante 2).
    assert "solo" in prompt.lower() and "evidencia" in prompt.lower()


# --- Criterio 5: respuesta no parseable → abstención --------------------------

def test_unparseable_response_abstains() -> None:
    agent, _r, _llm = _agent(_EVIDENCE, "lo siento, no puedo responder eso")
    assert agent.investigate("algo").verdict is Verdict.INSUFFICIENT


# --- Criterio 6: veredicto desconocido → abstención ---------------------------

def test_unknown_verdict_label_abstains() -> None:
    text = '{"verdict": "quizas", "explanation": "x", "cited_source_ids": ["e1"]}'
    agent, _r, _llm = _agent(_EVIDENCE, text)
    assert agent.investigate("algo").verdict is Verdict.INSUFFICIENT


def test_json_wrapped_in_fences_is_parsed() -> None:
    text = '```json\n{"verdict": "falso", "explanation": "x", "cited_source_ids": ["e2"]}\n```'
    agent, _r, _llm = _agent(_EVIDENCE, text)
    result = agent.investigate("algo")
    assert result.verdict is Verdict.FALSE
    assert result.sources[0].publisher == "Ministerio de Salud"
