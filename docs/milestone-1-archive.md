# Milestone 1 — Núcleo "archivo-primero" (sin LLM)

> Primer milestone de la hoja de ruta. **No usa ningún LLM.** Hace cumplir los
> invariantes 3 (validación determinística), 4 (abstención forzada) y 6 (privacidad).

## Objetivo

Resolver verificaciones consultando primero el archivo de verificaciones humanas previas,
sin razonamiento generativo. La mayoría de las falsedades se reciclan: muchas se resuelven acá.

## Alcance

**Incluye:**
- Cliente de **Google Fact Check Tools / ClaimReview** para buscar verificaciones previas.
- **Caché** local de afirmaciones consultadas (sin PII — invariante 6).
- **Validación determinística de citas**: toda fuente devuelta debe ser real y recuperada.
- **Abstención forzada**: sin fuentes validadas → `INSUFICIENTE`, nunca un veredicto inventado.
- Salida `(veredicto, semáforo, explicación, fuentes)`.

**No incluye:** router de modelos (M2), agente investigador (M3), UX (M4).

## Criterios de éxito (tests primero)

1. **Hit de archivo.** Una afirmación con ClaimReview previo devuelve su veredicto y fuentes.
2. **Miss → abstención.** Sin verificación previa, el resultado es `INSUFICIENTE` (no se inventa).
3. **Cita inventada = rechazada.** Una fuente que no fue recuperada nunca llega a la salida.
4. **Caché.** Una segunda consulta idéntica no vuelve a pegarle a la API.
5. **Sin PII.** Lo persistido es la afirmación y su caché, jamás identidad del usuario.

## Pendiente de decidir

- Esquema y backend de la caché (archivo plano vs SQLite).
- Política de expiración / *staleness* de verificaciones cacheadas.
