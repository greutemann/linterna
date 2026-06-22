"""Tope duro de búsquedas (la defensa que el proveedor no da).

Brave factura por uso sin corte de gasto. Como en Linterna la confianza —y el control
de costos— vive en el framework, ponemos el límite en código: pasado el tope diario de
búsquedas se lanza ``SearchBudgetExceeded`` ANTES de llamar al buscador.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date


class SearchBudgetExceeded(Exception):
    """Se alcanzó el tope diario de búsquedas. No se realiza la llamada."""


class SearchBudget:
    """Cuenta búsquedas del día y corta duro al alcanzar el máximo."""

    def __init__(self, daily_max: int, *, today: Callable[[], date] = date.today) -> None:
        self._max = daily_max
        self._today = today
        self._day = today()
        self._used = 0

    def _roll_day(self) -> None:
        current = self._today()
        if current != self._day:
            self._day = current
            self._used = 0

    def ensure_within_cap(self) -> None:
        self._roll_day()
        if self._used >= self._max:
            raise SearchBudgetExceeded(
                f"Tope diario de {self._max} búsquedas alcanzado. No se realiza la llamada."
            )

    def charge(self) -> None:
        self._roll_day()
        self._used += 1

    @property
    def used_today(self) -> int:
        self._roll_day()
        return self._used
