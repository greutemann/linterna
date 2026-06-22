# Milestone 3 — Agente investigador (RAG sobre evidencia fresca)

> Combina M1 (archivo-primero) y M2 (router). Cuando el archivo se abstiene, el agente
> recupera evidencia fresca y deja que un LLM **razone solo sobre esa evidencia**, con
> validación estricta de citas. Hace cumplir los invariantes 2, 3 y 4.

## Objetivo

Resolver afirmaciones que **no** tienen verificación humana previa, sin que el modelo
aporte hechos de su entrenamiento: recupera evidencia, razona sobre ella, y cada cita se
valida contra lo efectivamente recuperado. Si nada valida, se abstiene.

## Frontera determinística (lo no negociable)

- El modelo razona **solo** sobre la evidencia recuperada (invariante 2). El prompt no le
  pide "lo que sabe": le da la evidencia y le prohíbe salirse de ella.
- **Código** valida que cada cita apunte a una pieza de evidencia recuperada (invariante 3),
  reusando `assert_all_recovered`. Cita inventada → no hay veredicto, se abstiene.
- Sin evidencia, o sin citas válidas, o respuesta no parseable → `INSUFICIENTE` (invariante 4).

## Alcance

**Incluye:** el contrato `EvidenceRetriever` (inyectable), el orquestador `InvestigatorAgent`
(recupera → arma prompt → llama al router → parsea → valida citas → veredicto/abstención),
y el `LinternaPipeline` que encadena archivo-primero (M1) y el agente (M3).

**No incluye:** un adaptador concreto de búsqueda (Tavily/Brave/curado) — se enchufa
después sin tocar la lógica. Tampoco la UX (M4).

## Contrato de evidencia (orientativo)

```python
@dataclass(frozen=True)
class Evidence:
    id: str          # identificador estable para que el modelo lo cite
    url: str
    title: str
    publisher: str
    snippet: str     # texto recuperado sobre el que se razona

class EvidenceRetriever(Protocol):
    def retrieve(self, claim: str) -> list[Evidence]: ...
```

El modelo responde estructurado (JSON): `{verdict, explanation, cited_source_ids}`. El
código mapea `cited_source_ids` a la evidencia recuperada y valida.

## Criterios de éxito (tests primero)

1. **Sin evidencia → abstención.** `retrieve` vacío → `INSUFICIENTE`, sin llamar al LLM.
2. **Evidencia + cita válida → veredicto.** El modelo cita evidencia recuperada → veredicto
   con esas fuentes.
3. **Cita inventada → rechazada → abstención.** El modelo cita un id no recuperado → no se
   emite veredicto: `INSUFICIENTE`.
4. **Solo evidencia recuperada (invariante 2).** El prompt enviado al modelo contiene la
   evidencia y la instrucción de no salirse de ella.
5. **Respuesta no parseable → abstención.** Salida del modelo sin JSON válido → `INSUFICIENTE`.
6. **Veredicto desconocido → abstención.** Etiqueta de veredicto no reconocida → `INSUFICIENTE`
   (conservador: ante la duda, no se sentencia).
7. **Pipeline integrado.** Hit de archivo → resultado de M1 (no se invoca al agente). Miss de
   archivo → se delega al agente.
