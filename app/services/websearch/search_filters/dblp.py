"""
DBLP search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class DBLPFilter(BaseSearchFilter, DateFilterMixin):
    """
    DBLP search filter implementation.

    DBLP is a computer science bibliography with
    comprehensive publication data.
    """

    @property
    def source_name(self) -> str:
        return "DBLP"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication year filter using DBLP format"""
        start_year, end_year = self._get_year_range()
        filters["year"] = f"{start_year}:{end_year}"

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add venue/type filter for DBLP"""
        if not domain:
            return

        # DBLP is primarily computer science, so map to venue types
        domain_mappings = {
            "Computer Science": "conf",  # conferences
            "Machine Learning": "conf",
            "Artificial Intelligence": "conf",
            "Software Engineering": "conf",
            "Database Systems": "conf",
            "Human-Computer Interaction": "conf",
            "Computer Networks": "conf",
            "Information Systems": "journals",
        }

        venue_type = domain_mappings.get(domain)
        if venue_type:
            filters["type"] = venue_type

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add DBLP-specific optimizations"""
        # Sort by year (newest first)
        filters["sort"] = "year"
        # Include only complete publication records
        filters["complete"] = "1"
