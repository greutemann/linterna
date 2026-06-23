"""Arranque del servicio web real: arma el pipeline completo y lo sirve.

Construye M1 (archivo) + M3 (agente: Brave + router/Gemini) con las keys del entorno.
Para correr:  python -m linterna.web   (o uvicorn linterna.web.main:app)
"""

from __future__ import annotations

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


def build_default_pipeline() -> LinternaPipeline:
    """Pipeline real desde config/env. Requiere las keys en api_keys.env."""
    gemini_api_key()  # asegura GEMINI_API_KEY en el entorno para litellm

    archive = ArchiveVerifier(
        provider=GoogleFactCheckProvider(api_key=google_factcheck_api_key()),
        cache=JsonFileCache(_ROOT / ".cache" / "archive.json"),  # solo ClaimReview público
    )
    retriever = EphemeralCachingRetriever(  # caché efímero en memoria (compliance Brave)
        BraveRetriever(api_key=brave_api_key(), budget=SearchBudget(daily_max=200)),
        ttl_s=600,
    )
    router = RouterClient(RouterConfig.from_yaml(_ROOT / "config" / "router.yaml"))
    agent = InvestigatorAgent(retriever=retriever, llm=router)
    return LinternaPipeline(archive=archive, investigator=agent)


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(build_default_pipeline()), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
