"""
Europe PMC search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class EuropePMCFilter(BaseSearchFilter, DateFilterMixin):
    """
    Europe PMC search filter implementation.

    Europe PMC provides access to life sciences literature
    with advanced filtering capabilities.
    """

    @property
    def source_name(self) -> str:
        return "Europe PMC"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication date filter using Europe PMC format"""
        start_year, end_year = self._get_year_range()
        filters["sort_date"] = f"{start_year}-01-01 TO {end_year}-12-31"

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add subject/domain filter for Europe PMC"""
        if not domain:
            return

        # Map domains to Europe PMC subject areas
        domain_mappings = {
            "Biology": "Biology",
            "Medicine": "Medicine",
            "Chemistry": "Chemistry",
            "Biochemistry": "Biochemistry",
            "Pharmacology": "Pharmacology",
            "Genetics": "Genetics",
            "Immunology": "Immunology",
            "Neuroscience": "Neuroscience",
            "Cancer Research": "Oncology",
            "Environmental Science": "Environmental Sciences",
        }

        subject = domain_mappings.get(domain)
        if subject:
            filters["SUBJECT"] = subject

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add Europe PMC-specific optimizations"""
        # Include full text when available
        filters["HAS_FT"] = "Y"
        # Sort by relevance
        filters["sort"] = "relevance"
