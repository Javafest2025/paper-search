"""
arXiv API client for accessing preprints and early research papers.
arXiv is a crucial source for the latest research, especially in physics,
mathematics, computer science, and related fields.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote
import feedparser

from ..common import BaseAcademicClient
from ..parsers import FeedParser

logger = logging.getLogger(__name__)


class ArxivClient(BaseAcademicClient):
    """
    arXiv API client providing:
    - Search for preprints and papers
    - Access to full-text PDFs
    - Author and category information
    - Version history tracking
    - Subject classification
    """

    def __init__(self):
        super().__init__(
            base_url="https://export.arxiv.org/api",
            rate_limit_calls=300,  # arXiv allows 3 requests per second
            rate_limit_period=60,
            timeout=30,
        )
        
        # Override headers for arXiv which returns Atom XML, not JSON
        self.headers = {
            "User-Agent": "ScholarAI/1.0 (https://scholarai.dev; mailto:contact@scholarai.dev)",
            "Accept": "application/atom+xml",  # Changed from application/json
            "Content-Type": "application/atom+xml",  # Changed from application/json
        }
        
        # Update the HTTP client with new headers
        import httpx
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self.headers,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """arXiv doesn't require authentication"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using arXiv's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (category, date range, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # Build search query
        search_query = self._build_search_query(query, filters)

        params = {
            "search_query": search_query,
            "start": offset,
            "max_results": min(limit, 2000),  # arXiv API limit
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            response = await self._make_request("GET", "/query", params=params)

            # Parse the Atom feed response
            if isinstance(response, dict) and "content" in response:
                feed_content = response["content"]
            else:
                feed_content = str(response)

            # Use feed parser to parse the content
            papers = FeedParser.parse_feed_content(feed_content)

            logger.info(f"Found {len(papers)} papers from arXiv for query: {query}")

            # Normalize papers using base client
            return self.normalize_papers(papers)

        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific arXiv paper

        Args:
            paper_id: arXiv ID (e.g., "2301.12345" or "cs.AI/0601001")

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Clean the arXiv ID
        arxiv_id = paper_id.replace("arXiv:", "").replace("https://arxiv.org/abs/", "")

        params = {"id_list": arxiv_id, "max_results": 1}

        try:
            response = await self._make_request("GET", "/query", params=params)

            # Parse the Atom feed response
            if isinstance(response, dict) and "content" in response:
                feed_content = response["content"]
            else:
                feed_content = str(response)

            papers = FeedParser.parse_feed_content(feed_content)

            if papers:
                return self.normalize_paper(papers[0])
            return None

        except Exception as e:
            logger.error(f"Error getting arXiv paper details: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        arXiv doesn't provide direct citation data, so we return empty list
        This could be enhanced by integrating with other services
        """
        logger.info("arXiv doesn't provide citation data directly")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        arXiv doesn't provide direct reference data, so we return empty list
        This could be enhanced by parsing PDF content for references
        """
        logger.info("arXiv doesn't provide reference data directly")
        return []

    def _build_search_query(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build arXiv search query with filters

        Args:
            query: Base search query
            filters: Additional filters

        Returns:
            Formatted search query string
        """
        search_parts = []

        # Add main query to title and abstract
        if query:
            search_parts.append(f"all:{quote(query)}")

        # Add filters if provided
        if filters:
            if "category" in filters:
                search_parts.append(f"cat:{filters['category']}")

            if "author" in filters:
                search_parts.append(f"au:{quote(filters['author'])}")

            if "title" in filters:
                search_parts.append(f"ti:{quote(filters['title'])}")

            if "abstract" in filters:
                search_parts.append(f"abs:{quote(filters['abstract'])}")

        return " AND ".join(search_parts) if search_parts else "all:*"

    async def download_pdf(self, arxiv_id: str) -> Optional[bytes]:
        """
        Download PDF content for an arXiv paper

        Args:
            arxiv_id: arXiv ID

        Returns:
            PDF content as bytes or None if not available
        """
        # Clean the arXiv ID
        clean_id = arxiv_id.replace("arXiv:", "").replace("https://arxiv.org/abs/", "")
        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                return response.content

        except Exception as e:
            logger.error(f"Error downloading arXiv PDF: {str(e)}")
            return None

    async def get_paper_versions(self, arxiv_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for an arXiv paper

        Args:
            arxiv_id: arXiv ID

        Returns:
            List of version information
        """
        # arXiv API doesn't provide version history directly
        # This would need to be implemented by parsing the paper page
        logger.info("arXiv version history not available through API")
        return []
