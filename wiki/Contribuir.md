# Contribuir

Linterna es un bien público: el método es abierto, auditable y corregible. Toda contribución
debe respetar los [[Invariantes]].

## Reportar un error de verificación
La herramienta comete errores y los corrige a la vista de todos.
- Abrí un *issue* con la etiqueta **`correccion`**, indicando: la afirmación consultada, qué
  devolvió Linterna, y por qué creés que está mal (con fuentes si podés).
- Las correcciones se registran públicamente: qué se corrigió, cuándo y por qué.

## Contribuir código
1. Leé [[Invariantes]] y [[Arquitectura]] — son la fuente de verdad del diseño.
2. **Tests primero:** todo cambio de comportamiento viene con su test.
3. Corré la suite antes de abrir el PR: `pytest`, `ruff check .`, `mypy`.
4. No introduzcas dependencias o cláusulas que vuelvan irreversible un cierre del código
   (invariante 7), ni nada que persista PII (invariante 6).

## Proponer fuentes confiables
Ver [[Fuentes confiables]] — se edita `reliability.py` con justificación.

## Correr el proyecto localmente
```
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
python -m linterna.web        # http://127.0.0.1:8000
```
Requiere API keys en `api_keys.env` (gitignoreado): `GEMINI_API_KEY`,
`GOOGLE_FACTCHECK_API_KEY`, `BRAVE_API_KEY`.

## Licencia
Al contribuir, aceptás que tu aporte se distribuya bajo **AGPL-3.0**.
