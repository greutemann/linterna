"""Carga de configuración desde el entorno.

Los secretos (API keys) se leen de variables de entorno, nunca del código ni de
archivos versionados (invariantes 6/7). El `.gitignore` bloquea `.env`.
"""

from __future__ import annotations

import os
from pathlib import Path

GOOGLE_FACTCHECK_API_KEY_ENV = "GOOGLE_FACTCHECK_API_KEY"

# Raíz del repo: este archivo está en src/linterna/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path | None = None) -> None:
    """Carga pares CLAVE=valor de un .env al entorno, sin pisar lo ya seteado.

    Parser mínimo (sin dependencias): ignora líneas vacías y comentarios (#). El .env
    está gitignoreado; jamás se versiona ni se imprime su contenido.
    """
    dotenv = path or (_PROJECT_ROOT / ".env")
    if not dotenv.is_file():
        return
    for line in dotenv.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def google_factcheck_api_key() -> str:
    """Devuelve la API key de Google Fact Check Tools, o falla con un mensaje claro."""
    load_dotenv()
    key = os.environ.get(GOOGLE_FACTCHECK_API_KEY_ENV, "")
    if not key:
        raise RuntimeError(
            f"Falta la variable de entorno {GOOGLE_FACTCHECK_API_KEY_ENV}. "
            "Conseguí una key en https://console.cloud.google.com (habilitá "
            "'Fact Check Tools API') y exportala antes de correr."
        )
    return key
