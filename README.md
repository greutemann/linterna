# Linterna *(nombre provisorio)*

> Una linterna sobre el ruido. Servicio público, **open-source** y **sin fines de
> lucro** que acerca la fuente verificada al lugar donde la gente lee, y la ayuda a
> formar criterio propio. **No es un oráculo.** Cuando no sabe, lo dice.

**Estado:** etapa temprana / en construcción. Nada de lo acá descrito debe asumirse
estable todavía.

---

## Qué es y qué no es

**Es** una capa universal y transparente de acceso a la verificación: ante una
afirmación, busca primero qué ya verificaron periodistas y organizaciones humanas,
muestra la evidencia con sus fuentes, y deja que la persona concluya.

**No es** un juez que sentencia "verdad/mentira" sobre cualquier tema del mundo. En lo
disputado no falla: muestra los lados con sus fuentes. Donde no hay evidencia
suficiente, se abstiene — y eso es una respuesta válida, no una falla.

---

## Cómo funciona (en una pasada)

1. **Archivo primero.** Consulta verificaciones humanas previas (Google Fact Check /
   ClaimReview) y caché. La mayoría de las falsedades se reciclan: muchas se resuelven acá.
2. **Recuperación de evidencia.** Si no hay verificación previa, recupera evidencia de
   fuentes confiables y oficiales (no del "conocimiento" del modelo).
3. **Razonamiento sobre evidencia.** Un modelo de lenguaje redacta y razona **solo**
   sobre la evidencia recuperada. No aporta hechos de su entrenamiento.
4. **Validación determinística.** Código —no el modelo— verifica que cada afirmación
   apunte a una fuente real y recuperada. Cita inventada = rechazada.
5. **Salida.** `(veredicto, semáforo, explicación, fuentes)` — o `INSUFICIENTE` si no
   hay fuentes validadas.

> La confianza vive en el framework, no en el modelo. El modelo es intercambiable;
> las garantías de fuentes son código de este repositorio.

---

## Principios y garantías

Los invariantes de diseño (innegociables) viven en [`CLAUDE.md`](./CLAUDE.md). En resumen:

- El modelo es un commodity intercambiable; la verdad la garantiza el pipeline.
- Cero conocimiento paramétrico como fuente: se cita evidencia recuperada o se abstiene.
- La validación de citas es código determinístico.
- Evidencia antes que veredicto: la herramienta cultiva criterio, no lo reemplaza.
- Neutralidad por transparencia: separar hecho de interpretación; mostrar los lados.
- Anti-lock-in: capa de abstracción de modelos; preferencia por modelos *open-weight*.

---

## Transparencia y auditabilidad

- **Código abierto** de punta a punta. El método es el activo, y es público.
- Cada verificación expone **sus fuentes** y la fecha de revisión.
- El razonamiento y las reglas (prompts, validadores, fuentes curadas) están en el repo
  y bajo control de versiones.

## Política de correcciones

Este proyecto comete errores y los corrige a la vista de todos.

- Cualquier persona puede reportar un error de verificación abriendo un *issue* con la
  etiqueta `correccion`.
- Las correcciones se registran públicamente (qué se corrigió, cuándo y por qué).
- *(Requisito, además, para ser elegible como publicador en Google ClaimReview.)*

## Privacidad

- No se persisten datos personales de quien consulta.
- Se almacena la afirmación a verificar y su caché; **no** se asocia a identidad.

---

## Cómo se sostiene (sin fines de lucro)

Modelo **open-core**: la capa pública es y será gratuita. Se cross-subsidia con:

- **Capa institucional (B2G / B2Edu):** organismos electorales, educativos,
  universidades y bibliotecas que licencian despliegue + soporte.
- **Producto de criterio crítico:** currícula y capacitación en alfabetización mediática
  (el diferencial del proyecto).
- **Inteligencia de tendencias ética:** *insights* agregados y anonimizados — nunca datos
  de usuarios.
- **Grants catalíticos como puente, no como cimiento.**

**Regla de neutralidad innegociable:** las fuentes de financiamiento se **diversifican y
se publican**. Ningún financiador puede condicionar qué se verifica.

---

## Hoja de ruta

- [ ] **M1 — Núcleo "archivo-primero"** (sin LLM): ClaimReview + caché + validación de
      citas + abstención forzada.
- [ ] **M2 — Router de modelos con fallback** (anti-lock-in). Ver `docs/milestone-2-router.md`.
- [ ] **M3 — Agente investigador** (RAG sobre evidencia fresca, con validación estricta).
- [ ] **M4 — UX socrática** (gesto contextual + modo "mostrame las fuentes y dejame pensar").

---

## Contribuir

Aún no hay guía formal; por ahora, *issues* y propuestas de diseño son bienvenidos.
Toda contribución debe respetar los invariantes de `CLAUDE.md`.

## Gobernanza *(pendiente de definir)*

Se prevé un consejo asesor de periodistas y verificadores. Documentar antes de cualquier
adopción institucional.

## Licencia

- **Código:** [`AGPL-3.0`](./LICENSE) — mantiene abiertas las derivaciones de un bien
  público, **incluso las ofrecidas como servicio** (quien corra una versión modificada debe
  liberar su código). Coherente con el espíritu del proyecto: el método es público y no se
  puede cerrar.
- **Contenido y datos de verificación:** `CC BY 4.0` (consistente con el ecosistema de fact-checking).
