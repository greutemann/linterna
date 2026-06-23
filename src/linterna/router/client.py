"""Contrato de interfaz del router (M2).

El resto del código depende SOLO de esto. Nunca de un SDK de proveedor concreto
(invariante 1 y 7). La salida del LLM NO es evidencia: debe pasar luego por validación
de citas (invariante 2/3).

Esto es scaffold: define el contrato. La implementación (fallback, ruteo por tarea,
control de presupuesto, logging sin PII) llega cuando se construya M2 — tests primero,
según los criterios de éxito de docs/milestone-2-router.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

Task = Literal["claim_extraction", "synthesis"]


@dataclass(frozen=True)
class Message:
    """Un turno de conversación enviado al modelo."""

    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class LLMResult:
    """Resultado de una llamada. `effective_model` permite auditar qué resolvió la request."""

    text: str
    effective_model: str
    tokens: int
    estimated_cost_usd: float


class BudgetExceeded(Exception):
    """Tope de presupuesto alcanzado. Corte duro: la llamada NO se realiza (invariante operativo)."""


class ProviderUnavailable(Exception):
    """Todos los proveedores de la cadena de fallback fallaron."""


@runtime_checkable
class LLMClient(Protocol):
    """Interfaz estable que consume el resto del código."""

    def complete(
        self,
        task: Task,
        messages: list[Message],
        *,
        max_tokens: int,
        json_mode: bool = False,
    ) -> LLMResult:
        """Resuelve una llamada al LLM aplicando ruteo por tarea, fallback y presupuesto.

        Con ``json_mode=True`` se pide salida estructurada (JSON) al proveedor, para que
        la respuesta sea parseable de forma confiable. No reemplaza la validación de citas
        (invariante 3), que sigue siendo determinística aguas abajo.

        Lanza ``BudgetExceeded`` (corte duro) o ``ProviderUnavailable`` (tras agotar fallbacks).
        """
        ...
