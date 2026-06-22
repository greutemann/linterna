"""Carga de configuración del router desde YAML.

Toda la selección de modelos, presupuesto y límites vive en config, nunca en código
(invariantes 1 y 7). Cambiar de modelo/proveedor = editar el YAML.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .client import Task


@dataclass(frozen=True)
class Limits:
    request_timeout_s: float
    max_retries: int


@dataclass(frozen=True)
class RouterConfig:
    daily_usd_hard_cap: float
    routing: dict[str, tuple[str, ...]]  # task -> (primary, *fallbacks)
    limits: Limits
    log_pii: bool

    @classmethod
    def from_yaml(cls, path: str | Path) -> RouterConfig:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        routing: dict[str, tuple[str, ...]] = {}
        for task, spec in raw["routing"].items():
            primary = spec["primary"]
            fallback = spec.get("fallback") or []
            routing[task] = (primary, *fallback)
        limits = Limits(
            request_timeout_s=float(raw["limits"]["request_timeout_s"]),
            max_retries=int(raw["limits"]["max_retries"]),
        )
        return cls(
            daily_usd_hard_cap=float(raw["budget"]["daily_usd_hard_cap"]),
            routing=routing,
            limits=limits,
            log_pii=bool(raw.get("observability", {}).get("log_pii", False)),
        )

    def chain_for(self, task: Task) -> tuple[str, ...]:
        """Cadena de modelos para una tarea: primario seguido de fallbacks."""
        if task not in self.routing:
            raise KeyError(f"No hay ruteo configurado para la tarea {task!r}.")
        return self.routing[task]
