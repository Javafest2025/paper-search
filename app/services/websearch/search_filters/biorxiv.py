"""
bioRxiv search filter implementation
"""

from typing import Dict, Any, Optional
from .base import BaseSearchFilter, DateFilterMixin


class BioRxivFilter(BaseSearchFilter, DateFilterMixin):
    """
    bioRxiv search filter implementation.

    bioRxiv hosts preprints in biology and life sciences
    with category-based filtering.
    """

    @property
    def source_name(self) -> str:
        return "bioRxiv"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add publication date filter using bioRxiv format"""
        start_year, end_year = self._get_year_range()
        filters["from_date"] = f"{start_year}-01-01"
        filters["to_date"] = f"{end_year}-12-31"

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add subject category filter for bioRxiv"""
        if not domain:
            return

        # Map domains to bioRxiv subject categories
        domain_mappings = {
            "Biology": "biology",
            "Biochemistry": "biochemistry",
            "Bioinformatics": "bioinformatics",
            "Biophysics": "biophysics",
            "Cell Biology": "cell-biology",
            "Developmental Biology": "developmental-biology",
            "Ecology": "ecology",
            "Evolutionary Biology": "evolutionary-biology",
            "Genetics": "genetics",
            "Genomics": "genomics",
            "Immunology": "immunology",
            "Microbiology": "microbiology",
            "Molecular Biology": "molecular-biology",
            "Neuroscience": "neuroscience",
            "Plant Biology": "plant-biology",
            "Systems Biology": "systems-biology",
        }

        category = domain_mappings.get(domain)
        if category:
            filters["subject"] = category

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add bioRxiv-specific optimizations"""
        # Sort by posted date (newest first)
        filters["sort"] = "date"
        # Include only research articles
        filters["type"] = "research-article"
