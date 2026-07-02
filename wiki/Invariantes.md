# Los 7 invariantes

Son la **fuente de verdad** del diseño (viven en `CLAUDE.md`). Innegociables: si una tarea
parece exigir violarlos, se frena y se discute, no se esquiva.

1. **El modelo es un commodity intercambiable.** La verdad la garantiza el *pipeline*, no el
   LLM. Cambiar de modelo o proveedor es un cambio de **config**, nunca de lógica.

2. **Cero conocimiento paramétrico como fuente.** El modelo razona **solo** sobre evidencia
   recuperada; nunca aporta hechos de su entrenamiento. Que el modelo "responda" no convierte
   su respuesta en evidencia.

3. **Validación de citas determinística.** Código —no el modelo— verifica que cada afirmación
   apunte a una fuente real y efectivamente recuperada. **Cita inventada = rechazada.**

4. **Evidencia antes que veredicto.** La herramienta cultiva criterio, no lo reemplaza. Sin
   evidencia suficiente se **abstiene** (`INSUFICIENTE`), y eso es una respuesta válida.

5. **Neutralidad por transparencia.** Separar hecho de interpretación. En lo disputado no se
   sentencia: se muestran los lados con sus fuentes. El método es público y versionado.

6. **Privacidad y cero PII.** No se persisten datos personales de quien consulta. Ningún log
   contiene texto identificable ni IPs del usuario.

7. **Anti-lock-in / portabilidad.** Capa de abstracción de modelos por encima de todo SDK
   concreto. Preferencia por modelos *open-weight* y rutas auto-hosteables.

## Consecuencias prácticas
- El **veredicto firme** (verdadero/falso) solo sale del **archivo de verificación humana**.
- El **agente** (evidencia web) puede **desmentir** con fuentes confiables, pero **nunca
  afirma** — ver [[Esquema de verificación]].
- Los secretos (API keys) nunca entran al repo ni a los logs (invariantes 6 y 7).

Ver también: [[Esquema de verificación]] · [[Arquitectura]]
