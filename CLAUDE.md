# CLAUDE.md — Invariantes de diseño de Linterna

> Este archivo es la **fuente de verdad** del proyecto. Todo código, PR y decisión
> debe respetarlo. Los invariantes son **innegociables**: si una tarea parece exigir
> violarlos, hay que frenar y discutirlo, no esquivarlos en silencio.
>
> *(Reconstruido a partir de `README.md` y `docs/milestone-2-router.md`. Si el original
> del proyecto difiere, este archivo se actualiza para coincidir con él.)*

## Qué es Linterna

Una capa universal, pública y auditable de acceso a la verificación de información.
Ante una afirmación: busca primero qué ya verificaron humanos, muestra la evidencia con
sus fuentes, y deja que la persona concluya. **No es un oráculo.** Cuando no sabe, lo dice.

La confianza vive en el **framework**, no en el modelo. El modelo es intercambiable;
las garantías de fuentes son **código de este repositorio**.

---

## Los 7 invariantes

1. **El modelo es un commodity intercambiable.** La verdad la garantiza el *pipeline*,
   no el LLM. Cambiar de modelo o proveedor es un cambio de **config**, nunca de lógica.

2. **Cero conocimiento paramétrico como fuente.** El modelo razona **solo** sobre
   evidencia recuperada; nunca aporta hechos de su entrenamiento. Que el modelo
   "responda" no convierte su respuesta en evidencia.

3. **Validación de citas determinística.** Código —no el modelo— verifica que cada
   afirmación apunte a una fuente real y efectivamente recuperada. **Cita inventada =
   rechazada.**

4. **Evidencia antes que veredicto.** La herramienta cultiva criterio, no lo reemplaza.
   Cuando no hay evidencia suficiente se **abstiene** (`INSUFICIENTE`), y eso es una
   respuesta válida, no una falla.

5. **Neutralidad por transparencia.** Separar hecho de interpretación. En lo disputado
   no se sentencia: se muestran los lados con sus fuentes. El método es público y está
   bajo control de versiones (prompts, validadores, fuentes curadas).

6. **Privacidad y cero PII.** No se persisten datos personales de quien consulta. Se
   almacena la afirmación y su caché, jamás asociadas a identidad. **Ningún log contiene
   texto identificable del usuario.**

7. **Anti-lock-in / portabilidad.** Capa de abstracción de modelos por encima de todo
   SDK de proveedor concreto. Preferencia por modelos *open-weight* y rutas
   auto-hosteables. Ninguna dependencia debe volver irreversible un proveedor.

---

## Frontera determinística (regla operativa)

El borde entre "infraestructura" y "fuente de verdad" es sagrado:

- El **router de modelos** (M2) es infraestructura. No relaja el invariante 2.
- La salida de cualquier LLM **debe** pasar por validación de citas (invariante 3)
  antes de llegar al usuario.
- La abstención forzada es el comportamiento por defecto: sin fuentes validadas, no hay
  veredicto.

## Cómo trabajar en este repo

- **Tests primero.** Cada milestone define sus criterios de éxito como tests que fallan
  antes de implementar y pasan después.
- **Simplicidad primero.** No construir sistemas de plugins propios ni abstracciones
  especulativas. Apoyarse en librerías existentes y exponer interfaces mínimas.
- **Tradeoffs explícitos.** No resolver decisiones de arquitectura en silencio:
  listarlas, recomendar, y dejar la decisión al responsable del proyecto.

## Hoja de ruta

- **M1 — Núcleo "archivo-primero"** (sin LLM): ClaimReview + caché + validación de
  citas + abstención forzada.
- **M2 — Router de modelos con fallback** (anti-lock-in). Ver `docs/milestone-2-router.md`.
- **M3 — Agente investigador** (RAG sobre evidencia fresca, con validación estricta).
- **M4 — UX socrática** (gesto contextual + modo "mostrame las fuentes y dejame pensar").
