"""Smoke end-to-end del pipeline completo: archivo → agente → Brave → Gemini → validación.

Verifica una afirmación con TODA la máquina real:
  M1 archivo-primero (Google Fact Check) → si se abstiene →
  M3 agente: Brave recupera evidencia → router/Gemini razona → validación de citas.

COMPLIANCE: la evidencia de Brave se usa en vivo y se muestra, NUNCA se persiste.

Uso:  python scripts/smoke_evidence.py "afirmación a verificar"
"""

from __future__ import annotations

import sys
from pathlib import Path

from linterna.archive import ArchiveVerifier
from linterna.archive.cache import InMemoryCache
from linterna.archive.google_factcheck import GoogleFactCheckProvider
from linterna.config import brave_api_key, gemini_api_key, google_factcheck_api_key
from linterna.evidence.brave import BraveRetriever
from linterna.evidence.budget import SearchBudget
from linterna.evidence.investigator import InvestigatorAgent
from linterna.pipeline import LinternaPipeline
from linterna.router.config import RouterConfig
from linterna.router.router import RouterClient

_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    claim = " ".join(argv[1:]).strip() or "Un café por día reduce a la mitad el riesgo de infarto"

    gemini_api_key()  # asegura GEMINI_API_KEY en el entorno para litellm

    archive = ArchiveVerifier(
        provider=GoogleFactCheckProvider(api_key=google_factcheck_api_key()),
        cache=InMemoryCache(),
    )
    retriever = BraveRetriever(
        api_key=brave_api_key(),
        max_results=5,
        budget=SearchBudget(daily_max=20),  # tope duro propio para el smoke
    )
    router = RouterClient(RouterConfig.from_yaml(_ROOT / "config" / "router.yaml"))
    agent = InvestigatorAgent(retriever=retriever, llm=router)
    pipeline = LinternaPipeline(archive=archive, investigator=agent)

    print(f"Afirmación: {claim}\n")
    result = pipeline.verify(claim)

    print(f"Veredicto:  {result.verdict.value}  [{result.light.value}]")
    print(f"Explicación: {result.explanation}\n")
    if result.sources:
        print("Fuentes citadas (validadas contra lo recuperado):")
        for s in result.sources:
            print(f"  - [{s.publisher}] {s.title}")
            print(f"    {s.url}")
    else:
        print("(sin fuentes — abstención)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
