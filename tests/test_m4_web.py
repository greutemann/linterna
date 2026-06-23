"""M4 — API web socrática. Tests primero, con pipeline mockeado (sin red ni keys).

La UX es socrática: muestra la evidencia y deja la conclusión al usuario. La API expone
el resultado del pipeline; la página web decide cómo presentarlo (evidencia primero).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from linterna.types import Light, Source, Verdict, VerificationResult
from linterna.web.app import create_app


class StubPipeline:
    def __init__(self, result: VerificationResult) -> None:
        self._result = result
        self.last_claim: str | None = None

    def verify(self, claim: str) -> VerificationResult:
        self.last_claim = claim
        return self._result


_VERDICT_RESULT = VerificationResult(
    verdict=Verdict.FALSE,
    light=Light.RED,
    explanation="Las fuentes desmienten la afirmación.",
    sources=(
        Source(url="https://rtve.es/x", title="Es un bulo", publisher="RTVE", reviewed_at="2024-02-28"),
    ),
)

_ABSTENTION = VerificationResult(
    verdict=Verdict.INSUFFICIENT,
    light=Light.GREY,
    explanation="Sin evidencia validada no se emite veredicto.",
    sources=(),
)


def _client(result: VerificationResult) -> tuple[TestClient, StubPipeline]:
    pipeline = StubPipeline(result)
    return TestClient(create_app(pipeline)), pipeline


def test_verify_returns_verdict_and_sources() -> None:
    client, pipeline = _client(_VERDICT_RESULT)

    resp = client.post("/api/verify", json={"claim": "agua con limón cura el cáncer"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "falso"
    assert body["light"] == "rojo"
    assert body["is_abstention"] is False
    assert body["sources"][0]["url"] == "https://rtve.es/x"
    assert body["sources"][0]["publisher"] == "RTVE"
    assert pipeline.last_claim == "agua con limón cura el cáncer"


def test_abstention_is_marked() -> None:
    client, _p = _client(_ABSTENTION)

    body = client.post("/api/verify", json={"claim": "algo nunca verificado"}).json()

    assert body["verdict"] == "insuficiente"
    assert body["is_abstention"] is True
    assert body["sources"] == []


def test_empty_claim_is_rejected() -> None:
    client, _p = _client(_VERDICT_RESULT)
    resp = client.post("/api/verify", json={"claim": "   "})
    assert resp.status_code == 422


def test_missing_claim_is_rejected() -> None:
    client, _p = _client(_VERDICT_RESULT)
    resp = client.post("/api/verify", json={})
    assert resp.status_code == 422


def test_index_page_served() -> None:
    client, _p = _client(_VERDICT_RESULT)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    # La postura socrática está en la página: muestra fuentes, no sentencia.
    assert "fuentes" in resp.text.lower()
    # Mantiene a la vista la afirmación consultada junto a los resultados.
    assert "Afirmación consultada" in resp.text
    # Explica el esquema de verificación para quien quiera entenderlo.
    assert "Cómo verificamos" in resp.text


def test_privacy_page_served() -> None:
    client, _p = _client(_VERDICT_RESULT)
    resp = client.get("/privacy")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    # Disclosure clave para la Chrome Web Store: qué se manda y que no hay PII.
    assert "privacidad" in resp.text.lower()
    assert "pii" in resp.text.lower()
