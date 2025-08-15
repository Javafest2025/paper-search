"""
BASE (Bielefeld Academic Search Engine) API client for European academic repositories.
BASE provides access to over 240 million documents from thousands of content providers.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class BASESearchClient(BaseAcademicClient):
    """
    BASE API client providing:
    - Search across European academic repositories
    - OAI-PMH aggregated content access
    - Multi-disciplinary document discovery
    - Repository and source metadata
    """

    def __init__(self):
        super().__init__(
            base_url="https://api.base-search.net",
            rate_limit_calls=100,  # Conservative rate limit
            rate_limit_period=60,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """BASE API doesn't require authentication for basic search"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using BASE search API

        Args:
            query: Search query string
            limit: Maximum number of results to return (max 100)
            offset: Number of results to skip
            filters: Additional filters (year, language, type, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # BASE Search API endpoint appears to be unavailable or changed
        # Disabling for now to prevent 404 errors
        logger.warning(
            "BASE Search API endpoint is not available - returning empty results"
        )
        return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific document

        Args:
            paper_id: BASE document ID

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Search for the specific document by ID
        params = {"query": f"id:{paper_id}", "hits": 1, "format": "json"}

        try:
            response = await self._make_request("GET", "/search", params=params)

            if (
                response.get("response")
                and response["response"].get("docs")
                and len(response["response"]["docs"]) > 0
            ):

                doc = response["response"]["docs"][0]
                parsed_paper = JSONParser.parse_base_paper(doc)
                return self.normalize_paper(parsed_paper)

            return None

        except Exception as e:
            logger.error(f"Error getting paper details from BASE: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper
        Note: BASE doesn't provide structured citation data

        Args:
            paper_id: BASE document ID
            limit: Maximum number of citations to return

        Returns:
            Empty list (BASE doesn't provide citation networks)
        """
        logger.warning("BASE API doesn't provide citation data")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper
        Note: BASE doesn't provide structured reference data

        Args:
            paper_id: BASE document ID
            limit: Maximum number of references to return

        Returns:
            Empty list (BASE doesn't provide reference data)
        """
        logger.warning("BASE API doesn't provide reference data")
        return []

    async def search_by_repository(
        self, repository_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for documents from a specific repository

        Args:
            repository_name: Name of the repository to search in
            limit: Maximum number of documents to return

        Returns:
            List of normalized paper dictionaries
        """
        return await self.search_papers(
            query="*", limit=limit, filters={"repository": repository_name}
        )

    async def search_by_subject(
        self, subject: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for documents by subject classification

        Args:
            subject: Subject area to search for
            limit: Maximum number of documents to return

        Returns:
            List of normalized paper dictionaries
        """
        return await self.search_papers(
            query="*", limit=limit, filters={"subject": subject}
        )

    async def get_repositories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of available repositories in BASE
        Note: This would require a separate API endpoint that BASE might not provide

        Args:
            limit: Maximum number of repositories to return

        Returns:
            List of repository information dictionaries
        """
        # BASE doesn't provide a direct repositories endpoint in their search API
        # This would need to be implemented differently or return common repositories
        logger.warning("BASE API doesn't provide a repositories listing endpoint")

        # Return some common European repositories that are indexed by BASE
        common_repos = [
            {"name": "arXiv.org", "country": "USA", "type": "Preprint server"},
            {"name": "PubMed Central", "country": "USA", "type": "Medical"},
            {"name": "HAL", "country": "France", "type": "Institutional"},
            {"name": "NARCIS", "country": "Netherlands", "type": "National"},
            {"name": "SSOAR", "country": "Germany", "type": "Social sciences"},
            {"name": "OAPEN", "country": "Netherlands", "type": "Open access books"},
        ]

        return common_repos[:limit]

    async def search_open_access(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search specifically for open access documents

        Args:
            query: Search query string
            limit: Maximum number of documents to return

        Returns:
            List of normalized paper dictionaries
        """
        return await self.search_papers(
            query=query, limit=limit, filters={"open_access": True}
        )
