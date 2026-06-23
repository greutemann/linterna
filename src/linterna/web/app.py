"""API web socrática (M4).

`create_app(pipeline)` arma una app FastAPI sobre cualquier objeto con `verify(claim)`.
El pipeline se inyecta: los tests pasan un stub; el runtime pasa el real. La salida del
LLM ya pasó por validación de citas aguas arriba (invariante 3) antes de llegar acá.
"""

from __future__ import annotations

from typing import Any, Protocol

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

from linterna.types import Verdict, VerificationResult

from .page import INDEX_HTML


class _Pipeline(Protocol):
    def verify(self, claim: str) -> VerificationResult: ...


class ClaimIn(BaseModel):
    claim: str

    @field_validator("claim")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("La afirmación no puede estar vacía.")
        return v


def _result_to_dict(result: VerificationResult) -> dict[str, Any]:
    return {
        "verdict": result.verdict.value,
        "light": result.light.value,
        "explanation": result.explanation,
        "is_abstention": result.verdict is Verdict.INSUFFICIENT,
        "sources": [
            {
                "url": s.url,
                "title": s.title,
                "publisher": s.publisher,
                "reviewed_at": s.reviewed_at,
            }
            for s in result.sources
        ],
    }


def create_app(pipeline: _Pipeline) -> FastAPI:
    app = FastAPI(title="Linterna", description="Servicio público de verificación. No es un oráculo.")

    @app.post("/api/verify")
    def verify(payload: ClaimIn) -> dict[str, Any]:
        return _result_to_dict(pipeline.verify(payload.claim))

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return INDEX_HTML

    return app
