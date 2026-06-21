"""Tipos compartidos del dominio.

Stubs de scaffold: definen el vocabulario común. La lógica vive en cada milestone.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    """Veredicto de una verificación. INSUFICIENTE es una respuesta válida (invariante 4)."""

    TRUE = "verdadero"
    FALSE = "falso"
    MISLEADING = "enganoso"
    DISPUTED = "disputado"
    INSUFFICIENT = "insuficiente"  # abstención forzada: sin fuentes validadas, no hay veredicto


class Light(str, Enum):
    """Semáforo visual asociado al veredicto."""

    GREEN = "verde"
    YELLOW = "amarillo"
    RED = "rojo"
    GREY = "gris"  # abstención


@dataclass(frozen=True)
class Source:
    """Una fuente recuperada. Toda cita debe apuntar a una de estas (invariante 3)."""

    url: str
    title: str
    publisher: str
    reviewed_at: str | None = None  # fecha de revisión, ISO-8601


@dataclass(frozen=True)
class VerificationResult:
    """Salida del pipeline: (veredicto, semáforo, explicación, fuentes)."""

    verdict: Verdict
    light: Light
    explanation: str
    sources: tuple[Source, ...]
