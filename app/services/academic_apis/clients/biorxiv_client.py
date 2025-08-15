"""
bioRxiv/medRxiv API client for preprint research papers.
bioRxiv hosts preprints in biology and medRxiv hosts preprints in medical and clinical research.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class BioRxivClient(BaseAcademicClient):
    """
    bioRxiv/medRxiv API client providing:
    - Preprint search and discovery
    - Early access to research findings
    - Subject category filtering
    - Author and institution tracking
    - Version history access
    """

    def __init__(self, server: str = "biorxiv"):
        """
        Initialize the client for bioRxiv or medRxiv

        Args:
            server: "biorxiv" or "medrxiv"
        """
        if server not in ["biorxiv", "medrxiv"]:
            raise ValueError("Server must be 'biorxiv' or 'medrxiv'")

        self.server = server
        super().__init__(
            base_url=f"https://api.{server}.org",
            rate_limit_calls=100,  # Conservative rate limit
            rate_limit_period=60,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """bioRxiv/medRxiv APIs are free to use, no authentication required"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for preprints
        Note: bioRxiv/medRxiv don't have a text search API, so we'll use the collection endpoint
        with date filtering and then filter results locally

        Args:
            query: Search query string (will be applied as local filter)
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (date, category, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # Get recent papers and filter locally since there's no search API
        date_from = datetime.now() - timedelta(
            days=365
        )  # Last year by default instead of 30 days
        date_to = datetime.now()

        if filters and "date_range" in filters:
            date_from = datetime.fromisoformat(filters["date_range"][0])
            date_to = datetime.fromisoformat(filters["date_range"][1])

        # Format interval as YYYY-MM-DD/YYYY-MM-DD as required by API
        interval = f"{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}"
        cursor = offset
        format_type = "json"

        # Build the correct URL path according to bioRxiv/medRxiv API docs:
        # https://api.biorxiv.org/details/[server]/[interval]/[cursor]/[format]
        # https://api.medrxiv.org/details/[server]/[interval]/[cursor]/[format]
        endpoint_path = f"details/{self.server}/{interval}/{cursor}/{format_type}"

        # Add category filter as query parameter if provided
        params = {}
        if filters and "category" in filters:
            params["category"] = filters["category"]

        try:
            response = await self._make_request("GET", endpoint_path, params=params)

            papers = response.get("collection", [])

            # Local filtering by query terms - use broader matching
            if query:
                query_terms = query.lower().split()
                filtered_papers = []
                for paper in papers:
                    title = paper.get("title", "").lower()
                    abstract = paper.get("abstract", "").lower()

                    # Handle authors - can be a string or list
                    authors_text = ""
                    authors_data = paper.get("authors", "")
                    if isinstance(authors_data, str):
                        authors_text = authors_data.lower()
                    elif isinstance(authors_data, list):
                        authors_text = " ".join(
                            [
                                (
                                    author.get("name", "")
                                    if isinstance(author, dict)
                                    else str(author)
                                )
                                for author in authors_data
                            ]
                        ).lower()

                    content = f"{title} {abstract} {authors_text}"

                    # Check if any query term matches (not all terms required)
                    if any(term in content for term in query_terms):
                        filtered_papers.append(paper)
                papers = filtered_papers

            # Apply additional filters
            if filters:
                if "category" in filters:
                    papers = [
                        p
                        for p in papers
                        if filters["category"].lower() in p.get("category", "").lower()
                    ]

            logger.info(
                f"Found {len(papers)} papers from {self.server} for query: {query}"
            )

            # Parse and normalize papers
            parsed_papers = []
            for paper in papers[:limit]:
                parsed_paper = JSONParser.parse_biorxiv_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching {self.server}: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific preprint

        Args:
            paper_id: DOI or bioRxiv/medRxiv ID

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Handle DOI format
        if paper_id.startswith("10.1101/"):
            doi = paper_id
        elif "/" in paper_id:
            doi = f"10.1101/{paper_id}"
        else:
            doi = f"10.1101/{paper_id}"

        try:
            # Use correct path format: /details/[server]/[DOI]/na/[format]
            endpoint_path = f"details/{self.server}/{doi}/na/json"
            response = await self._make_request("GET", endpoint_path)

            if response and response.get("collection"):
                paper = response["collection"][0]
                parsed_paper = JSONParser.parse_biorxiv_paper(paper)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from {self.server}: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        bioRxiv/medRxiv don't provide citation data directly

        Args:
            paper_id: Paper DOI or ID
            limit: Maximum citations

        Returns:
            Empty list (citations not supported)
        """
        logger.warning(f"{self.server} doesn't provide citation data")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        bioRxiv/medRxiv don't provide structured reference data

        Args:
            paper_id: Paper DOI or ID
            limit: Maximum references

        Returns:
            Empty list (references not supported)
        """
        logger.warning(f"{self.server} doesn't provide reference data")
        return []

    async def get_papers_by_category(
        self, category: str, limit: int = 20, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get papers from a specific subject category

        Args:
            category: Subject category (e.g., "bioinformatics", "neuroscience")
            limit: Maximum number of results
            days_back: Number of days to look back

        Returns:
            List of normalized paper dictionaries
        """
        date_from = datetime.now() - timedelta(days=days_back)
        date_to = datetime.now()

        # Format interval and build correct path
        interval = f"{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}"
        endpoint_path = f"details/{self.server}/{interval}/0/json"

        # Add category as query parameter
        params = {"category": category}

        try:
            response = await self._make_request("GET", endpoint_path, params=params)
            papers = response.get("collection", [])

            # Filter by category (additional filtering in case API doesn't handle it properly)
            filtered_papers = [
                p for p in papers if category.lower() in p.get("category", "").lower()
            ]

            parsed_papers = []
            for paper in filtered_papers[:limit]:
                parsed_paper = JSONParser.parse_biorxiv_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(
                f"Error getting papers by category from {self.server}: {str(e)}"
            )
            return []

    async def get_recent_papers(
        self, days: int = 7, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent preprints from the last N days

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of normalized paper dictionaries
        """
        date_from = datetime.now() - timedelta(days=days)
        date_to = datetime.now()

        # Format interval and build correct path
        interval = f"{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}"
        endpoint_path = f"details/{self.server}/{interval}/0/json"

        try:
            response = await self._make_request("GET", endpoint_path)
            papers = response.get("collection", [])

            parsed_papers = []
            for paper in papers[:limit]:
                parsed_paper = JSONParser.parse_biorxiv_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error getting recent papers from {self.server}: {str(e)}")
            return []

    async def get_paper_versions(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a preprint

        Args:
            paper_id: DOI or bioRxiv/medRxiv ID

        Returns:
            List of paper versions with metadata
        """
        # Handle DOI format
        if paper_id.startswith("10.1101/"):
            doi = paper_id
        elif "/" in paper_id:
            doi = f"10.1101/{paper_id}"
        else:
            doi = f"10.1101/{paper_id}"

        try:
            # Use correct path format: /details/[server]/[DOI]/na/[format]
            endpoint_path = f"details/{self.server}/{doi}/na/json"
            response = await self._make_request("GET", endpoint_path)

            if response and response.get("collection"):
                versions = response["collection"]

                parsed_versions = []
                for version in versions:
                    parsed_paper = JSONParser.parse_biorxiv_paper(version)
                    parsed_versions.append(parsed_paper)

                return self.normalize_papers(parsed_versions)
            return []

        except Exception as e:
            logger.error(f"Error getting paper versions from {self.server}: {str(e)}")
            return []

    async def search_by_author(
        self, author_name: str, limit: int = 20, days_back: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Search papers by author name

        Args:
            author_name: Author name to search for
            limit: Maximum number of results
            days_back: Number of days to look back

        Returns:
            List of normalized paper dictionaries
        """
        date_from = datetime.now() - timedelta(days=days_back)
        date_to = datetime.now()

        # Format interval and build correct path
        interval = f"{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}"
        endpoint_path = f"details/{self.server}/{interval}/0/json"

        try:
            response = await self._make_request("GET", endpoint_path)
            papers = response.get("collection", [])

            # Filter by author name
            author_lower = author_name.lower()
            filtered_papers = []
            for paper in papers:
                authors = paper.get("authors", [])
                for author in authors:
                    if author_lower in author.get("name", "").lower():
                        filtered_papers.append(paper)
                        break

            parsed_papers = []
            for paper in filtered_papers[:limit]:
                parsed_paper = JSONParser.parse_biorxiv_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching by author in {self.server}: {str(e)}")
            return []
