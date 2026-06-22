"""Control de presupuesto con corte duro (invariante operativo de M2).

Superado el tope diario se lanza ``BudgetExceeded`` ANTES de llamar al proveedor:
el gasto queda acotado siempre. El conteo se resetea por día.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .client import BudgetExceeded


class BudgetTracker:
    """Lleva el gasto del día y corta duro al alcanzar el tope."""

    def __init__(self, daily_cap_usd: float, *, today: Callable[[], date] = date.today) -> None:
        self._cap = daily_cap_usd
        self._today = today
        self._day = today()
        self._spent = 0.0

    def _roll_day(self) -> None:
        current = self._today()
        if current != self._day:
            self._day = current
            self._spent = 0.0

    def ensure_within_cap(self) -> None:
        """Lanza ``BudgetExceeded`` si ya se alcanzó el tope. No realiza la llamada."""
        self._roll_day()
        if self._spent >= self._cap:
            raise BudgetExceeded(
                f"Tope diario de US${self._cap:.2f} alcanzado (gastado US${self._spent:.4f}). "
                "No se realiza la llamada."
            )

    def add(self, cost_usd: float) -> None:
        self._roll_day()
        self._spent += cost_usd

    @property
    def spent_today(self) -> float:
        self._roll_day()
        return self._spent
