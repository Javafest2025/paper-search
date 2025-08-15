"""
Unpaywall search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class UnpaywallFilter(BaseSearchFilter, DateFilterMixin):
    """
    Unpaywall search filter implementation.

    Unpaywall provides open access PDF status
    and links for scholarly articles.
    """

    @property
    def source_name(self) -> str:
        return "Unpaywall"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication year filter using Unpaywall format"""
        start_year, end_year = self._get_year_range()
        filters["published_date"] = f"[{start_year}-01-01 TO {end_year}-12-31]"

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add journal/publisher filter for Unpaywall"""
        if not domain:
            return

        # Map domains to common journal patterns
        domain_mappings = {
            "Computer Science": "computer science OR computing OR IEEE OR ACM",
            "Biology": "biology OR nature OR cell OR science",
            "Medicine": "medicine OR medical OR health OR clinical",
            "Physics": "physics OR physical review OR nature physics",
            "Chemistry": "chemistry OR chemical OR ACS OR RSC",
            "Mathematics": "mathematics OR mathematical OR math",
            "Engineering": "engineering OR IEEE OR technology",
            "Psychology": "psychology OR psychological OR behavioral",
            "Economics": "economics OR economic OR finance",
            "Environmental Science": "environmental OR ecology OR climate",
        }

        journal_pattern = domain_mappings.get(domain)
        if journal_pattern:
            filters["journal"] = journal_pattern

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add Unpaywall-specific optimizations"""
        # Focus on open access papers
        filters["is_oa"] = True
        # Prefer gold open access
        filters["oa_color"] = "gold"
