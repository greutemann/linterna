# Milestone 3 — Agente investigador (RAG sobre evidencia fresca)

> Combina M1 (archivo-primero) y M2 (router). Cuando el archivo se abstiene, el agente
> recupera evidencia fresca y deja que un LLM **razone solo sobre esa evidencia**, con
> validación estricta de citas. Hace cumplir los invariantes 2, 3 y 4.

## Objetivo

Resolver afirmaciones que **no** tienen verificación humana previa, sin que el modelo
aporte hechos de su entrenamiento: recupera evidencia, razona sobre ella, y cada cita se
valida contra lo efectivamente recuperado. Si nada valida, se abstiene.

## Rediseño (tras incidente): el agente NO sentencia

Una afirmación dañina/contestada llegó a estamparse como "verdadero" usando fuentes
marginales. Corrección de principios:

- **El agente nunca emite veredictos de verdad (TRUE/FALSE).** Eso queda solo para el
  archivo (M1), donde un humano verificó. El agente describe el **estado de la evidencia**:
  `EVIDENCE_SUPPORTS` / `EVIDENCE_REFUTES` / `EVIDENCE_MIXED`, con un **% de apoyo** y color.
  Es "lo que dicen las fuentes", no un fallo de Linterna.
- **Curaduría de fuentes** (`reliability.py`): se descartan dominios fringe/desinformantes;
  un lean fuerte (respaldado/contradicho) exige al menos una fuente de **alta confiabilidad**,
  si no se degrada a "dividida". Mostrar un blog marginal como evidencia ya es un daño.
- **`temperature = 0`** en la síntesis: fidelidad a la evidencia, menos azar.
- Si no hay evidencia confiable → abstención. El objetivo no es abstenerse siempre, es
  **aportar** evidencia fiel sin tomar partido (invariantes 4 y 5).

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

**No incluye:** la UX (M4).

### Adaptador de evidencia

Se eligió **Brave Search API** por su índice web **propio e independiente** (no un
reempaquetador de terceros), alineado con el invariante 7 y con la tesis de
auditabilidad. Como Brave factura por uso **sin corte de gasto**, el adaptador se envuelve
en un `SearchBudget` con **tope duro en código** (la defensa que el proveedor no da): pasado
el límite diario de búsquedas se lanza `SearchBudgetExceeded` antes de llamar. La key se
lee de `BRAVE_API_KEY` (`api_keys.env`, gitignoreado). Otros retrievers (Tavily, curados)
pueden sumarse bajo el mismo contrato `EvidenceRetriever`.

### Compliance con los términos de Brave

Brave prohíbe almacenar/reutilizar/revender las respuestas de su API (permite inferencia
de IA durante la suscripción). Por eso la evidencia del agente **nunca se persiste a
disco**; la caché persistente es solo para el archivo (ClaimReview público). Como decisión
deliberada del dueño del proyecto, se admite un **caché efímero en memoria con TTL corto**
(`EphemeralCachingRetriever`) para deduplicar búsquedas repetidas en una ventana breve —
un "gris permitible" de footprint mínimo, no un corpus persistente.

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
