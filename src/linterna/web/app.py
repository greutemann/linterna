"""API web socrática (M4).

`create_app(pipeline)` arma una app FastAPI sobre cualquier objeto con `verify(claim)`.
El pipeline se inyecta: los tests pasan un stub; el runtime pasa el real. La salida del
LLM ya pasó por validación de citas aguas arriba (invariante 3) antes de llegar acá.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

from linterna.types import Verdict, VerificationResult

from .page import INDEX_HTML, PRIVACY_HTML


class _RateLimiter:
    """Limitador por clave (IP) con ventana deslizante. Protege las keys del abuso."""

    def __init__(self, max_requests: int, window_s: float, clock: Callable[[], float]) -> None:
        self._max = max_requests
        self._window_s = window_s
        self._clock = clock
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = self._clock()
        recent = [t for t in self._hits[key] if t > now - self._window_s]
        if len(recent) >= self._max:
            self._hits[key] = recent
            return False
        recent.append(now)
        self._hits[key] = recent
        return True


def _client_ip(request: Request) -> str:
    # Detrás de Cloud Run la IP real viene en X-Forwarded-For (primer salto).
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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


def create_app(
    pipeline: _Pipeline,
    *,
    rate_limit: int = 30,
    rate_window_s: float = 60.0,
    clock: Callable[[], float] = time.monotonic,
) -> FastAPI:
    app = FastAPI(title="Linterna", description="Servicio público de verificación. No es un oráculo.")
    limiter = _RateLimiter(rate_limit, rate_window_s, clock)

    @app.post("/api/verify")
    def verify(payload: ClaimIn, request: Request) -> dict[str, Any]:
        if not limiter.allow(_client_ip(request)):
            raise HTTPException(status_code=429, detail="Demasiadas consultas. Probá en un momento.")
        return _result_to_dict(pipeline.verify(payload.claim))

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return INDEX_HTML

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy() -> str:
        return PRIVACY_HTML

    return app
