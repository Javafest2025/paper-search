"""
Academic APIs module for comprehensive research paper discovery.

This module provides clients for various academic databases and APIs:
- Semantic Scholar: AI-powered semantic search and citation analysis
- arXiv: Physics, mathematics, computer science preprints
- Crossref: DOI metadata and citation information
- PubMed: Biomedical and life sciences literature
- OpenAlex: Open catalog of scholarly papers and metadata
- CORE: Open access research aggregator
- Unpaywall: Open access PDF finder
- Europe PMC: Life sciences literature and full-text access
- DBLP: Computer science bibliography
- bioRxiv/medRxiv: Biology and medical preprint servers
- DOAJ: Directory of Open Access Journals
- Lens: Comprehensive scholarly and patent data
- BASE: European academic search engine

All clients implement a unified interface for searching, retrieving paper details,
and analyzing citation networks.
"""

from .clients import (
    SemanticScholarClient,
    ArxivClient,
    CrossrefClient,
    PubMedClient,
    OpenAlexClient,
    COREClient,
    UnpaywallClient,
    EuropePMCClient,
    DBLPClient,
    BioRxivClient,
    DOAJClient,
    BASESearchClient,
)
from .common import (
    BaseAcademicClient,
    APIError,
    RateLimitError,
)
from pydantic import ValidationError

__all__ = [
    # Client classes
    "SemanticScholarClient",
    "ArxivClient",
    "CrossrefClient",
    "PubMedClient",
    "OpenAlexClient",
    "COREClient",
    "UnpaywallClient",
    "EuropePMCClient",
    "DBLPClient",
    "BioRxivClient",
    "DOAJClient",
    "BASESearchClient",
    # Base classes and exceptions
    "BaseAcademicClient",
    "APIError",
    "RateLimitError",
    "ValidationError",
]

__version__ = "2.0.0"
