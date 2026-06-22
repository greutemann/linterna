"""Caché de verificaciones (invariante 6: jamás identidad del usuario).

Sólo se almacena la afirmación normalizada y su resultado. La firma de la caché no
tiene lugar para datos personales. El backend es intercambiable: por ahora en memoria;
SQLite u otro llegan cuando haga falta (decisión pendiente, ver milestone-1-archive.md).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol

from linterna.types import Light, Source, VerificationResult, Verdict


class Cache(Protocol):
    """Contrato mínimo de caché. Clave = afirmación normalizada."""

    def get(self, key: str) -> VerificationResult | None: ...
    def set(self, key: str, value: VerificationResult) -> None: ...
    def keys(self) -> Iterator[str]: ...


class InMemoryCache:
    """Implementación en memoria. Útil para tests y como default del MVP."""

    def __init__(self) -> None:
        self._store: dict[str, VerificationResult] = {}

    def get(self, key: str) -> VerificationResult | None:
        return self._store.get(key)

    def set(self, key: str, value: VerificationResult) -> None:
        self._store[key] = value

    def keys(self) -> Iterator[str]:
        return iter(self._store.keys())


def _result_to_dict(result: VerificationResult) -> dict[str, Any]:
    return {
        "verdict": result.verdict.value,
        "light": result.light.value,
        "explanation": result.explanation,
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


def _result_from_dict(data: dict[str, Any]) -> VerificationResult:
    return VerificationResult(
        verdict=Verdict(data["verdict"]),
        light=Light(data["light"]),
        explanation=data["explanation"],
        sources=tuple(
            Source(
                url=s["url"],
                title=s["title"],
                publisher=s["publisher"],
                reviewed_at=s.get("reviewed_at"),
            )
            for s in data["sources"]
        ),
    )


class JsonFileCache:
    """Caché persistente en un archivo JSON. Sobrevive al reinicio del proceso.

    Solo persiste {afirmación normalizada -> resultado}. Sin identidad del usuario
    (invariante 6). Escritura atómica vía archivo temporal + replace.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._store: dict[str, VerificationResult] = self._load()

    def _load(self) -> dict[str, VerificationResult]:
        if not self._path.is_file():
            return {}
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {key: _result_from_dict(value) for key, value in raw.items()}

    def _flush(self) -> None:
        serializable = {key: _result_to_dict(value) for key, value in self._store.items()}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def get(self, key: str) -> VerificationResult | None:
        return self._store.get(key)

    def set(self, key: str, value: VerificationResult) -> None:
        self._store[key] = value
        self._flush()

    def keys(self) -> Iterator[str]:
        return iter(self._store.keys())
