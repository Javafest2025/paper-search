"""
Base classes for search filter implementations
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseSearchFilter(ABC):
    """
    Abstract base class for academic source search filters.

    Each academic API has different filter formats and capabilities.
    This base class defines the common interface that all filter
    implementations must follow.
    """

    def __init__(self, recent_years_filter: int = 5):
        self.recent_years_filter = recent_years_filter
        self.current_year = datetime.now().year

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the academic source"""
        pass

    def build_filters(self, domain: str = None, query: str = None) -> Dict[str, Any]:
        """
        Build appropriate filters for this academic source.

        Args:
            domain: Research domain/field for domain-specific filtering
            query: Search query for context-aware filtering

        Returns:
            Dictionary of filters appropriate for the source
        """
        filters = {}

        # Add date filter
        self._add_date_filter(filters)

        # Add domain-specific filters (let implementations handle None)
        self._add_domain_filter(filters, domain)

        # Add source-specific optimizations
        self._add_source_optimizations(filters)

        logger.debug(f"Built filters for {self.source_name}: {filters}")
        return filters

    @abstractmethod
    def _add_date_filter(self, filters: Dict[str, Any]):
        """Add date/year filtering based on source API format"""
        pass

    @abstractmethod
    def _add_domain_filter(self, filters: Dict[str, Any], domain: Optional[str]):
        """Add domain-specific filters based on source capabilities"""
        pass

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """
        Add source-specific optimizations for better results.
        Default implementation does nothing - override in subclasses.
        """
        pass

    def get_filter_info(self) -> Dict[str, Any]:
        """
        Get information about available filters for this source.

        Returns:
            Dictionary with filter capabilities and metadata
        """
        return {
            "source_name": self.source_name,
            "supports_date_filter": True,
            "supports_domain_filter": True,
            "recent_years_filter": self.recent_years_filter,
        }

    def update_recent_years_filter(self, years: int):
        """Update the recent years filter setting"""
        self.recent_years_filter = years
        logger.info(
            f"Updated recent years filter for {self.source_name} to {years} years"
        )


class DateFilterMixin:
    """Mixin providing common date filter implementations"""

    def _get_year_range(self) -> tuple:
        """Get start and end years for filtering"""
        start_year = self.current_year - self.recent_years_filter
        end_year = self.current_year
        return start_year, end_year

    def _add_year_range_filter(self, filters: Dict[str, Any]):
        """Add year range filter in format: 'YYYY-YYYY'"""
        start_year, end_year = self._get_year_range()
        filters["year"] = f"{start_year}-{end_year}"

    def _add_date_range_object_filter(self, filters: Dict[str, Any]):
        """Add date range as object with start/end keys"""
        start_year, end_year = self._get_year_range()
        filters["date_range"] = {"start": str(start_year), "end": str(end_year)}

    def _add_separate_date_filters(self, filters: Dict[str, Any]):
        """Add separate from/until date filters"""
        start_year, end_year = self._get_year_range()
        filters["from_pub_date"] = start_year
        filters["until_pub_date"] = end_year
