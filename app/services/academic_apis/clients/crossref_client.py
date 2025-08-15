"""
Crossref API client for comprehensive bibliographic metadata and DOI resolution.
Crossref is the official DOI registration agency and provides extensive
metadata for scholarly publications.
"""

import logging
from typing import Dict, Any, List, Optional

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class CrossrefClient(BaseAcademicClient):
    """
    Crossref API client providing:
    - DOI resolution and metadata
    - Comprehensive bibliographic data
    - Publisher and journal information
    - Citation and reference data
    - Funding information
    - License and access information
    """

    def __init__(
        self, api_key: Optional[str] = None, mailto: str = "contact@scholarai.dev"
    ):
        super().__init__(
            base_url="https://api.crossref.org",
            rate_limit_calls=50,  # Polite pool: 50 requests per second
            rate_limit_period=1,
            api_key=api_key,
        )
        self.mailto = mailto
        # Update headers for Crossref polite pool
        self.headers.update(
            {"User-Agent": f"ScholarAI/1.0 (https://scholarai.dev; mailto:{mailto})"}
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Crossref uses Plus service for authenticated requests"""
        if self.api_key:
            return {"Crossref-Plus-API-Token": f"Bearer {self.api_key}"}
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Crossref's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (type, publisher, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "query": query,
            "rows": min(limit, 1000),  # Crossref API limit
            "offset": offset,
            "sort": "relevance",
            "order": "desc",
        }

        # Add filters if provided
        if filters:
            filter_parts = []

            # Handle type filter properly
            if "type" in filters:
                filter_parts.append(f"type:{filters['type']}")

            if "publisher" in filters:
                filter_parts.append(f"publisher-name:{filters['publisher']}")

            # Handle date filters
            if "from_pub_date" in filters:
                filter_parts.append(f"from-pub-date:{filters['from_pub_date']}")

            if "until_pub_date" in filters:
                filter_parts.append(f"until-pub-date:{filters['until_pub_date']}")

            # Legacy year filter support
            if "year" in filters:
                if isinstance(filters["year"], list) and len(filters["year"]) == 2:
                    filter_parts.append(f"from-pub-date:{filters['year'][0]}")
                    filter_parts.append(f"until-pub-date:{filters['year'][1]}")
                else:
                    filter_parts.append(f"from-pub-date:{filters['year']}")
                    filter_parts.append(f"until-pub-date:{filters['year']}")

            if "journal" in filters:
                filter_parts.append(f"container-title:{filters['journal']}")

            # Boolean filters - only add if True
            if "has_full_text" in filters and filters["has_full_text"]:
                filter_parts.append("has-full-text:true")

            if "has_abstract" in filters and filters["has_abstract"]:
                filter_parts.append("has-abstract:true")

            if "has_license" in filters and filters["has_license"]:
                filter_parts.append("has-license:true")

            # Only add filter parameter if we have valid filters
            if filter_parts:
                params["filter"] = ",".join(filter_parts)

        try:
            response = await self._make_request("GET", "/works", params=params)

            message = response.get("message", {})
            items = message.get("items", [])

            logger.info(f"Found {len(items)} papers from Crossref for query: {query}")

            # Parse and normalize papers
            parsed_papers = []
            for item in items:
                parsed_paper = JSONParser.parse_crossref_work(item)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            # Log more detailed error information for filter debugging
            error_msg = str(e)
            if "filter" in error_msg.lower() and filters:
                logger.error(f"Crossref filter error with filters: {filters}")
                logger.error(f"Generated filter string: {params.get('filter', 'None')}")
            logger.error(f"Error searching Crossref: {error_msg}")
            return []

    async def get_paper_details(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper by DOI

        Args:
            doi: DOI of the paper

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Clean the DOI
        clean_doi = doi.replace("https://doi.org/", "").replace(
            "http://dx.doi.org/", ""
        )

        try:
            response = await self._make_request("GET", f"/works/{clean_doi}")

            message = response.get("message", {})
            if message:
                parsed_paper = JSONParser.parse_crossref_work(message)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting Crossref paper details: {str(e)}")
            return None

    async def get_citations(self, doi: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given DOI
        Note: Crossref doesn't provide direct citation data in their free API
        This would require integration with other services or Crossref Plus
        """
        logger.info("Crossref free API doesn't provide citation data directly")
        return []

    async def get_references(self, doi: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given DOI

        Args:
            doi: DOI of the paper
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        clean_doi = doi.replace("https://doi.org/", "").replace(
            "http://dx.doi.org/", ""
        )

        try:
            # Get the paper details first
            paper = await self.get_paper_details(clean_doi)
            if not paper:
                return []

            # Extract references from the paper metadata
            # Note: Not all papers have reference DOIs in Crossref
            references = []
            # This would need to be implemented based on Crossref's reference format

            return references

        except Exception as e:
            logger.error(f"Error getting references from Crossref: {str(e)}")
            return []

    async def resolve_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a DOI to get basic metadata

        Args:
            doi: DOI to resolve

        Returns:
            Basic paper metadata or None if not found
        """
        return await self.get_paper_details(doi)

    async def get_journal_info(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a journal by ISSN

        Args:
            issn: ISSN of the journal

        Returns:
            Journal metadata or None if not found
        """
        try:
            response = await self._make_request("GET", f"/journals/{issn}")

            message = response.get("message", {})
            if message:
                return {
                    "title": message.get("title"),
                    "issn": message.get("ISSN", []),
                    "publisher": message.get("publisher"),
                    "subject": message.get("subject", []),
                    "language": message.get("language"),
                    "url": message.get("URL"),
                }
            return None

        except Exception as e:
            logger.error(f"Error getting journal info from Crossref: {str(e)}")
            return None
