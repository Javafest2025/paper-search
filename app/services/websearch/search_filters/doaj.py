"""
DOAJ search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class DOAJFilter(BaseSearchFilter, DateFilterMixin):
    """
    DOAJ search filter implementation.

    DOAJ (Directory of Open Access Journals) provides
    access to quality open access articles.
    """

    @property
    def source_name(self) -> str:
        return "DOAJ"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication date filter using DOAJ format"""
        start_year, end_year = self._get_year_range()
        filters["from_date"] = f"{start_year}-01-01"
        filters["to_date"] = f"{end_year}-12-31"

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add subject/classification filter for DOAJ"""
        if not domain:
            return

        # Map domains to DOAJ subject classifications
        domain_mappings = {
            "Biology": "Science: Biology",
            "Medicine": "Medicine",
            "Chemistry": "Science: Chemistry",
            "Physics": "Science: Physics",
            "Mathematics": "Science: Mathematics",
            "Computer Science": "Technology: Computer Science",
            "Engineering": "Technology: Engineering",
            "Psychology": "Social Sciences: Psychology",
            "Economics": "Social Sciences: Economics",
            "Environmental Science": "Science: Environmental Sciences",
            "Agriculture": "Agriculture",
            "Education": "Education",
        }

        subject = domain_mappings.get(domain)
        if subject:
            filters["subject"] = subject

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add DOAJ-specific optimizations"""
        # Sort by relevance
        filters["sort"] = "relevance"
        # Include only articles (not journal metadata)
        filters["type"] = "article"
