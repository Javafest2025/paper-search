"""
Semantic Scholar API client for comprehensive paper discovery and citation analysis.
Semantic Scholar provides one of the most comprehensive academic databases with
rich citation networks and metadata.
"""

import logging
from typing import Dict, Any, List, Optional

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class SemanticScholarClient(BaseAcademicClient):
    """
    Semantic Scholar API client providing:
    - Comprehensive paper search
    - Citation and reference networks
    - Author information and metrics
    - Venue and publication details
    - PDF availability detection
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url="https://api.semanticscholar.org/graph/v1",
            rate_limit_calls=100,  # 100 requests per 5 minutes for free tier
            rate_limit_period=300,
            api_key=api_key,
            timeout=60,  # Increase timeout for potentially slow responses
        )

        # Reduce default fields to essential ones for faster responses
        self.default_fields = (
            "paperId,externalIds,title,abstract,venue,year," \
            "isOpenAccess,openAccessPdf,authors,publicationDate"
        )

        # Use inherited HTTP client (HTTP/1.1) – avoids extra h2 dependency

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Semantic Scholar API authentication headers"""
        headers = {
            "User-Agent": "ScholarAI/1.0 (+https://scholarai.dev)"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Semantic Scholar's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (year, venue, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "query": query,
            "limit": min(limit, 100),  # API limit
            "offset": offset,
            "fields": self.default_fields,
        }

        # Add filters if provided
        if filters:
            if "year" in filters:
                params["year"] = filters["year"]
            if "venue" in filters:
                params["venue"] = filters["venue"]
            if "fieldsOfStudy" in filters:
                params["fieldsOfStudy"] = filters["fieldsOfStudy"]

        try:
            response = await self._make_request("GET", "/paper/search", params=params)
            papers = response.get("data", [])

            logger.info(
                f"Found {len(papers)} papers from Semantic Scholar for query: {query}"
            )

            # Parse and normalize papers
            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_semantic_scholar_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI

        Returns:
            Normalized paper dictionary or None if not found
        """
        fields = self.default_fields + ",references,citations"

        try:
            response = await self._make_request(
                "GET", f"/paper/{paper_id}", params={"fields": fields}
            )

            if response:
                parsed_paper = JSONParser.parse_semantic_scholar_paper(response)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from Semantic Scholar: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        fields = self.default_fields

        try:
            response = await self._make_request(
                "GET",
                f"/paper/{paper_id}/citations",
                params={"fields": fields, "limit": min(limit, 1000)},
            )

            citations = response.get("data", [])
            logger.info(f"Found {len(citations)} citations for paper {paper_id}")

            parsed_citations = []
            for citation in citations:
                citing_paper = citation.get("citingPaper", {})
                parsed_paper = JSONParser.parse_semantic_scholar_paper(citing_paper)
                parsed_citations.append(parsed_paper)

            return self.normalize_papers(parsed_citations)

        except Exception as e:
            logger.error(f"Error getting citations from Semantic Scholar: {str(e)}")
            return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        fields = self.default_fields

        try:
            response = await self._make_request(
                "GET",
                f"/paper/{paper_id}/references",
                params={"fields": fields, "limit": min(limit, 1000)},
            )

            references = response.get("data", [])
            logger.info(f"Found {len(references)} references for paper {paper_id}")

            parsed_references = []
            for reference in references:
                cited_paper = reference.get("citedPaper", {})
                parsed_paper = JSONParser.parse_semantic_scholar_paper(cited_paper)
                parsed_references.append(parsed_paper)

            return self.normalize_papers(parsed_references)

        except Exception as e:
            logger.error(f"Error getting references from Semantic Scholar: {str(e)}")
            return []

    async def get_author_papers(
        self, author_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers by a specific author

        Args:
            author_id: Semantic Scholar author ID
            limit: Maximum number of papers to return

        Returns:
            List of normalized paper dictionaries
        """
        fields = self.default_fields

        try:
            response = await self._make_request(
                "GET",
                f"/author/{author_id}/papers",
                params={"fields": fields, "limit": min(limit, 1000)},
            )

            papers = response.get("data", [])
            logger.info(f"Found {len(papers)} papers for author {author_id}")

            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_semantic_scholar_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error getting author papers from Semantic Scholar: {str(e)}")
            return []
