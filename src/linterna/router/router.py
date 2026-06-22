"""Implementación del contrato ``LLMClient`` sobre LiteLLM (M2).

El resto del código depende solo de ``LLMClient``; nunca importa litellm directo
(invariantes 1 y 7). LiteLLM se importa de forma perezosa: los tests inyectan un
``completion_fn`` falso y no necesitan la librería ni red.

Recordatorio de frontera (invariante 2): que el modelo responda NO convierte su salida
en evidencia. El texto devuelto debe pasar luego por validación de citas (M1/M3).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .budget import BudgetTracker
from .client import LLMResult, Message, ProviderUnavailable, Task
from .config import RouterConfig

logger = logging.getLogger("linterna.router")

# completion_fn: recibe model/messages/max_tokens/timeout y devuelve una respuesta
# estilo litellm (con .choices[0].message.content y .usage.total_tokens).
CompletionFn = Callable[..., Any]
CostFn = Callable[[Any], float]

# Códigos HTTP transitorios: vale la pena reintentar el mismo modelo. El resto (4xx
# como 401/400) es fatal — reintentar no ayuda, mejor pasar directo al fallback.
_RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status in _RETRYABLE_STATUS
    # Sin código y sin tipo conocido: tratamos como transitorio (conservador).
    return True


def _default_completion(**kwargs: Any) -> Any:
    import litellm  # import perezoso: solo si se usa el proveedor real

    return litellm.completion(**kwargs)


def _default_cost(response: Any) -> float:
    import litellm

    cost: float = litellm.completion_cost(completion_response=response)
    return cost


class RouterClient:
    """Router con fallback, ruteo por tarea, presupuesto, timeout y reintentos acotados."""

    def __init__(
        self,
        config: RouterConfig,
        *,
        completion_fn: CompletionFn | None = None,
        cost_fn: CostFn | None = None,
        budget: BudgetTracker | None = None,
    ) -> None:
        self._config = config
        self._completion = completion_fn or _default_completion
        self._cost = cost_fn or _default_cost
        self._budget = budget or BudgetTracker(config.daily_usd_hard_cap)

    def complete(
        self,
        task: Task,
        messages: list[Message],
        *,
        max_tokens: int,
    ) -> LLMResult:
        # Corte duro de presupuesto ANTES de cualquier llamada.
        self._budget.ensure_within_cap()

        chain = self._config.chain_for(task)
        payload = [{"role": m.role, "content": m.content} for m in messages]
        last_error: Exception | None = None

        for model in chain:
            try:
                response = self._call_with_retries(model, payload, max_tokens)
            except Exception as exc:  # noqa: BLE001 (cualquier fallo -> probar el siguiente)
                last_error = exc
                logger.warning(
                    "modelo falló, intentando fallback", extra={"model": model, "task": task}
                )
                continue

            cost = self._cost(response)
            self._budget.add(cost)
            tokens = int(getattr(response.usage, "total_tokens", 0))
            # Log SIN PII: solo metadata, jamás el contenido de los mensajes (invariante 6).
            logger.info(
                "llamada resuelta",
                extra={"task": task, "model": model, "tokens": tokens, "cost_usd": cost},
            )
            return LLMResult(
                text=response.choices[0].message.content,
                effective_model=model,
                tokens=tokens,
                estimated_cost_usd=cost,
            )

        raise ProviderUnavailable(
            f"Todos los modelos de la cadena fallaron para la tarea {task!r}."
        ) from last_error

    def _call_with_retries(
        self, model: str, payload: list[dict[str, str]], max_tokens: int
    ) -> Any:
        attempts = self._config.limits.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return self._completion(
                    model=model,
                    messages=payload,
                    max_tokens=max_tokens,
                    timeout=self._config.limits.request_timeout_s,
                )
            except Exception as exc:  # noqa: BLE001 (clasificamos abajo)
                last_error = exc
                # Error fatal: no insistir en este modelo, pasar al fallback ya.
                if not _is_retryable(exc) or attempt == attempts - 1:
                    raise
        assert last_error is not None  # pragma: no cover
        raise last_error  # pragma: no cover
