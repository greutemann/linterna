# Arquitectura

Linterna se construyó por milestones, cada uno con sus criterios de éxito escritos como
tests que fallan antes y pasan después (*tests primero*).

## Milestones
- **M1 — Núcleo "archivo-primero"** (sin LLM): ClaimReview / Google Fact Check + caché +
  validación determinística de citas + abstención forzada + control de similitud de afirmación.
- **M2 — Router de modelos con fallback** (anti-lock-in): una única interfaz `LLMClient` por
  la que pasa toda llamada a un LLM, con ruteo por tarea, fallback, tope de presupuesto,
  timeouts/reintentos y logging sin PII. Hoy: LiteLLM in-process con Gemini.
- **M3 — Agente investigador**: recuperación de evidencia (Brave Search), razonamiento sobre
  esa evidencia con validación estricta de citas y **cautela asimétrica** (ver
  [[Esquema de verificación]]).
- **M4 — UX socrática**: API web (FastAPI) + página que muestra la evidencia primero, y la
  extensión de navegador (gesto contextual).

## Estructura del código (`src/linterna/`)
- `types.py` — vocabulario del dominio (Verdict, Light, Source, VerificationResult).
- `archive/` — M1: `ArchiveVerifier`, proveedor Google Fact Check, caché, similitud.
- `router/` — M2: contrato `LLMClient`, `RouterClient` (LiteLLM), config YAML, presupuesto.
- `evidence/` — M3: `EvidenceRetriever`, `BraveRetriever`, `reliability` (curaduría),
  `investigator` (el agente), caché efímero, tope de búsquedas.
- `validation/` — validación de citas determinística (usada por M1 y M3).
- `web/` — M4: API FastAPI, página socrática, `/privacy`, `/esquema`, rate limiting.
- `pipeline.py` — encadena archivo-primero (M1) y agente (M3).

## Despliegue
- **Web:** contenedor en Google Cloud Run. Keys en Secret Manager (nunca en el repo).
- **Extensión:** Chrome MV3 (`activeTab` + `scripting`, sin permisos de host amplios);
  consume la API.

## Principios de trabajo
- Tests primero. Simplicidad primero (apoyarse en librerías, no reinventar).
- Tradeoffs explícitos: se listan, se recomienda, y decide el responsable del proyecto.

Ver también: [[Invariantes]] · [[Esquema de verificación]]
