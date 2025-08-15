"""
OpenAlex API client for comprehensive academic metadata and citation analysis.
OpenAlex provides one of the largest open catalogs of scholarly papers, authors,
institutions, concepts, and venues.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class OpenAlexClient(BaseAcademicClient):
    """
    OpenAlex API client providing:
    - Comprehensive paper search across all disciplines
    - Rich metadata including concepts and institutions
    - Citation and reference networks
    - Author and venue information
    - Open access status and links
    """

    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        super().__init__(
            base_url="https://api.openalex.org",
            rate_limit_calls=100,  # 100 requests per second for polite pool
            rate_limit_period=1,
            api_key=api_key,
        )
        self.email = email
        if email:
            self.headers["User-Agent"] = f"ScholarAI/1.0 (mailto:{email})"

    def _get_auth_headers(self) -> Dict[str, str]:
        """OpenAlex doesn't require authentication but benefits from email contact"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using OpenAlex's works API

        Args:
            query: Search query string
            limit: Maximum number of results to return (max 200)
            offset: Number of results to skip
            filters: Additional filters (year, type, open_access, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "search": query,
            "per-page": min(limit, 200),  # API limit
            "page": (offset // limit) + 1,
        }

        # Add filters if provided
        filter_parts = []
        if filters:
            if "year" in filters:
                if isinstance(filters["year"], list):
                    year_range = f"{filters['year'][0]}:{filters['year'][1]}"
                    filter_parts.append(f"publication_year:{year_range}")
                else:
                    filter_parts.append(f"publication_year:{filters['year']}")

            if "open_access" in filters and filters["open_access"]:
                filter_parts.append("is_oa:true")

            if "type" in filters:
                filter_parts.append(f"type:{filters['type']}")

            if "concept" in filters:
                filter_parts.append(
                    f"concepts.display_name.search:{quote(filters['concept'])}"
                )

        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        try:
            response = await self._make_request("GET", "/works", params=params)
            papers = response.get("results", [])

            logger.info(f"Found {len(papers)} papers from OpenAlex for query: {query}")

            # Parse and normalize papers
            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_openalex_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching OpenAlex: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper

        Args:
            paper_id: OpenAlex work ID or DOI

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Handle different ID formats
        if paper_id.startswith("10."):
            # DOI format
            work_id = f"https://doi.org/{paper_id}"
        elif not paper_id.startswith("https://openalex.org/"):
            # Assume it's an OpenAlex ID
            work_id = (
                f"https://openalex.org/W{paper_id}"
                if not paper_id.startswith("W")
                else f"https://openalex.org/{paper_id}"
            )
        else:
            work_id = paper_id

        try:
            response = await self._make_request(
                "GET", f"/works/{quote(work_id, safe='')}"
            )

            if response:
                parsed_paper = JSONParser.parse_openalex_paper(response)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from OpenAlex: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper

        Args:
            paper_id: OpenAlex work ID or DOI
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        # Handle different ID formats
        if paper_id.startswith("10."):
            work_id = f"https://doi.org/{paper_id}"
        elif not paper_id.startswith("https://openalex.org/"):
            work_id = (
                f"https://openalex.org/W{paper_id}"
                if not paper_id.startswith("W")
                else f"https://openalex.org/{paper_id}"
            )
        else:
            work_id = paper_id

        params = {
            "filter": f"cites:{quote(work_id, safe='')}",
            "per-page": min(limit, 200),
        }

        try:
            response = await self._make_request("GET", "/works", params=params)
            citations = response.get("results", [])

            logger.info(f"Found {len(citations)} citations for paper {paper_id}")

            parsed_citations = []
            for citation in citations:
                parsed_paper = JSONParser.parse_openalex_paper(citation)
                parsed_citations.append(parsed_paper)

            return self.normalize_papers(parsed_citations)

        except Exception as e:
            logger.error(f"Error getting citations from OpenAlex: {str(e)}")
            return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper

        Args:
            paper_id: OpenAlex work ID or DOI
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        # Get paper details first to access referenced_works
        paper_details = await self.get_paper_details(paper_id)
        if not paper_details or not paper_details.get("referenced_works"):
            return []

        referenced_work_ids = paper_details["referenced_works"][:limit]

        if not referenced_work_ids:
            return []

        # Build filter for referenced works
        filter_ids = "|".join(
            [quote(work_id, safe="") for work_id in referenced_work_ids]
        )
        params = {
            "filter": f"openalex_id:{filter_ids}",
            "per-page": min(len(referenced_work_ids), 200),
        }

        try:
            response = await self._make_request("GET", "/works", params=params)
            references = response.get("results", [])

            logger.info(f"Found {len(references)} references for paper {paper_id}")

            parsed_references = []
            for reference in references:
                parsed_paper = JSONParser.parse_openalex_paper(reference)
                parsed_references.append(parsed_paper)

            return self.normalize_papers(parsed_references)

        except Exception as e:
            logger.error(f"Error getting references from OpenAlex: {str(e)}")
            return []

    async def search_by_concept(
        self, concept: str, limit: int = 20, level: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search papers by concept/field of study

        Args:
            concept: Concept name to search for
            limit: Maximum number of results
            level: Concept level (0=most general, higher=more specific)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "filter": f"concepts.display_name.search:{quote(concept)},concepts.level:{level}",
            "per-page": min(limit, 200),
            "sort": "citation_count:desc",
        }

        try:
            response = await self._make_request("GET", "/works", params=params)
            papers = response.get("results", [])

            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_openalex_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching by concept in OpenAlex: {str(e)}")
            return []

    async def search_by_institution(
        self, institution: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search papers by institution

        Args:
            institution: Institution name to search for
            limit: Maximum number of results

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "filter": f"authorships.institutions.display_name.search:{quote(institution)}",
            "per-page": min(limit, 200),
            "sort": "citation_count:desc",
        }

        try:
            response = await self._make_request("GET", "/works", params=params)
            papers = response.get("results", [])

            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_openalex_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching by institution in OpenAlex: {str(e)}")
            return []
