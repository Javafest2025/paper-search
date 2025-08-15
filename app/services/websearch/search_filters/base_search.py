"""
BASE Search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class BASESearchFilter(BaseSearchFilter, DateFilterMixin):
    """
    BASE Search filter implementation.

    BASE is a European academic search engine providing
    access to scholarly resources.
    """

    @property
    def source_name(self) -> str:
        return "BASE Search"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication date filter using BASE format"""
        start_year, end_year = self._get_year_range()
        filters["from_year"] = start_year
        filters["to_year"] = end_year

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add subject classification filter for BASE"""
        if not domain:
            return

        # Map domains to BASE subject classifications
        domain_mappings = {
            "Computer Science": "004",  # Computer science
            "Mathematics": "510",  # Mathematics
            "Physics": "530",  # Physics
            "Chemistry": "540",  # Chemistry
            "Biology": "570",  # Life sciences
            "Medicine": "610",  # Medicine and health
            "Engineering": "620",  # Engineering
            "Agriculture": "630",  # Agriculture
            "Economics": "330",  # Economics
            "Psychology": "150",  # Psychology
            "Education": "370",  # Education
            "History": "900",  # History and auxiliary sciences
            "Philosophy": "100",  # Philosophy and psychology
            "Religion": "200",  # Religion
            "Social Science": "300",  # Social sciences
        }

        ddc_code = domain_mappings.get(domain)
        if ddc_code:
            filters["ddc"] = ddc_code

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add BASE-specific optimizations"""
        # Prefer open access documents
        filters["oa"] = "1"
        # Sort by relevance
        filters["sort"] = "relevance"
        # Include only documents (not collections)
        filters["type"] = "121"  # Document type
