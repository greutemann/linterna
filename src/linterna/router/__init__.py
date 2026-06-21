"""M2 — Router de modelos con fallback (anti-lock-in).

Única interfaz por la que pasa toda llamada a un LLM. El resto del código depende SOLO
del contrato `LLMClient`, nunca de un SDK de proveedor concreto. Ver
docs/milestone-2-router.md.
"""

from .client import (
    BudgetExceeded,
    LLMClient,
    LLMResult,
    Message,
    ProviderUnavailable,
    Task,
)

__all__ = [
    "BudgetExceeded",
    "LLMClient",
    "LLMResult",
    "Message",
    "ProviderUnavailable",
    "Task",
]
