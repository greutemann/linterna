"""Tope de búsquedas (la defensa que el proveedor no da, como capa extra).

Brave factura por uso; como en Linterna el control de costos vive en el framework, ponemos
un límite en código: alcanzado el tope del período se lanza ``SearchBudgetExceeded`` ANTES
de llamar al buscador.

NOTA: en serverless (Cloud Run) este contador es **en memoria y por instancia**, así que es
una defensa *best-effort*, no una garantía global. La garantía dura contra la facturación es
el plan de Brave ("Limit monthly spending → Free", que pausa y no cobra).
"""

from __future__ import annotations

from collections.abc import Callable, Hashable
from datetime import date


class SearchBudgetExceeded(Exception):
    """Se alcanzó el tope de búsquedas del período. No se realiza la llamada."""


def month_period() -> str:
    """Clave de período mensual (año-mes), p. ej. '2026-06'."""
    return date.today().strftime("%Y-%m")


class SearchBudget:
    """Cuenta búsquedas del período y corta al alcanzar el máximo.

    `period_of` devuelve la clave del período (por defecto el día); pasá `month_period`
    para un tope mensual. `max_searches` es el tope por período.
    """

    def __init__(
        self,
        max_searches: int,
        *,
        period_of: Callable[[], Hashable] = date.today,
    ) -> None:
        self._max = max_searches
        self._period_of = period_of
        self._period = period_of()
        self._used = 0

    def _roll(self) -> None:
        current = self._period_of()
        if current != self._period:
            self._period = current
            self._used = 0

    def ensure_within_cap(self) -> None:
        self._roll()
        if self._used >= self._max:
            raise SearchBudgetExceeded(
                f"Tope de {self._max} búsquedas del período alcanzado. No se realiza la llamada."
            )

    def charge(self) -> None:
        self._roll()
        self._used += 1

    @property
    def used(self) -> int:
        self._roll()
        return self._used
