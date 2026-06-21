"""Smoke test manual contra la API real de Google Fact Check Tools.

Lee la key de la variable de entorno GOOGLE_FACTCHECK_API_KEY (no la pidas por chat
ni la pongas en código). Uso:

    python scripts/smoke_factcheck.py "La afirmación a verificar"

No es un test automatizado: es una verificación end-to-end manual con red real.
"""

from __future__ import annotations

import sys

from linterna.archive import ArchiveVerifier
from linterna.archive.cache import InMemoryCache
from linterna.archive.google_factcheck import GoogleFactCheckProvider
from linterna.config import google_factcheck_api_key


def main(argv: list[str]) -> int:
    claim = " ".join(argv[1:]).strip() or "La vacuna contra el COVID contiene microchips"

    provider = GoogleFactCheckProvider(api_key=google_factcheck_api_key())
    verifier = ArchiveVerifier(provider=provider, cache=InMemoryCache())

    print(f"Afirmación: {claim}\n")
    result = verifier.verify(claim)

    print(f"Veredicto:  {result.verdict.value}  [{result.light.value}]")
    print(f"Explicación: {result.explanation}\n")
    if result.sources:
        print("Fuentes:")
        for s in result.sources:
            fecha = f" — {s.reviewed_at}" if s.reviewed_at else ""
            print(f"  - [{s.publisher}] {s.title}{fecha}")
            print(f"    {s.url}")
    else:
        print("(sin fuentes — abstención)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
