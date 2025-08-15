"""
PubMed search filter implementation
"""

from typing import Dict, Any

from .base import BaseSearchFilter, DateFilterMixin


class PubMedFilter(BaseSearchFilter, DateFilterMixin):
    """
    Search filter implementation for PubMed API.

    PubMed supports:
    - Date range object filtering
    - Publication type filtering
    - MeSH term filtering
    - Article type filtering
    """

    @property
    def source_name(self) -> str:
        return "PubMed"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """PubMed uses date range object format"""
        self._add_date_range_object_filter(filters)

    def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
        """Add medical/biological domain filtering for PubMed"""
        if not domain:
            return  # No domain-specific filtering needed

        domain_lower = domain.lower()

        # Medical and biological terms that PubMed specializes in
        medical_terms = [
            "medicine",
            "medical",
            "clinical",
            "health",
            "healthcare",
            "biology",
            "biological",
            "biomedical",
            "biochemistry",
            "pharmacology",
            "pathology",
            "physiology",
            "anatomy",
            "genetics",
            "molecular biology",
            "cell biology",
            "neuroscience",
            "cardiology",
            "oncology",
            "immunology",
        ]

        # Check if domain is medical/biological
        is_medical = any(term in domain_lower for term in medical_terms)

        if is_medical:
            # Add publication type filter for research articles
            filters["publication_types"] = [
                "Journal Article",
                "Clinical Trial",
                "Review",
            ]

            # Add specific filters based on subdomain
            if "clinical" in domain_lower:
                filters["publication_types"].extend(
                    ["Clinical Study", "Randomized Controlled Trial"]
                )

            if "genetics" in domain_lower or "molecular" in domain_lower:
                filters["publication_types"].extend(
                    ["Research Support, N.I.H., Extramural"]
                )

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add PubMed specific optimizations"""
        # Focus on peer-reviewed articles with abstracts
        filters["has_abstract"] = True
        filters["article_types"] = ["research", "review"]

        # Prioritize recent, high-quality research
        filters["publication_status"] = ["published"]

    def get_filter_info(self) -> Dict[str, Any]:
        """Get PubMed filter capabilities"""
        base_info = super().get_filter_info()
        base_info.update(
            {
                "date_format": "date_range_object",
                "available_optimizations": [
                    "has_abstract",
                    "publication_types",
                    "article_types",
                    "publication_status",
                ],
                "supported_domains": [
                    "Medicine",
                    "Biology",
                    "Clinical Research",
                    "Biomedical",
                    "Neuroscience",
                    "Genetics",
                    "Pharmacology",
                    "Pathology",
                ],
                "publication_types": [
                    "Journal Article",
                    "Clinical Trial",
                    "Review",
                    "Clinical Study",
                    "Randomized Controlled Trial",
                ],
            }
        )
        return base_info
