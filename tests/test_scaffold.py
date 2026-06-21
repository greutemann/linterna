"""Smoke test del scaffold: el contrato público importa y los tipos existen.

No prueba lógica (todavía no hay). Garantiza que la estructura del paquete carga.
"""

from linterna.router import BudgetExceeded, LLMClient, LLMResult, ProviderUnavailable
from linterna.types import Light, Verdict, VerificationResult


def test_router_contract_imports() -> None:
    assert hasattr(LLMClient, "complete")
    assert issubclass(BudgetExceeded, Exception)
    assert issubclass(ProviderUnavailable, Exception)


def test_abstention_is_a_valid_verdict() -> None:
    # Invariante 4: INSUFICIENTE es una respuesta válida, no una falla.
    assert Verdict.INSUFFICIENT in Verdict
    assert Light.GREY in Light


def test_result_carries_sources() -> None:
    result = VerificationResult(
        verdict=Verdict.INSUFFICIENT,
        light=Light.GREY,
        explanation="Sin fuentes validadas.",
        sources=(),
    )
    assert result.sources == ()
