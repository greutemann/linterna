"""Caché persistente en disco (JSON). Sobrevive al reinicio del proceso.

Sigue valiendo el invariante 6: solo se guarda la afirmación normalizada (clave) y su
resultado. Nunca identidad del usuario.
"""

from __future__ import annotations

from pathlib import Path

from linterna.archive import ArchiveVerifier, RawReview
from linterna.archive.cache import JsonFileCache
from linterna.types import Light, Source, Verdict, VerificationResult

_RESULT = VerificationResult(
    verdict=Verdict.FALSE,
    light=Light.RED,
    explanation="Chequeado lo calificó como falso.",
    sources=(
        Source(url="https://x.test/a", title="t", publisher="Chequeado", reviewed_at="2024-01-01"),
    ),
)


def test_roundtrip_get_set(tmp_path: Path) -> None:
    cache = JsonFileCache(tmp_path / "cache.json")
    assert cache.get("clave") is None

    cache.set("clave", _RESULT)
    assert cache.get("clave") == _RESULT


def test_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    JsonFileCache(path).set("la tierra es plana", _RESULT)

    # Nueva instancia (simula reinicio del proceso): debe leer lo guardado.
    reloaded = JsonFileCache(path).get("la tierra es plana")
    assert reloaded == _RESULT


def test_only_claim_and_result_persisted_no_pii(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    cache = JsonFileCache(path)
    cache.set("el dolar a 5000", _RESULT)

    raw = path.read_text(encoding="utf-8")
    assert "el dolar a 5000" in raw
    assert "Chequeado" in raw
    # No hay campos de usuario/identidad en el esquema serializado.
    assert "user" not in raw.lower()


def test_integrates_with_verifier_and_survives_restart(tmp_path: Path) -> None:
    claim = "La vacuna contiene microchips"
    source = Source(url="https://x.test/m", title="t", publisher="AFP", reviewed_at=None)

    class CountingProvider:
        def __init__(self) -> None:
            self.calls = 0

        def search(self, _claim: str) -> list[RawReview]:
            self.calls += 1
            return [RawReview(claim, "Falso", source)]

    provider = CountingProvider()
    path = tmp_path / "cache.json"

    ArchiveVerifier(provider=provider, cache=JsonFileCache(path)).verify(claim)
    # Reinicio: nuevo verifier + nueva caché desde el mismo archivo.
    result = ArchiveVerifier(provider=provider, cache=JsonFileCache(path)).verify(claim)

    assert result.verdict is Verdict.FALSE
    assert provider.calls == 1  # la segunda salió de la caché en disco
