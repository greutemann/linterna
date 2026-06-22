"""Carga de configuración desde el entorno.

Los secretos (API keys) se leen de variables de entorno, nunca del código ni de
archivos versionados (invariantes 6/7). El `.gitignore` bloquea `.env`.
"""

from __future__ import annotations

import os
from pathlib import Path

GOOGLE_FACTCHECK_API_KEY_ENV = "GOOGLE_FACTCHECK_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# Raíz del repo: este archivo está en src/linterna/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Archivos de secretos buscados, en orden. Todos gitignoreados.
_SECRET_FILES = ("api_keys.env", ".env")


def load_dotenv(path: Path | None = None) -> None:
    """Carga pares CLAVE=valor de un archivo de secretos al entorno, sin pisar lo ya seteado.

    Parser mínimo (sin dependencias): ignora líneas vacías y comentarios (#). El archivo
    está gitignoreado; jamás se versiona ni se imprime su contenido.
    """
    candidates = [path] if path is not None else [_PROJECT_ROOT / name for name in _SECRET_FILES]
    for dotenv in candidates:
        if dotenv is None or not dotenv.is_file():
            continue
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _require(env_var: str, hint: str) -> str:
    load_dotenv()
    value = os.environ.get(env_var, "")
    if not value:
        raise RuntimeError(f"Falta la variable de entorno {env_var}. {hint}")
    return value


def google_factcheck_api_key() -> str:
    """Devuelve la API key de Google Fact Check Tools, o falla con un mensaje claro."""
    return _require(
        GOOGLE_FACTCHECK_API_KEY_ENV,
        "Conseguila en https://console.cloud.google.com (habilitá 'Fact Check Tools API').",
    )


def gemini_api_key() -> str:
    """Devuelve la API key de Gemini (Generative Language API). Para M2."""
    return _require(
        GEMINI_API_KEY_ENV,
        "Es la 'Generative Language API Key' en https://aistudio.google.com/apikey.",
    )
