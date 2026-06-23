# Milestone 4 — UX socrática (API web + página mínima)

> Le pone cara al motor (M1–M3) sin traicionar su postura: **mostrar la evidencia y
> devolver la decisión al usuario.** No es un oráculo. Encarna los invariantes 4 y 5 en
> la presentación.

## Objetivo

Exponer el `LinternaPipeline` como **servicio público HTTP** y servir una página que
presenta el resultado *evidencia primero*: las fuentes se muestran siempre; el veredicto
hay que pedirlo ("mostrame las fuentes y dejame pensar"). La abstención (`INSUFICIENTE`)
se presenta con calma como respuesta válida, no como error.

## Alcance

**Incluye:**
- API FastAPI: `POST /api/verify` (afirmación → veredicto/semáforo/explicación/fuentes,
  con `is_abstention`), `GET /` (página).
- Página HTML+JS mínima (sin build step): caja de afirmación, fuentes clickeables primero,
  veredicto detrás de un botón "mostrar lo que concluyen las fuentes".
- Bootstrap (`linterna.web.main`) que arma el pipeline real desde config/env.

**No incluye:** autenticación, persistencia de consultas (invariante 6: cero PII), ni la
extensión de navegador / gesto contextual (queda como evolución futura sobre esta API).

## Postura de diseño (lo que la hace "socrática")

- **Evidencia primero, veredicto a pedido.** El usuario ve las fuentes antes que la
  conclusión; revelar el veredicto es un acto voluntario.
- **El veredicto se enmarca, no se impone:** "esto es lo que concluyen las fuentes citadas;
  la decisión final es tuya".
- **Abstención digna.** Sin evidencia, el mensaje es "y eso es una respuesta válida".

## Criterios de éxito (tests primero)

1. `POST /api/verify` con una afirmación devuelve veredicto, semáforo y fuentes.
2. La abstención se marca explícitamente (`is_abstention: true`, sin fuentes).
3. Afirmación vacía / faltante → 422 (no se procesa basura).
4. `GET /` sirve la página HTML socrática.

## Cómo correr

```
python -m linterna.web        # levanta en http://127.0.0.1:8000
```
Requiere las keys en `api_keys.env` (`GEMINI_API_KEY`, `GOOGLE_FACTCHECK_API_KEY`,
`BRAVE_API_KEY`). Compliance Brave: la evidencia del agente no se persiste a disco.
