"""Reputación de fuentes para el agente (M3).

No alcanza con que una cita sea "real" (invariante 3): para *aportar* sin equivocar, el
agente debe preferir fuentes confiables y descartar las marginales/desinformantes. Esto
es curaduría — pública y versionada, como manda el invariante 5.

Tres niveles por dominio:
- HIGH: instituciones científicas/oficiales, enciclopedias, agencias de fact-checking y
  medios establecidos. Pueden sostener un lean fuerte.
- DENY: fuentes conocidas por desinformación/pseudociencia. Se descartan, no se muestran.
- UNKNOWN: el resto. Se pueden mostrar como contexto, pero NO sostienen por sí solas un
  "respaldado/contradicho" fuerte.

Listas semilla, deliberadamente conservadoras y ampliables por la comunidad.
"""

from __future__ import annotations

import urllib.parse
from enum import Enum


class Tier(str, Enum):
    HIGH = "alta"
    UNKNOWN = "desconocida"
    DENY = "descartada"


# Dominios de alta confianza (semilla). Se compara por sufijo, así cubre subdominios.
_HIGH = (
    # Ciencia / organismos oficiales
    "who.int", "paho.org", "ops.org.ar", "nih.gov", "ncbi.nlm.nih.gov", "cdc.gov",
    "nature.com", "science.org", "thelancet.com", "nejm.org", "bmj.com", "cell.com",
    "pnas.org", "plos.org", "cochrane.org", "europa.eu", "un.org", "unesco.org",
    "oecd.org", "imf.org", "worldbank.org", "ipcc.ch", "nasa.gov", "esa.int",
    "noaa.gov", "usgs.gov", "fda.gov", "ema.europa.eu", "efsa.europa.eu",
    "argentina.gob.ar", "conicet.gov.ar", "ieee.org", "acm.org",
    # Ciencia / academia (bases arbitradas, preprints, agencias de ciencia)
    "scielo.org", "scielo.org.mx", "scielo.org.ar", "scielo.br", "redalyc.org",
    "sciencedirect.com", "link.springer.com", "springer.com", "arxiv.org",
    "agenciasinc.es", "csic.es", "nist.gov", "w3.org", "mit.edu", "stanford.edu",
    "harvard.edu", "ox.ac.uk", "cam.ac.uk", "uba.ar", "unam.mx",
    # Salud / medicina basada en evidencia
    "mayoclinic.org", "clevelandclinic.org", "medlineplus.gov", "hopkinsmedicine.org",
    "nhs.uk", "cancer.gov", "cancer.org", "aecc.es", "seom.org", "healthline.com",
    "medicalnewstoday.com", "uptodate.com", "msdmanuals.com", "kidshealth.org",
    # Enciclopédico / secundario
    "wikipedia.org", "britannica.com",
    # Fact-checking (signatarios IFCN y agencias establecidas)
    "chequeado.com", "maldita.es", "newtral.es", "factcheck.org", "politifact.com",
    "snopes.com", "afp.com", "factual.afp.com", "factcheck.afp.com", "colombiacheck.com",
    "verificat.cat", "fullfact.org", "apnews.com", "reuters.com", "factchequeado.com",
    "leadstories.com", "animalpolitico.com", "grupoanimal.mx", "verificado.com.mx",
    "efe.com", "cotejo.info", "boliviaverifica.bo", "malaespinacheck.cl",
    "lasillavacia.com", "cazadoresdefakenews.info", "africacheck.org",
    "dpa-factchecking.com", "correctiv.org", "science.feedback.org", "sciencefeedback.co",
    "factly.in",
    # Medios establecidos
    "bbc.com", "bbc.co.uk", "nytimes.com", "washingtonpost.com", "theguardian.com",
    "rtve.es", "elpais.com", "lanacion.com.ar", "clarin.com", "dw.com", "npr.org",
    "nationalgeographic.com", "scientificamerican.com",
)

# Dominios descartados (desinformación/pseudociencia conocida).
_DENY = (
    "infowars.com", "naturalnews.com", "mercola.com", "breitbart.com",
    "newspunch.com", "yournewswire.com", "beforeitsnews.com", "globalresearch.ca",
    "davidicke.com", "zerohedge.com", "vaxxedthemovie.com",
)


def _host(url: str) -> str:
    netloc = urllib.parse.urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def _matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def tier_of(url: str) -> Tier:
    host = _host(url)
    if not host or _matches(host, _DENY):
        return Tier.DENY
    if _matches(host, _HIGH):
        return Tier.HIGH
    return Tier.UNKNOWN
