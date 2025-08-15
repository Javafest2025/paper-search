"""
Search filter service for academic sources (Refactored to use modular implementations)
"""

from datetime import datetime
from typing import Dict, Any
import logging

from .search_filters import FilterFactory, BaseSearchFilter

logger = logging.getLogger(__name__)


class SearchFilterService:
    """
    Service for building domain and source-specific search filters.

    This service now uses modular filter implementations for each academic source,
    providing better maintainability and extensibility while maintaining
    backward compatibility.
    """

    def __init__(self, recent_years_filter: int = 5):
        self.recent_years_filter = recent_years_filter
        self.current_year = datetime.now().year
        self._filter_cache = {}

    def build_filters(
        self, source_name: str, domain: str = None, query: str = None
    ) -> Dict[str, Any]:
        """
        Build appropriate filters for the given academic source.

        Args:
            source_name: Name of the academic source (e.g., "Semantic Scholar", "PubMed")
            domain: Research domain/field for domain-specific filtering
            query: Search query for context-aware filtering

        Returns:
            Dictionary of filters appropriate for the source
        """
        try:
            # Get or create filter instance for this source
            filter_instance = self._get_filter_instance(source_name)

            # Build filters using the specific implementation
            filters = filter_instance.build_filters(domain=domain, query=query)

            logger.debug(f"Built filters for {source_name}: {filters}")
            return filters

        except ValueError as e:
            logger.warning(f"No filter implementation for {source_name}: {e}")
            # Fallback to basic filters
            return self._build_fallback_filters()
        except Exception as e:
            logger.error(f"Error building filters for {source_name}: {e}")
            return self._build_fallback_filters()

    def _get_filter_instance(self, source_name: str) -> BaseSearchFilter:
        """Get or create a filter instance for the given source"""
        if source_name not in self._filter_cache:
            filter_instance = FilterFactory.create_filter(source_name)
            # Set the recent years filter after creation
            filter_instance.recent_years_filter = self.recent_years_filter
            self._filter_cache[source_name] = filter_instance
        return self._filter_cache[source_name]

    def _build_fallback_filters(self) -> Dict[str, Any]:
        """Build basic fallback filters for unknown sources"""
        start_year = self.current_year - self.recent_years_filter
        end_year = self.current_year
        return {"year": f"{start_year}-{end_year}"}

    def get_supported_sources(self) -> list:
        """Get list of academic sources that support filtering"""
        return FilterFactory.get_available_sources()

    def update_recent_years_filter(self, years: int):
        """Update the recent years filter setting for all cached filters"""
        self.recent_years_filter = years

        # Update all cached filter instances
        for filter_instance in self._filter_cache.values():
            filter_instance.update_recent_years_filter(years)

        logger.info(f"Updated recent years filter to {years} years")

    def get_filter_info(self, source_name: str) -> Dict[str, Any]:
        """
        Get information about available filters for a source.

        Args:
            source_name: Name of the academic source

        Returns:
            Dictionary with filter capabilities and metadata
        """
        try:
            filter_instance = self._get_filter_instance(source_name)
            return filter_instance.get_filter_info()
        except ValueError:
            return {
                "source_name": source_name,
                "supported": False,
                "error": "No filter implementation available",
            }

    def clear_cache(self):
        """Clear the filter instance cache"""
        self._filter_cache.clear()
        logger.debug("Filter instance cache cleared")

    def register_custom_filter(self, source_name: str, filter_class):
        """
        Register a custom filter implementation.

        Args:
            source_name: Name of the academic source
            filter_class: Filter class that extends BaseSearchFilter
        """
        FilterFactory.register_filter(source_name, filter_class)
        # Clear cache to ensure new filter is used
        if source_name in self._filter_cache:
            del self._filter_cache[source_name]
        logger.info(f"Registered custom filter for {source_name}")


# Backward compatibility: Keep the old methods for existing code
class SearchFilterService_Legacy(SearchFilterService):
    """
    Legacy wrapper that implements the old interface methods.
    Deprecated - use the new modular approach instead.
    """

    def _add_date_filter(self, filters: Dict[str, Any], source_name: str):
        """Legacy method - deprecated"""
        logger.warning("_add_date_filter is deprecated, use build_filters() instead")
        start_year = self.current_year - self.recent_years_filter
        end_year = self.current_year

        if source_name == "Crossref":
            filters["from_pub_date"] = start_year
            filters["until_pub_date"] = end_year
        elif source_name == "PubMed":
            filters["date_range"] = {"start": str(start_year), "end": str(end_year)}
        else:
            filters["year"] = f"{start_year}-{end_year}"

    def _add_domain_filter(
        self, filters: Dict[str, Any], source_name: str, domain: str
    ):
        """Legacy method - deprecated"""
        logger.warning("_add_domain_filter is deprecated, use build_filters() instead")
        # Use the new implementation
        new_filters = self.build_filters(source_name, domain)
        filters.update(new_filters)

    def _add_source_optimizations(self, filters: Dict[str, Any], source_name: str):
        """Legacy method - deprecated"""
        logger.warning(
            "_add_source_optimizations is deprecated, use build_filters() instead"
        )
        # Optimizations are now handled automatically in build_filters()
