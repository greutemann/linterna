"""Smoke test del router (M2) contra Gemini real, vía LiteLLM.

Carga config/router.yaml y la key de api_keys.env (GEMINI_API_KEY → litellm la lee del
entorno). Hace una llamada real por cada tarea y muestra modelo efectivo, tokens y costo.
La key nunca se imprime.

Recordatorio (invariante 2): esta salida NO es evidencia. En el pipeline real pasaría
luego por validación de citas (M1/M3). Acá solo probamos la infraestructura del router.

Uso:  python scripts/smoke_router.py
"""

from __future__ import annotations

from pathlib import Path

from linterna.config import gemini_api_key
from linterna.router import Message
from linterna.router.config import RouterConfig
from linterna.router.router import RouterClient

_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    # Asegura GEMINI_API_KEY en el entorno (litellm la toma de ahí).
    gemini_api_key()

    config = RouterConfig.from_yaml(_ROOT / "config" / "router.yaml")
    client = RouterClient(config)

    for task in ("claim_extraction", "synthesis"):
        messages = [
            Message(role="user", content="Respondé solo 'ok' para probar conectividad.")
        ]
        result = client.complete(task, messages, max_tokens=20)  # type: ignore[arg-type]
        print(f"[{task}]")
        print(f"  modelo efectivo: {result.effective_model}")
        print(f"  tokens: {result.tokens}   costo estimado: US${result.estimated_cost_usd:.6f}")
        print(f"  texto: {result.text!r}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
