"""
Europe PMC API client for life sciences and biomedical literature.
Europe PMC provides access to life sciences literature including abstracts,
full text, and supplementary data.
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from ..common import BaseAcademicClient
from ..parsers import JSONParser

logger = logging.getLogger(__name__)


class EuropePMCClient(BaseAcademicClient):
    """
    Europe PMC API client providing:
    - Life sciences and biomedical literature search
    - Full-text article access
    - Citation and reference networks
    - MeSH term and keyword indexing
    - Patent and grant information
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url="https://www.ebi.ac.uk/europepmc/webservices/rest",
            rate_limit_calls=100,  # Conservative rate limit
            rate_limit_period=60,
            api_key=api_key,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Europe PMC is free to use, no authentication required"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Europe PMC's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return (max 1000)
            offset: Number of results to skip
            filters: Additional filters (year, source, open_access, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "query": query,
            "resultType": "core",
            "pageSize": min(limit, 1000),  # API limit
            "cursorMark": "*" if offset == 0 else f"offset_{offset}",
            "format": "json",
        }

        # Add filters if provided
        filter_parts = []
        if filters:
            if "year" in filters:
                if isinstance(filters["year"], list):
                    filter_parts.append(
                        f"(PUB_YEAR:[{filters['year'][0]} TO {filters['year'][1]}])"
                    )
                else:
                    filter_parts.append(f"PUB_YEAR:{filters['year']}")

            if "source" in filters:
                filter_parts.append(f"SRC:{filters['source']}")

            if "open_access" in filters and filters["open_access"]:
                filter_parts.append("OPEN_ACCESS:y")

            if "has_fulltext" in filters and filters["has_fulltext"]:
                filter_parts.append("HAS_FT:y")

            if "mesh_terms" in filters:
                for term in filters["mesh_terms"]:
                    filter_parts.append(f'MESH:"{term}"')

        if filter_parts:
            params["query"] = f"({query}) AND ({' AND '.join(filter_parts)})"

        try:
            response = await self._make_request("GET", "/search", params=params)

            result_list = response.get("resultList", {})
            papers = result_list.get("result", [])

            logger.info(
                f"Found {len(papers)} papers from Europe PMC for query: {query}"
            )

            # Parse and normalize papers
            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_europepmc_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching Europe PMC: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper

        Args:
            paper_id: Europe PMC ID, PMID, or DOI

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Handle different ID formats
        if paper_id.startswith("PMC"):
            source = "PMC"
            ext_id = paper_id
        elif paper_id.isdigit():
            source = "MED"
            ext_id = paper_id
        elif paper_id.startswith("10."):
            source = "DOI"
            ext_id = paper_id
        else:
            # Try as PMC ID first
            source = "PMC"
            ext_id = paper_id

        params = {
            "format": "json",
        }

        try:
            response = await self._make_request(
                "GET", f"/{source}/{ext_id}", params=params
            )

            if response and response.get("result"):
                result = (
                    response["result"][0]
                    if isinstance(response["result"], list)
                    else response["result"]
                )
                parsed_paper = JSONParser.parse_europepmc_paper(result)
                return self.normalize_paper(parsed_paper)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from Europe PMC: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper

        Args:
            paper_id: Europe PMC ID, PMID, or DOI
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        # Handle different ID formats
        if paper_id.startswith("PMC"):
            source = "PMC"
            ext_id = paper_id
        elif paper_id.isdigit():
            source = "MED"
            ext_id = paper_id
        else:
            source = "PMC"
            ext_id = paper_id

        params = {
            "format": "json",
            "pageSize": min(limit, 1000),
        }

        try:
            response = await self._make_request(
                "GET", f"/{source}/{ext_id}/citations", params=params
            )

            citation_list = response.get("citationList", {})
            citations = citation_list.get("citation", [])

            logger.info(f"Found {len(citations)} citations for paper {paper_id}")

            # Get detailed info for each citation
            parsed_citations = []
            for citation in citations[:limit]:
                if citation.get("id"):
                    citation_details = await self.get_paper_details(citation["id"])
                    if citation_details:
                        parsed_citations.append(citation_details)

            return parsed_citations

        except Exception as e:
            logger.error(f"Error getting citations from Europe PMC: {str(e)}")
            return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper

        Args:
            paper_id: Europe PMC ID, PMID, or DOI
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        # Handle different ID formats
        if paper_id.startswith("PMC"):
            source = "PMC"
            ext_id = paper_id
        elif paper_id.isdigit():
            source = "MED"
            ext_id = paper_id
        else:
            source = "PMC"
            ext_id = paper_id

        params = {
            "format": "json",
            "pageSize": min(limit, 1000),
        }

        try:
            response = await self._make_request(
                "GET", f"/{source}/{ext_id}/references", params=params
            )

            reference_list = response.get("referenceList", {})
            references = reference_list.get("reference", [])

            logger.info(f"Found {len(references)} references for paper {paper_id}")

            # Get detailed info for each reference
            parsed_references = []
            for reference in references[:limit]:
                if reference.get("id"):
                    reference_details = await self.get_paper_details(reference["id"])
                    if reference_details:
                        parsed_references.append(reference_details)

            return parsed_references

        except Exception as e:
            logger.error(f"Error getting references from Europe PMC: {str(e)}")
            return []

    async def search_by_mesh_terms(
        self, mesh_terms: List[str], limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search papers by MeSH terms

        Args:
            mesh_terms: List of MeSH terms to search for
            limit: Maximum number of results

        Returns:
            List of normalized paper dictionaries
        """
        mesh_query = " AND ".join([f'MESH:"{term}"' for term in mesh_terms])

        params = {
            "query": mesh_query,
            "resultType": "core",
            "pageSize": min(limit, 1000),
            "format": "json",
        }

        try:
            response = await self._make_request("GET", "/search", params=params)

            result_list = response.get("resultList", {})
            papers = result_list.get("result", [])

            parsed_papers = []
            for paper in papers:
                parsed_paper = JSONParser.parse_europepmc_paper(paper)
                parsed_papers.append(parsed_paper)

            return self.normalize_papers(parsed_papers)

        except Exception as e:
            logger.error(f"Error searching by MeSH terms in Europe PMC: {str(e)}")
            return []

    async def get_fulltext_xml(self, paper_id: str) -> Optional[str]:
        """
        Get full-text XML for a paper if available

        Args:
            paper_id: Europe PMC ID, PMID, or DOI

        Returns:
            Full-text XML or None if not available
        """
        # Handle different ID formats
        if paper_id.startswith("PMC"):
            source = "PMC"
            ext_id = paper_id
        elif paper_id.isdigit():
            source = "MED"
            ext_id = paper_id
        else:
            source = "PMC"
            ext_id = paper_id

        try:
            # Change response format for XML
            response = await self._make_request(
                "GET", f"/{source}/{ext_id}/fullTextXML"
            )
            return response

        except Exception as e:
            logger.error(f"Error getting full-text XML from Europe PMC: {str(e)}")
            return None

    async def search_clinical_trials(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for clinical trials related to a query

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of clinical trial information
        """
        params = {
            "query": f"({query}) AND SRC:ctg",
            "resultType": "core",
            "pageSize": min(limit, 1000),
            "format": "json",
        }

        try:
            response = await self._make_request("GET", "/search", params=params)

            result_list = response.get("resultList", {})
            trials = result_list.get("result", [])

            return trials

        except Exception as e:
            logger.error(f"Error searching clinical trials in Europe PMC: {str(e)}")
            return []
