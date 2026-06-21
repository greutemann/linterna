"""Caché de verificaciones (invariante 6: jamás identidad del usuario).

Sólo se almacena la afirmación normalizada y su resultado. La firma de la caché no
tiene lugar para datos personales. El backend es intercambiable: por ahora en memoria;
SQLite u otro llegan cuando haga falta (decisión pendiente, ver milestone-1-archive.md).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from linterna.types import VerificationResult


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
