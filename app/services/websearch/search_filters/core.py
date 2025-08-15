"""
CORE search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class COREFilter(BaseSearchFilter, DateFilterMixin):
    """
    CORE search filter implementation.

    CORE is an open access research aggregator
    providing access to millions of research papers.
    """

    @property
    def source_name(self) -> str:
        return "CORE"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication year filter using CORE format"""
        start_year, end_year = self._get_year_range()
        filters["year"] = [start_year, end_year]

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add subject filter for CORE"""
        if not domain:
            return

        # Map domains to CORE subject areas
        domain_mappings = {
            "Computer Science": "Computer Science",
            "Biology": "Biology",
            "Medicine": "Medicine",
            "Physics": "Physics",
            "Chemistry": "Chemistry",
            "Mathematics": "Mathematics",
            "Engineering": "Engineering",
            "Psychology": "Psychology",
            "Economics": "Economics",
            "Environmental Science": "Environmental Science",
            "Materials Science": "Materials Science",
            "Business": "Business",
            "Education": "Education",
            "History": "History",
            "Philosophy": "Philosophy",
        }

        subject = domain_mappings.get(domain)
        if subject:
            filters["subject"] = subject

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add CORE-specific optimizations"""
        # Sort by relevance
        filters["sort"] = "relevance"
        # Include only full text papers
        filters["fulltext"] = True
