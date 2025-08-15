"""
Semantic Scholar search filter implementation
"""

from typing import Dict, Any, Optional

from .base import BaseSearchFilter, DateFilterMixin


class SemanticScholarFilter(BaseSearchFilter, DateFilterMixin):
    """
    Search filter implementation for Semantic Scholar API.

    Semantic Scholar supports:
    - Field of study filtering
    - Year range filtering
    - PDF availability filtering
    - Citation count filtering
    """

    @property
    def source_name(self) -> str:
        return "Semantic Scholar"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Semantic Scholar uses year range format: 'YYYY-YYYY'"""
        self._add_year_range_filter(filters)

    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add field of study filtering for Semantic Scholar"""
        if not domain:
            return  # No domain-specific filtering needed

        domain_lower = domain.lower()

        # Semantic Scholar field of study mapping
        field_mapping = {
            "computer science": "Computer Science",
            "machine learning": "Computer Science",
            "artificial intelligence": "Computer Science",
            "deep learning": "Computer Science",
            "neural networks": "Computer Science",
            "biology": "Biology",
            "medicine": "Medicine",
            "physics": "Physics",
            "chemistry": "Chemistry",
            "mathematics": "Mathematics",
            "engineering": "Engineering",
            "economics": "Economics",
            "psychology": "Psychology",
            "sociology": "Sociology",
            "linguistics": "Linguistics",
            "philosophy": "Philosophy",
        }

        # Find the best matching field
        for key, value in field_mapping.items():
            if key in domain_lower:
                filters["fieldsOfStudy"] = [value]
                break

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add Semantic Scholar specific optimizations"""
        # Prioritize papers with PDFs and citations
        filters["has_pdf"] = True
        filters["min_citation_count"] = 1

    def get_filter_info(self) -> Dict[str, Any]:
        """Get Semantic Scholar filter capabilities"""
        base_info = super().get_filter_info()
        base_info.update(
            {
                "date_format": "year_range",
                "available_optimizations": [
                    "has_pdf",
                    "min_citation_count",
                    "fields_of_study",
                ],
                "supported_fields": [
                    "Computer Science",
                    "Biology",
                    "Medicine",
                    "Physics",
                    "Chemistry",
                    "Mathematics",
                    "Engineering",
                    "Economics",
                    "Psychology",
                    "Sociology",
                    "Linguistics",
                    "Philosophy",
                ],
            }
        )
        return base_info
