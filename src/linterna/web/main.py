"""Arranque del servicio web real: arma el pipeline completo y lo sirve.

Construye M1 (archivo) + M3 (agente: Brave + router/Gemini) con las keys del entorno.
Para correr:  python -m linterna.web   (o uvicorn linterna.web.main:app)
"""

from __future__ import annotations

import os
from pathlib import Path

from linterna.archive import ArchiveVerifier
from linterna.archive.cache import JsonFileCache
from linterna.archive.google_factcheck import GoogleFactCheckProvider
from linterna.config import brave_api_key, gemini_api_key, google_factcheck_api_key
from linterna.evidence.brave import BraveRetriever
from linterna.evidence.budget import SearchBudget
from linterna.evidence.cache import EphemeralCachingRetriever
from linterna.evidence.investigator import InvestigatorAgent
from linterna.pipeline import LinternaPipeline
from linterna.router.config import RouterConfig
from linterna.router.router import RouterClient

from .app import create_app

_ROOT = Path(__file__).resolve().parents[3]


def _router_config_path() -> Path:
    return Path(os.environ.get("LINTERNA_ROUTER_CONFIG") or (_ROOT / "config" / "router.yaml"))


def _cache_dir() -> Path:
    # En contenedor (Cloud Run) el FS es efímero/solo /tmp escribible: configurable por env.
    return Path(os.environ.get("LINTERNA_CACHE_DIR") or (_ROOT / ".cache"))


def build_default_pipeline() -> LinternaPipeline:
    """Pipeline real desde config/env. Requiere las keys en el entorno (o api_keys.env)."""
    gemini_api_key()  # asegura GEMINI_API_KEY en el entorno para litellm

    archive = ArchiveVerifier(
        provider=GoogleFactCheckProvider(api_key=google_factcheck_api_key()),
        cache=JsonFileCache(_cache_dir() / "archive.json"),  # solo ClaimReview público
    )
    retriever = EphemeralCachingRetriever(  # caché efímero en memoria (compliance Brave)
        BraveRetriever(api_key=brave_api_key(), budget=SearchBudget(daily_max=200)),
        ttl_s=600,
    )
    router = RouterClient(RouterConfig.from_yaml(_router_config_path()))
    # Cautela asimétrica: el agente puede DESMENTIR (rojo) con fuentes confiables, pero
    # nunca AFIRMA (verde) desde evidencia web; lo no-desmentible cae a fuentes-guía.
    agent = InvestigatorAgent(retriever=retriever, llm=router, synthesize=True)
    return LinternaPipeline(archive=archive, investigator=agent)


def main() -> None:
    import uvicorn

    # PORT/HOST por env: Cloud Run inyecta $PORT y exige escuchar en 0.0.0.0.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(create_app(build_default_pipeline()), host=host, port=port)


if __name__ == "__main__":
    main()
