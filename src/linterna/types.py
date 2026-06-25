"""Tipos compartidos del dominio.

Distinción central (tras el rediseño de M3):
- El **archivo** (M1) entrega veredictos autoritativos porque un humano verificador los
  emitió (TRUE/FALSE/...). Eso es legítimo.
- El **agente** (M3) NO sentencia. Describe el estado de la evidencia recuperada de fuentes
  confiables (la respalda / la contradice / dividida / insuficiente) con un porcentaje de
  apoyo. Aporta evidencia con sus fuentes; la conclusión es del usuario (invariantes 4 y 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    """Resultado de una verificación.

    Los primeros valores son veredictos de archivo (verificación humana, autoritativos).
    Los `EVIDENCE_*` describen el lean de la evidencia hallada por el agente — NO son un
    veredicto de Linterna, sino un resumen de qué dicen las fuentes confiables.
    """

    # Archivo (verificación humana) — autoritativo
    TRUE = "verdadero"
    FALSE = "falso"
    MISLEADING = "enganoso"
    DISPUTED = "disputado"
    INSUFFICIENT = "insuficiente"  # abstención: sin evidencia validada, no hay respuesta

    # Agente (lean de la evidencia) — NO autoritativo, describe a las fuentes
    EVIDENCE_SUPPORTS = "la_evidencia_respalda"
    EVIDENCE_REFUTES = "la_evidencia_contradice"
    EVIDENCE_MIXED = "evidencia_dividida"


class Light(str, Enum):
    """Color asociado. En el camino-agente representa el lean, no un veredicto."""

    GREEN = "verde"
    YELLOW = "amarillo"
    RED = "rojo"
    GREY = "gris"  # abstención


_LABELS: dict[Verdict, str] = {
    Verdict.TRUE: "Verdadero",
    Verdict.FALSE: "Falso",
    Verdict.MISLEADING: "Engañoso",
    Verdict.DISPUTED: "En disputa",
    Verdict.INSUFFICIENT: "Sin evidencia suficiente",
    Verdict.EVIDENCE_SUPPORTS: "Las fuentes confiables lo respaldan",
    Verdict.EVIDENCE_REFUTES: "Las fuentes confiables lo contradicen",
    Verdict.EVIDENCE_MIXED: "Las fuentes están divididas",
}

_LIGHTS: dict[Verdict, Light] = {
    Verdict.TRUE: Light.GREEN,
    Verdict.FALSE: Light.RED,
    Verdict.MISLEADING: Light.YELLOW,
    Verdict.DISPUTED: Light.YELLOW,
    Verdict.INSUFFICIENT: Light.GREY,
    Verdict.EVIDENCE_SUPPORTS: Light.GREEN,
    Verdict.EVIDENCE_REFUTES: Light.RED,
    Verdict.EVIDENCE_MIXED: Light.YELLOW,
}


def light_for(verdict: Verdict) -> Light:
    """Color canónico para un veredicto/lean. Fuente única para todo el pipeline."""
    return _LIGHTS[verdict]


def label_for(verdict: Verdict) -> str:
    """Texto legible para mostrar al usuario."""
    return _LABELS[verdict]


@dataclass(frozen=True)
class Source:
    """Una fuente recuperada. Toda cita debe apuntar a una de estas (invariante 3)."""

    url: str
    title: str
    publisher: str
    reviewed_at: str | None = None  # fecha de revisión, ISO-8601


@dataclass(frozen=True)
class VerificationResult:
    """Salida del pipeline.

    `kind`: "archivo" (veredicto humano) o "evidencia" (lean del agente).
    `support_pct`: solo en camino-agente — % de la evidencia confiable que respalda la
    afirmación (0–100). En el archivo es None.
    """

    verdict: Verdict
    light: Light
    explanation: str
    sources: tuple[Source, ...]
    kind: str = "archivo"
    support_pct: int | None = None

    @property
    def label(self) -> str:
        return label_for(self.verdict)
