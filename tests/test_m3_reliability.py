"""Clasificación de confiabilidad de fuentes (curaduría de M3)."""

from __future__ import annotations

from linterna.evidence.reliability import Tier, tier_of


def test_high_trust_domains() -> None:
    assert tier_of("https://www.who.int/es/dengue") is Tier.HIGH
    assert tier_of("https://es.wikipedia.org/wiki/x") is Tier.HIGH  # subdominio
    assert tier_of("https://chequeado.com/x") is Tier.HIGH


def test_denied_domains() -> None:
    assert tier_of("https://www.infowars.com/x") is Tier.DENY
    assert tier_of("https://naturalnews.com/y") is Tier.DENY


def test_unknown_domains() -> None:
    assert tier_of("https://un-blog-personal.com/post") is Tier.UNKNOWN
    assert tier_of("") is Tier.DENY  # sin host -> descartada (conservador)


def test_www_prefix_is_ignored() -> None:
    assert tier_of("https://www.nature.com/articles/x") is Tier.HIGH


def test_expanded_science_and_academia_domains() -> None:
    assert tier_of("https://www.scielo.org.ar/scielo.php?pid=x") is Tier.HIGH
    assert tier_of("https://arxiv.org/abs/2401.00001") is Tier.HIGH
    assert tier_of("https://www.agenciasinc.es/Noticias/x") is Tier.HIGH
    assert tier_of("https://news.mit.edu/2026/x") is Tier.HIGH
    assert tier_of("https://www.redalyc.org/articulo.oa?id=x") is Tier.HIGH


def test_expanded_ifcn_factcheckers() -> None:
    assert tier_of("https://science.feedback.org/review/x") is Tier.HIGH
    assert tier_of("https://boliviaverifica.bo/x") is Tier.HIGH
    assert tier_of("https://malaespinacheck.cl/x") is Tier.HIGH
    assert tier_of("https://grupoanimal.mx/verificacion-viral/x") is Tier.HIGH
    assert tier_of("https://factcheck.afp.com/x") is Tier.HIGH
