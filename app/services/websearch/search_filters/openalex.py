"""
OpenAlex search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class OpenAlexFilter(BaseSearchFilter, DateFilterMixin):
    """
    OpenAlex search filter implementation.

    OpenAlex is a comprehensive open catalog of scholarly papers
    with rich metadata and filtering capabilities.
    """

    @property
    def source_name(self) -> str:
        return "OpenAlex"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication date filter using OpenAlex format"""
        start_year, end_year = self._get_year_range()
        filters["from_publication_date"] = f"{start_year}-01-01"
        filters["to_publication_date"] = f"{end_year}-12-31"

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add concept/domain filter for OpenAlex"""
        if not domain:
            return

        # Map common domains to OpenAlex concept IDs
        domain_mappings = {
            "Computer Science": "computer-science",
            "Biology": "biology",
            "Medicine": "medicine",
            "Physics": "physics",
            "Chemistry": "chemistry",
            "Mathematics": "mathematics",
            "Engineering": "engineering",
            "Psychology": "psychology",
            "Economics": "economics",
            "Business": "business",
            "Environmental Science": "environmental-science",
            "Materials Science": "materials-science",
            "Social Science": "sociology",
        }

        concept = domain_mappings.get(domain)
        if concept:
            filters["concepts.display_name"] = concept

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add OpenAlex-specific optimizations"""
        # Prefer open access papers when available
        filters["is_oa"] = True
        # Sort by citation count for quality
        filters["sort"] = "cited_by_count:desc"
