"""
Unpaywall API client for open-access PDF discovery and resolution.
Unpaywall finds fulltext PDFs for scholarly articles by checking for legal open access copies.
"""

import logging
from typing import Dict, Any, List, Optional
import urllib.parse

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class UnpaywallClient(BaseAcademicClient):
    """
    Unpaywall API client providing:
    - Open-access PDF resolution by DOI
    - Repository and publisher OA information
    - Legal fulltext access detection
    - OA hosting and license information
    - Text search functionality
    """

    def __init__(self, email: str):
        if not email:
            raise ValueError("Unpaywall API requires an email address")

        super().__init__(
            base_url="https://api.unpaywall.org/v2",
            rate_limit_calls=100,  # 100 requests per second
            rate_limit_period=1,
        )
        self.email = email
        logger.info(f"Initialized Unpaywall client with email: {email}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Unpaywall doesn't require authentication but requires email parameter"""
        return {}

    async def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get paper information and OA status by DOI

        Args:
            doi: Paper DOI

        Returns:
            Paper information with OA status or None if not found
        """
        if not doi:
            return None

        # Clean DOI
        if doi.startswith("doi:"):
            doi = doi[4:]
        if doi.startswith("https://doi.org/"):
            doi = doi[16:]

        params = {"email": self.email}

        try:
            response = await self._make_request("GET", f"/{doi}", params=params)

            if response:
                parsed_paper = JSONParser.parse_unpaywall_paper(response)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper from Unpaywall: {str(e)}")
            return None

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search papers using Unpaywall's search API

        Args:
            query: Search query string
            limit: Maximum results (50 per page is the API limit)
            offset: Offset for pagination
            filters: Optional filters (is_oa, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        if not query:
            return []

        # Build search parameters
        params = {"query": query, "email": self.email}

        # Handle pagination - Unpaywall uses page numbers, not offset
        page = (offset // min(limit, 50)) + 1
        if page > 1:
            params["page"] = page

        # Apply filters
        if filters:
            # Check for open access filter
            if "is_oa" in filters:
                params["is_oa"] = filters["is_oa"]

            # Handle date filters if provided
            if "year_min" in filters:
                # Note: Unpaywall search doesn't directly support date filtering
                # but we can filter results post-search
                pass

        try:
            logger.info(f"Searching Unpaywall with query: '{query}', params: {params}")
            response = await self._make_request("GET", "/search", params=params)

            if not response:
                return []

            # Handle response format - could be array of results or object with results
            results = (
                response if isinstance(response, list) else response.get("results", [])
            )

            papers = []
            for result in results[:limit]:  # Respect the limit parameter
                # The search API returns objects with 'response' containing the paper data
                paper_data = result.get("response", result)

                if paper_data:
                    parsed_paper = JSONParser.parse_unpaywall_paper(paper_data)
                    normalized_paper = self.normalize_paper(parsed_paper)
                    if normalized_paper:
                        # Add search score if available
                        if "score" in result:
                            normalized_paper["search_score"] = result["score"]
                        papers.append(normalized_paper)

            logger.info(f"Found {len(papers)} papers from Unpaywall search")
            return papers

        except Exception as e:
            logger.error(f"Error searching papers in Unpaywall: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed paper information by DOI

        Args:
            paper_id: DOI of the paper

        Returns:
            Normalized paper dictionary or None if not found
        """
        return await self.get_paper_by_doi(paper_id)

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Unpaywall doesn't provide citation data

        Args:
            paper_id: Paper DOI
            limit: Maximum citations

        Returns:
            Empty list (citations not supported)
        """
        logger.warning("Unpaywall doesn't provide citation data")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Unpaywall doesn't provide reference data

        Args:
            paper_id: Paper DOI
            limit: Maximum references

        Returns:
            Empty list (references not supported)
        """
        logger.warning("Unpaywall doesn't provide reference data")
        return []

    async def check_multiple_dois(self, dois: List[str]) -> List[Dict[str, Any]]:
        """
        Check OA status for multiple DOIs

        Args:
            dois: List of DOIs to check

        Returns:
            List of paper information with OA status
        """
        results = []

        for doi in dois:
            paper = await self.get_paper_by_doi(doi)
            if paper:
                results.append(paper)

        return results

    async def get_oa_pdf_url(self, doi: str) -> Optional[str]:
        """
        Get the best open-access PDF URL for a DOI

        Args:
            doi: Paper DOI

        Returns:
            PDF URL or None if no OA version available
        """
        paper = await self.get_paper_by_doi(doi)

        # Use the normalized field name 'isOpenAccess'
        if not paper or not paper.get("isOpenAccess"):
            return None

        # Look for best OA location
        oa_locations = paper.get("oa_locations", [])

        # Prefer repository versions over publisher versions
        for location in oa_locations:
            if location.get("host_type") == "repository" and location.get(
                "url_for_pdf"
            ):
                return location["url_for_pdf"]

        # Fall back to publisher versions
        for location in oa_locations:
            if location.get("url_for_pdf"):
                return location["url_for_pdf"]

        return None

    async def get_oa_status_bulk(self, dois: List[str]) -> Dict[str, bool]:
        """
        Get OA status for multiple DOIs in bulk (simplified)

        Args:
            dois: List of DOIs to check

        Returns:
            Dictionary mapping DOI to OA status
        """
        oa_status = {}

        for doi in dois:
            paper = await self.get_paper_by_doi(doi)
            # Use the normalized field name 'isOpenAccess'
            oa_status[doi] = paper.get("isOpenAccess", False) if paper else False

        return oa_status

    async def get_repository_versions(self, doi: str) -> List[Dict[str, Any]]:
        """
        Get all repository versions of a paper

        Args:
            doi: Paper DOI

        Returns:
            List of repository location information
        """
        paper = await self.get_paper_by_doi(doi)

        if not paper:
            return []

        oa_locations = paper.get("oa_locations", [])
        repository_versions = []

        for location in oa_locations:
            if location.get("host_type") == "repository":
                repository_versions.append(
                    {
                        "repository": location.get("repository_institution"),
                        "url": location.get("url"),
                        "pdf_url": location.get("url_for_pdf"),
                        "version": location.get("oa_version"),
                        "license": location.get("license"),
                    }
                )

        return repository_versions

    async def search_open_access_only(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for open access papers only

        Args:
            query: Search query string
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of open access papers
        """
        filters = {"is_oa": True}
        return await self.search_papers(query, limit, offset, filters)
