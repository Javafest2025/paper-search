"""
Search filters for academic sources.
"""

from .base import BaseSearchFilter, DateFilterMixin
from .semantic_scholar import SemanticScholarFilter
from .arxiv import ArxivFilter
from .pubmed import PubMedFilter
from .crossref import CrossrefFilter
from .openalex import OpenAlexFilter
from .core import COREFilter
from .unpaywall import UnpaywallFilter
from .europepmc import EuropePMCFilter
from .dblp import DBLPFilter
from .biorxiv import BioRxivFilter
from .doaj import DOAJFilter
from .base_search import BASESearchFilter


# Filter factory for creating source-specific filters
class FilterFactory:
    """Factory for creating source-specific search filters"""

    # Mapping of source names to filter classes
    _filters = {
        "Semantic Scholar": SemanticScholarFilter,
        "arXiv": ArxivFilter,
        "PubMed": PubMedFilter,
        "Crossref": CrossrefFilter,
        "OpenAlex": OpenAlexFilter,
        "CORE": COREFilter,
        "Unpaywall": UnpaywallFilter,
        "Europe PMC": EuropePMCFilter,
        "DBLP": DBLPFilter,
        "bioRxiv": BioRxivFilter,
        "DOAJ": DOAJFilter,
        "BASE Search": BASESearchFilter,
    }

    @classmethod
    def create_filter(cls, source_name: str) -> BaseSearchFilter:
        """
        Create a filter instance for the specified source.

        Args:
            source_name: Name of the academic source

        Returns:
            Filter instance for the source

        Raises:
            ValueError: If source is not supported
        """
        if source_name not in cls._filters:
            available = ", ".join(cls._filters.keys())
            raise ValueError(
                f"Filter not available for '{source_name}'. Available: {available}"
            )

        filter_class = cls._filters[source_name]
        return filter_class()

    @classmethod
    def get_available_sources(cls) -> list:
        """Get list of sources with available filters"""
        return list(cls._filters.keys())

    @classmethod
    def get_filter_capabilities(cls, source_name: str) -> dict:
        """
        Get filter capabilities for a specific source.

        Args:
            source_name: Name of the academic source

        Returns:
            Dictionary describing filter capabilities
        """
        if source_name not in cls._filters:
            return {}

        filter_instance = cls.create_filter(source_name)
        return filter_instance.get_filter_info()

    @classmethod
    def register_filter(cls, source_name: str, filter_class):
        """
        Register a new filter implementation.

        Args:
            source_name: Name of the academic source
            filter_class: Filter class that extends BaseSearchFilter
        """
        cls._filters[source_name] = filter_class


__all__ = [
    "BaseSearchFilter",
    "DateFilterMixin",
    "SemanticScholarFilter",
    "ArxivFilter",
    "PubMedFilter",
    "CrossrefFilter",
    "OpenAlexFilter",
    "COREFilter",
    "UnpaywallFilter",
    "EuropePMCFilter",
    "DBLPFilter",
    "BioRxivFilter",
    "DOAJFilter",
    "BASESearchFilter",
    "FilterFactory",
]
