"""
CORE API client for open-access research papers and full-text access.
CORE aggregates open access research outputs from repositories and journals worldwide.
"""

import logging
from typing import Dict, Any, List, Optional
import os

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class COREClient(BaseAcademicClient):
    """
    CORE API client providing:
    - Open-access paper search and discovery
    - Full-text PDF access and download links
    - Repository and journal metadata
    - Citation and reference networks for OA papers

    Based on CORE API v3 documentation: https://api.core.ac.uk/docs/v3
    """

    def __init__(self, api_key: Optional[str] = None):
        resolved_api_key = api_key or os.getenv("CORE_API_KEY")

        if not resolved_api_key:
            logger.warning(
                "COREClient initialized without an API key. Most API calls will likely fail. "
                "Please provide an API key via constructor or CORE_API_KEY environment variable."
            )
            # Allow initialization with None api_key for now; actual calls will fail if key is mandatory

        super().__init__(
            base_url="https://api.core.ac.uk/v3",
            rate_limit_calls=100,  # 100 requests per hour for free tier
            rate_limit_period=3600,
            api_key=resolved_api_key,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get CORE API authentication headers"""
        if not self.api_key:
            logger.warning(
                "COREClient: API key not available for authenticated request. Returning empty headers."
            )
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for open-access papers using CORE's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return (max 100)
            offset: Number of results to skip
            filters: Additional filters (year, language, repository, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "q": query,
            "limit": min(limit, 100),  # API limit
            "offset": offset,
        }

        # Add filters if provided
        if filters:
            # Year range filter
            if "year" in filters:
                if isinstance(filters["year"], list) and len(filters["year"]) == 2:
                    params["yearFrom"] = filters["year"][0]
                    params["yearTo"] = filters["year"][1]
                else:
                    params["yearFrom"] = filters["year"]
                    params["yearTo"] = filters["year"]

            # Language filter
            if "language" in filters:
                params["language"] = filters["language"]

            # Repository filter
            if "repository" in filters:
                params["repositoryId"] = filters["repository"]

            # Full text filter
            if "fulltext" in filters and filters["fulltext"]:
                params["hasFulltext"] = "true"

            # Subject filter
            if "subject" in filters:
                params["subject"] = filters["subject"]

            # Sort filter
            if "sort" in filters:
                params["sort"] = filters["sort"]

        try:
            # Use the correct endpoint for searching works (add trailing slash)
            response = await self._make_request("GET", "/search/works/", params=params)

            # Handle different response structures
            papers = []
            if "results" in response:
                papers = response["results"]
            elif "data" in response:
                papers = response["data"]
            elif isinstance(response, list):
                papers = response
            else:
                logger.warning(
                    f"Unexpected CORE response structure: {list(response.keys())}"
                )
                return []

            logger.info(f"Found {len(papers)} papers from CORE for query: {query}")

            # Parse and normalize papers
            parsed_papers = []
            for paper in papers:
                try:
                    parsed_paper = JSONParser.parse_core_paper(paper)
                    parsed_papers.append(parsed_paper)
                except Exception as e:
                    logger.warning(f"Failed to parse CORE paper: {str(e)}")
                    continue

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching CORE: {str(e)}")
            # Log the full response for debugging
            if hasattr(e, "response"):
                logger.error(f"CORE API response: {e.response}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper

        Args:
            paper_id: CORE work ID

        Returns:
            Normalized paper dictionary or None if not found
        """
        try:
            response = await self._make_request("GET", f"/works/{paper_id}")

            if response:
                parsed_paper = JSONParser.parse_core_paper(response)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from CORE: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper

        Args:
            paper_id: CORE work ID
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        # CORE doesn't have a direct citations endpoint, so we search for papers citing this one
        paper_details = await self.get_paper_details(paper_id)
        if not paper_details:
            return []

        # Search for papers that mention this paper's DOI or title
        search_terms = []
        if paper_details.get("doi"):
            search_terms.append(f'"{paper_details["doi"]}"')
        if paper_details.get("title"):
            # Use part of the title for citation search
            title_words = paper_details["title"].split()[:5]
            search_terms.append(f'"{" ".join(title_words)}"')

        if not search_terms:
            return []

        try:
            citations = []
            for search_term in search_terms:
                params = {
                    "q": search_term,
                    "limit": min(limit, 100),
                }

                response = await self._make_request(
                    "GET", "/search/works/", params=params
                )
                results = response.get("results", [])

                for result in results:
                    # Skip the original paper
                    if result.get("id") != paper_id:
                        try:
                            parsed_paper = JSONParser.parse_core_paper(result)
                            citations.append(parsed_paper)
                        except Exception as e:
                            logger.warning(f"Failed to parse citation paper: {str(e)}")
                            continue

            logger.info(
                f"Found {len(citations)} potential citations for paper {paper_id}"
            )
            return self.normalize_papers(citations[:limit])

        except Exception as e:
            logger.error(f"Error getting citations from CORE: {str(e)}")
            return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper

        Args:
            paper_id: CORE work ID
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        # CORE doesn't provide structured reference data in their API
        # This would require full-text analysis which is beyond the scope
        logger.warning("CORE API doesn't provide structured reference data")
        return []

    async def get_fulltext_pdf(self, paper_id: str) -> Optional[str]:
        """
        Get the PDF download URL for a paper

        Args:
            paper_id: CORE work ID

        Returns:
            PDF download URL or None if not available
        """
        try:
            response = await self._make_request("GET", f"/works/{paper_id}")

            if response:
                # Check for downloadUrl in the response
                if "downloadUrl" in response:
                    return response["downloadUrl"]

                # Check for PDF URL in repositories
                if "repositories" in response:
                    for repo in response["repositories"]:
                        if "pdfUrl" in repo:
                            return repo["pdfUrl"]
                        if "fullTextUrl" in repo:
                            return repo["fullTextUrl"]

            return None

        except Exception as e:
            logger.error(f"Error getting PDF URL from CORE: {str(e)}")
            return None

    async def search_by_repository(
        self, repository_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search papers from a specific repository

        Args:
            repository_id: CORE repository ID
            limit: Maximum number of results

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "repositoryId": repository_id,
            "limit": min(limit, 100),
        }

        try:
            response = await self._make_request("GET", "/search/works/", params=params)
            papers = response.get("results", [])

            parsed_papers = []
            for paper in papers:
                try:
                    parsed_paper = JSONParser.parse_core_paper(paper)
                    parsed_papers.append(parsed_paper)
                except Exception as e:
                    logger.warning(f"Failed to parse repository paper: {str(e)}")
                    continue

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching repository in CORE: {str(e)}")
            return []

    async def get_repositories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of repositories in CORE

        Args:
            limit: Maximum number of repositories to return

        Returns:
            List of repository information
        """
        params = {"limit": min(limit, 100)}

        try:
            response = await self._make_request("GET", "/repositories", params=params)
            return response.get("results", [])

        except Exception as e:
            logger.error(f"Error getting repositories from CORE: {str(e)}")
            return []
