"""Validación de citas determinística (invariante 3).

Código —no el modelo— verifica que cada afirmación apunte a una fuente real y
efectivamente recuperada. Cita inventada = rechazada.
"""

from __future__ import annotations

from collections.abc import Iterable

from linterna.types import Source


class FabricatedCitation(Exception):
    """Se citó una fuente que no estaba en el conjunto recuperado. Rechazo duro."""


def assert_all_recovered(
    cited: Iterable[Source],
    recovered: Iterable[Source],
) -> tuple[Source, ...]:
    """Garantiza que toda fuente citada fue efectivamente recuperada.

    Devuelve las fuentes citadas si todas son legítimas; lanza ``FabricatedCitation``
    ante la primera que no pertenezca al conjunto recuperado. No "limpia" en silencio:
    una cita inventada es un error, no algo a tolerar.
    """
    recovered_set = set(recovered)
    cited_tuple = tuple(cited)
    for source in cited_tuple:
        if source not in recovered_set:
            raise FabricatedCitation(
                f"Fuente no recuperada citada en la salida: {source.url!r}"
            )
    return cited_tuple


__all__ = ["FabricatedCitation", "assert_all_recovered"]
