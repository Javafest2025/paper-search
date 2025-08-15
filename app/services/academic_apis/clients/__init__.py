"""
Academic API client implementations.
"""

from .semantic_scholar_client import SemanticScholarClient
from .pubmed_client import PubMedClient
from .arxiv_client import ArxivClient
from .crossref_client import CrossrefClient
from .openalex_client import OpenAlexClient
from .core_client import COREClient
from .unpaywall_client import UnpaywallClient
from .europepmc_client import EuropePMCClient
from .dblp_client import DBLPClient
from .biorxiv_client import BioRxivClient
from .doaj_client import DOAJClient
from .base_search_client import BASESearchClient

__all__ = [
    "SemanticScholarClient",
    "PubMedClient",
    "ArxivClient",
    "CrossrefClient",
    "OpenAlexClient",
    "COREClient",
    "UnpaywallClient",
    "EuropePMCClient",
    "DBLPClient",
    "BioRxivClient",
    "DOAJClient",
    "BASESearchClient",
]
