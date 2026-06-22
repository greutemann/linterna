"""Chequeo mínimo de conectividad con la API de Gemini (Generative Language API).

NO es parte de M2 todavía: solo valida que la key cargada en api_keys.env funcione y
lista los modelos disponibles. La key se lee del entorno y jamás se imprime.

Uso:  python scripts/smoke_gemini.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from linterna.config import gemini_api_key

_BASE = "https://generativelanguage.googleapis.com/v1beta"


def main() -> int:
    key = gemini_api_key()
    url = f"{_BASE}/models?{urllib.parse.urlencode({'key': key})}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 (URL fija)
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        # Nunca imprimimos la URL (lleva la key); solo el código y el cuerpo del error.
        print(f"ERROR HTTP {e.code}: {body[:500]}")
        return 1

    models = [m.get("name", "?") for m in data.get("models", [])]
    gen = [
        m.get("name", "?")
        for m in data.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    print(f"Key OK. {len(models)} modelos visibles.\n")
    print("Modelos que soportan generateContent (los útiles para síntesis en M2):")
    for name in gen:
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
