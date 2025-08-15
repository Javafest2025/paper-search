"""
DOAJ (Directory of Open Access Journals) API client for open access journal articles.
DOAJ provides access to open access journals and their articles across all disciplines.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class DOAJClient(BaseAcademicClient):
    """
    DOAJ API client providing:
    - Open access journal and article search
    - Journal metadata and indexing information
    - Article full-text access links
    - Publisher and subject classification data
    """

    def __init__(self):
        super().__init__(
            base_url="https://doaj.org/api",
            rate_limit_calls=60,  # Conservative rate limit
            rate_limit_period=60,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """DOAJ API doesn't require authentication for read operations"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for open access articles using DOAJ's articles API

        Args:
            query: Search query string
            limit: Maximum number of results to return (max 100)
            offset: Number of results to skip
            filters: Additional filters (subject, journal, language, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # URL encode the query for the path
        encoded_query = quote(query)

        # Build query parameters for pagination and filters
        params = {
            "pageSize": min(limit, 100),  # API limit
            "page": (offset // limit) + 1,
        }

        # Add filters if provided
        if filters:
            filter_parts = []

            if "subject" in filters:
                filter_parts.append(f"classification.term:\"{filters['subject']}\"")

            if "journal" in filters:
                filter_parts.append(f"bibjson.journal.title:\"{filters['journal']}\"")

            if "language" in filters:
                filter_parts.append(
                    f"bibjson.journal.language:\"{filters['language']}\""
                )

            if "year" in filters:
                if isinstance(filters["year"], list):
                    year_start, year_end = filters["year"]
                    filter_parts.append(f"bibjson.year:[{year_start} TO {year_end}]")
                else:
                    filter_parts.append(f"bibjson.year:{filters['year']}")

            if "country" in filters:
                filter_parts.append(f"bibjson.journal.country:\"{filters['country']}\"")

            if filter_parts:
                # Combine filters with the main query
                combined_query = f"({query}) AND ({' AND '.join(filter_parts)})"
                encoded_query = quote(combined_query)

        try:
            # Use the correct DOAJ v4 endpoint: /api/search/articles/{search_query}
            response = await self._make_request(
                "GET", f"search/articles/{encoded_query}", params=params
            )

            # Parse response - check for different possible response structures
            articles = []
            if isinstance(response, dict):
                articles = response.get("results", [])
            elif isinstance(response, list):
                articles = response

            logger.info(f"Found {len(articles)} articles from DOAJ for query: {query}")

            # Parse and normalize articles
            parsed_papers = []
            for article in articles:
                parsed_paper = JSONParser.parse_doaj_paper(article)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching DOAJ: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific article

        Args:
            paper_id: DOAJ article ID

        Returns:
            Normalized paper dictionary or None if not found
        """
        try:
            response = await self._make_request("GET", f"articles/{paper_id}")

            if response:
                parsed_paper = JSONParser.parse_doaj_paper(response)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from DOAJ: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper
        Note: DOAJ doesn't provide citation data

        Args:
            paper_id: DOAJ article ID
            limit: Maximum number of citations to return

        Returns:
            Empty list (DOAJ doesn't provide citation data)
        """
        logger.warning("DOAJ API doesn't provide citation data")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper
        Note: DOAJ doesn't provide reference data

        Args:
            paper_id: DOAJ article ID
            limit: Maximum number of references to return

        Returns:
            Empty list (DOAJ doesn't provide reference data)
        """
        logger.warning("DOAJ API doesn't provide reference data")
        return []

    async def search_journals(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for open access journals in DOAJ

        Args:
            query: Search query for journal names or subjects
            limit: Maximum number of journals to return

        Returns:
            List of journal dictionaries with metadata
        """
        # URL encode the query for the path
        encoded_query = quote(query)

        params = {
            "pageSize": min(limit, 100),
        }

        try:
            # Use the correct DOAJ v4 endpoint: /api/search/journals/{search_query}
            response = await self._make_request(
                "GET", f"search/journals/{encoded_query}", params=params
            )

            # Parse response - check for different possible response structures
            journals = []
            if isinstance(response, dict):
                journals = response.get("results", [])
            elif isinstance(response, list):
                journals = response

            logger.info(f"Found {len(journals)} journals from DOAJ for query: {query}")

            parsed_journals = []
            for journal in journals:
                parsed_journal = self._parse_doaj_journal(journal)
                parsed_journals.append(parsed_journal)

            return parsed_journals

        except Exception as e:
            logger.error(f"Error searching DOAJ journals: {str(e)}")
            return []

    async def search_by_subject(
        self, subject: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for articles by subject classification

        Args:
            subject: Subject area (e.g., "Medicine", "Engineering")
            limit: Maximum number of articles to return

        Returns:
            List of normalized paper dictionaries
        """
        return await self.search_papers(
            query="*", limit=limit, filters={"subject": subject}
        )

    def _parse_doaj_journal(self, journal: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DOAJ journal data to standardized format"""
        bibjson = journal.get("bibjson", {})

        return {
            "id": journal.get("id"),
            "title": bibjson.get("title", ""),
            "issn": bibjson.get("pissn") or bibjson.get("eissn"),
            "publisher": bibjson.get("publisher", {}).get("name", ""),
            "country": bibjson.get("publisher", {}).get("country", ""),
            "language": bibjson.get("language", []),
            "subjects": [subj.get("term", "") for subj in bibjson.get("subject", [])],
            "apc": bibjson.get("apc", {}),
            "license": bibjson.get("license", []),
            "homepage": (
                bibjson.get("link", [{}])[0].get("url", "")
                if bibjson.get("link")
                else ""
            ),
            "isOpenAccess": True,  # All DOAJ journals are open access
            "source": "doaj",
        }
