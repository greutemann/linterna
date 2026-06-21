# Milestone 2 — Router de modelos con *fallback*

> Hace cumplir los invariantes **1** (el modelo es commodity intercambiable) y **7**
> (anti-lock-in / portabilidad) de `CLAUDE.md`. Después de M2, cambiar de modelo o de
> proveedor debe ser un cambio de **config**, nunca de lógica.

## Objetivo

Una única interfaz por la que pasa toda llamada a un LLM, con:
- selección de modelo/proveedor por **configuración**,
- **fallback automático** ante caída o error de un proveedor,
- **ruteo por tarea** (modelo barato para extracción de *claims*; modelo más capaz para síntesis),
- **tope de presupuesto con corte duro**,
- *timeouts*, reintentos acotados y observabilidad **sin PII**.

## Alcance

**Incluye:** la capa de abstracción, configuración, fallback, ruteo por tarea, control de
presupuesto, logging sin PII, y una interfaz estable que el resto del código consume.

**No incluye** (otros milestones): el agente investigador (M3), la UX (M4), ni la lógica
de verificación en sí. M2 entrega *cómo se habla con cualquier modelo*, no *qué se le pide*.

> **Simplicidad primero:** no construir un sistema de plugins propio. Apoyarse en una
> librería de router existente y exponer una interfaz mínima por encima. Nada especulativo.

## Frontera determinística

El router es **infraestructura**, no fuente de verdad. No relaja el invariante 2: que el
modelo "responda" no significa que su respuesta sea evidencia. El contrato de la interfaz
deja explícito que la salida del LLM debe pasar luego por validación de citas (M1/M3).

## Contrato de interfaz (orientativo)

```python
# El resto del código depende SOLO de esto. Nunca de un SDK de proveedor concreto.
class LLMClient(Protocol):
    def complete(
        self,
        task: Literal["claim_extraction", "synthesis"],
        messages: list[Message],
        *,
        max_tokens: int,
    ) -> LLMResult: ...
    # LLMResult incluye: texto, modelo_efectivo_usado, tokens, costo_estimado.
    # Lanza BudgetExceeded (corte duro) y ProviderUnavailable (tras agotar fallbacks).
```

## Configuración (ejemplo, no normativo)

```yaml
budget:
  daily_usd_hard_cap: 5.00        # supera esto -> BudgetExceeded, sin excepción
routing:
  claim_extraction:
    primary: groq/llama-3.x        # barato/rápido
    fallback: [together/llama-3.x, openrouter/auto]
  synthesis:
    primary: <modelo capaz>
    fallback: [<alternativa open-weight>, <alternativa cerrada>]
limits:
  request_timeout_s: 30
  max_retries: 2
observability:
  log_pii: false                   # invariante: jamás texto identificable del usuario
```

## Criterios de éxito (escribir los tests PRIMERO y hacerlos pasar)

1. **Swap por config.** Cambiar el modelo primario en el YAML y obtener otra respuesta
   **sin tocar código**. → test que falla si hace falta editar `.py` para cambiar de modelo.
2. **Fallback automático.** Con el primario *mockeado* como caído, la request igual se
   resuelve por el siguiente de la cadena. → test con proveedor que lanza error.
3. **Corte duro de presupuesto.** Superado el tope diario, se lanza `BudgetExceeded` y
   **no** se hace la llamada. Gasto acotado siempre. → test que simula tope alcanzado.
4. **Ruteo por tarea.** `claim_extraction` usa el tier barato configurado; `synthesis`
   el configurado. → test que verifica el modelo efectivo por tipo de tarea.
5. **Sin PII en logs.** Ningún log contiene el texto identificable del usuario.
   → test que escanea la salida de logging.
6. **Timeout/reintentos acotados.** Una llamada colgada corta a los N s; los reintentos
   no exceden el máximo. → test con proveedor lento *mockeado*.

## Tradeoffs a decidir (no los resuelvo en silencio)

- **Router self-hosted vs meta-proveedor.** Un proxy propio (p. ej. LiteLLM corriendo en
  tu VPS) es **más auditable** y evita un intermediario, alineado con "público y
  auditable" — a cambio de operarlo vos. Un meta-proveedor (p. ej. OpenRouter) es más
  cómodo pero agrega un tercero a la cadena de confianza. **Para un servicio que se
  promete auditable, me inclinaría por el proxy propio**, pero la decisión es tuya.
- **SDK in-process vs proxy como servicio.** In-process es más simple para un MVP; el
  proxy separado facilita límites de presupuesto y observabilidad centralizados. Empezar
  in-process y migrar si hace falta es defendible (no sobre-construir antes de tiempo).
- **Default open-weight vs cerrado para síntesis.** Open-weight maximiza portabilidad
  (mañana auto-hosteable); un cerrado puede dar mejor calidad hoy. La capa permite
  cambiar, así que no es una decisión irreversible — pero conviene fijar el default.

## Antes de codear (recordatorio del principio 1)

Listar supuestos, elegir el tradeoff del proxy, y declarar el plan paso-a-paso con su
verificación. Si algo del contrato no cierra con M1, frenar y avisar.
