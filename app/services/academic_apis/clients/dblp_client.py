"""
DBLP API client for computer science bibliography.
DBLP provides bibliographic information for computer science publications
including conferences, journals, and proceedings.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

from ..common import BaseAcademicClient
from ..parsers import XMLParser

logger = logging.getLogger(__name__)


class DBLPClient(BaseAcademicClient):
    """
    DBLP API client providing:
    - Computer science bibliography search
    - Author publication lists and metrics
    - Venue and conference proceedings
    - Co-authorship networks
    - Publication venue rankings
    """

    def __init__(self):
        super().__init__(
            base_url="https://dblp.org/search",
            rate_limit_calls=100,  # Conservative rate limit
            rate_limit_period=60,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """DBLP is free to use, no authentication required"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using DBLP's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return (max 1000)
            offset: Number of results to skip (DBLP uses 'f' parameter)
            filters: Additional filters (year, venue, type, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "q": query,
            "h": min(limit, 1000),  # API limit (h = hits)
            "f": offset,  # First result index
            "format": "json",
        }

        # Add filters if provided
        if filters:
            query_parts = [query]

            if "year" in filters:
                if isinstance(filters["year"], list):
                    year_filter = f"year:{filters['year'][0]}..{filters['year'][1]}"
                else:
                    year_filter = f"year:{filters['year']}"
                query_parts.append(year_filter)

            if "venue" in filters:
                query_parts.append(f"venue:{filters['venue']}")

            if "type" in filters:
                # DBLP publication types: article, inproceedings, proceedings, book, incollection, phdthesis, mastersthesis
                query_parts.append(f"type:{filters['type']}")

            params["q"] = " ".join(query_parts)

        try:
            response = await self._make_request("GET", "/publ/api", params=params)

            result = response.get("result", {})
            hits = result.get("hits", {})
            papers = hits.get("hit", [])

            logger.info(f"Found {len(papers)} papers from DBLP for query: {query}")

            # Parse and normalize papers
            parsed_papers = []
            for paper_hit in papers:
                paper_info = paper_hit.get("info", {})
                parsed_paper = XMLParser.parse_dblp_paper(paper_info)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching DBLP: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper
        Note: DBLP doesn't have individual paper detail endpoints,
        so we search by the paper key/URL

        Args:
            paper_id: DBLP paper key or URL

        Returns:
            Normalized paper dictionary or None if not found
        """
        try:
            # If it's a DBLP key, search for it specifically
            params = {
                "q": paper_id,
                "h": 1,
                "format": "json",
            }

            response = await self._make_request("GET", "/publ/api", params=params)

            result = response.get("result", {})
            hits = result.get("hits", {})
            papers = hits.get("hit", [])

            if papers:
                paper_info = papers[0].get("info", {})
                parsed_paper = XMLParser.parse_dblp_paper(paper_info)
                return self.normalize_paper(parsed_paper)

            return None

        except Exception as e:
            logger.error(f"Error getting paper details from DBLP: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        DBLP doesn't provide citation information directly

        Args:
            paper_id: DBLP paper key
            limit: Maximum citations

        Returns:
            Empty list (citations not supported)
        """
        logger.warning("DBLP doesn't provide citation data")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        DBLP doesn't provide reference information directly

        Args:
            paper_id: DBLP paper key
            limit: Maximum references

        Returns:
            Empty list (references not supported)
        """
        logger.warning("DBLP doesn't provide reference data")
        return []

    async def search_author(
        self, author_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for author information

        Args:
            author_name: Author name to search for
            limit: Maximum number of results

        Returns:
            List of author information
        """
        params = {
            "q": author_name,
            "h": min(limit, 1000),
            "format": "json",
        }

        try:
            response = await self._make_request("GET", "/author/api", params=params)

            result = response.get("result", {})
            hits = result.get("hits", {})
            authors = hits.get("hit", [])

            parsed_authors = []
            for author_hit in authors:
                author_info = author_hit.get("info", {})
                parsed_authors.append(
                    {
                        "name": author_info.get("author", ""),
                        "dblp_key": author_info.get("url", ""),
                        "aliases": author_info.get("aliases", []),
                    }
                )

            return parsed_authors

        except Exception as e:
            logger.error(f"Error searching authors in DBLP: {str(e)}")
            return []

    async def get_author_publications(
        self, author_key: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get publications by a specific author using their DBLP key

        Args:
            author_key: DBLP author key (from author search)
            limit: Maximum number of publications

        Returns:
            List of normalized paper dictionaries
        """
        try:
            # DBLP author URLs follow pattern: https://dblp.org/pid/xx/yy.xml
            xml_url = f"https://dblp.org/pid/{author_key}.xml"

            # Make direct request to author's XML
            response = await self.client.get(xml_url)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.text)
            publications = []

            for pub in root.findall(".//r"):
                # Extract publication information
                pub_info = {}
                for child in pub:
                    if child.tag in [
                        "article",
                        "inproceedings",
                        "proceedings",
                        "book",
                        "incollection",
                    ]:
                        pub_info.update(XMLParser.parse_dblp_xml_element(child))

                if pub_info:
                    parsed_paper = XMLParser.parse_dblp_paper(pub_info)
                    publications.append(parsed_paper)

            return self.normalize_papers(publications[:limit])

        except Exception as e:
            logger.error(f"Error getting author publications from DBLP: {str(e)}")
            return []

    async def search_venue(
        self, venue_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for venue information (conferences, journals)

        Args:
            venue_name: Venue name to search for
            limit: Maximum number of results

        Returns:
            List of venue information
        """
        params = {
            "q": venue_name,
            "h": min(limit, 1000),
            "format": "json",
        }

        try:
            response = await self._make_request("GET", "/venue/api", params=params)

            result = response.get("result", {})
            hits = result.get("hits", {})
            venues = hits.get("hit", [])

            parsed_venues = []
            for venue_hit in venues:
                venue_info = venue_hit.get("info", {})
                parsed_venues.append(
                    {
                        "name": venue_info.get("venue", ""),
                        "dblp_key": venue_info.get("url", ""),
                        "type": venue_info.get("type", ""),
                        "acronym": venue_info.get("acronym", ""),
                    }
                )

            return parsed_venues

        except Exception as e:
            logger.error(f"Error searching venues in DBLP: {str(e)}")
            return []

    async def get_venue_publications(
        self, venue_key: str, year: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get publications from a specific venue

        Args:
            venue_key: DBLP venue key
            year: Optional year filter
            limit: Maximum number of publications

        Returns:
            List of normalized paper dictionaries
        """
        query = f"venue:{venue_key}"
        if year:
            query += f" year:{year}"

        params = {
            "q": query,
            "h": min(limit, 1000),
            "format": "json",
        }

        try:
            response = await self._make_request("GET", "/publ/api", params=params)

            result = response.get("result", {})
            hits = result.get("hits", {})
            papers = hits.get("hit", [])

            parsed_papers = []
            for paper_hit in papers:
                paper_info = paper_hit.get("info", {})
                parsed_paper = XMLParser.parse_dblp_paper(paper_info)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error getting venue publications from DBLP: {str(e)}")
            return []

    async def search_by_publication_type(
        self, pub_type: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search publications by type

        Args:
            pub_type: Publication type (article, inproceedings, proceedings, book, etc.)
            limit: Maximum number of results

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "q": f"type:{pub_type}",
            "h": min(limit, 1000),
            "format": "json",
        }

        try:
            response = await self._make_request("GET", "/publ/api", params=params)

            result = response.get("result", {})
            hits = result.get("hits", {})
            papers = hits.get("hit", [])

            parsed_papers = []
            for paper_hit in papers:
                paper_info = paper_hit.get("info", {})
                parsed_paper = XMLParser.parse_dblp_paper(paper_info)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching by publication type in DBLP: {str(e)}")
            return []
