"""
Crossref search filter implementation
"""

from typing import Dict, Any

from .base import BaseSearchFilter, DateFilterMixin


class CrossrefFilter(BaseSearchFilter, DateFilterMixin):
    """
    Search filter implementation for Crossref API.

    Crossref supports:
    - Separate from/until date filtering
    - Type filtering (journal-article, book-chapter, etc.)
    - Publisher filtering
    - Boolean filters (has-abstract, has-full-text, etc.)
    """

    @property
    def source_name(self) -> str:
        return "Crossref"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """Crossref uses separate from-pub-date and until-pub-date parameters"""
        self._add_separate_date_filters(filters)

    def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
        """Add domain-specific filtering for Crossref"""
        if domain:
            domain_lower = domain.lower()

            # Crossref type filtering based on domain
            if any(
                term in domain_lower
                for term in ["computer science", "engineering", "technology"]
            ):
                # Focus on journal articles for technical fields
                filters["type"] = "journal-article"
                filters["has_abstract"] = True

            elif any(
                term in domain_lower
                for term in ["medicine", "biology", "clinical", "health"]
            ):
                # Medical and biological research - focus on peer-reviewed articles
                filters["type"] = "journal-article"
                filters["has_abstract"] = True
                filters["has_full_text"] = True

            elif any(
                term in domain_lower for term in ["physics", "chemistry", "mathematics"]
            ):
                # Physical sciences - include both journal articles and proceedings
                filters["type"] = "journal-article"
                filters["has_abstract"] = True

            elif any(
                term in domain_lower
                for term in ["social", "economics", "psychology", "sociology"]
            ):
                # Social sciences - focus on journal articles and books
                filters["type"] = "journal-article"
                filters["has_abstract"] = True

            else:
                # Default: journal articles with abstracts
                filters["type"] = "journal-article"
                filters["has_abstract"] = True
        else:
            # No domain provided - use default filters
            filters["type"] = "journal-article"
            filters["has_abstract"] = True

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add Crossref specific optimizations"""
        # Use minimal, well-supported filters for better API compatibility
        # Crossref is sensitive to complex filter combinations

        # Only add has-license if not already specified
        if "has_license" not in filters:
            # Don't add has_license by default as it might be too restrictive
            pass

    def get_filter_info(self) -> Dict[str, Any]:
        """Get Crossref filter capabilities"""
        base_info = super().get_filter_info()
        base_info.update(
            {
                "date_format": "separate_date_filters",
                "available_optimizations": [
                    "type_filter",
                    "has_abstract",
                    "has_full_text",
                    "has_license",
                    "publisher_filter",
                ],
                "supported_types": [
                    "journal-article",
                    "book-chapter",
                    "proceedings-article",
                    "monograph",
                    "book",
                    "reference-entry",
                    "report",
                    "dataset",
                ],
                "boolean_filters": [
                    "has-abstract",
                    "has-full-text",
                    "has-license",
                    "has-references",
                    "has-orcid",
                    "has-authenticated-orcid",
                    "has-affiliation",
                ],
                "date_filters": [
                    "from-pub-date",
                    "until-pub-date",
                    "from-online-pub-date",
                    "until-online-pub-date",
                    "from-print-pub-date",
                    "until-print-pub-date",
                ],
            }
        )
        return base_info
