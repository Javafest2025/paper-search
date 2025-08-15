"""
PubMed API client for biomedical and life sciences literature.
PubMed is the premier database for biomedical literature maintained by NCBI.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

from ..common import BaseAcademicClient
from ..parsers import XMLParser

logger = logging.getLogger(__name__)


class PubMedClient(BaseAcademicClient):
    """
    PubMed API client providing:
    - Biomedical literature search
    - MeSH term integration
    - Author and affiliation data
    - Journal and publication metadata
    - Abstract and full-text access
    """

    def __init__(
        self, api_key: Optional[str] = None, email: str = "contact@scholarai.dev"
    ):
        super().__init__(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            rate_limit_calls=10,  # 10 requests per second with API key, 3 without
            rate_limit_period=1,
            api_key=api_key,
        )
        self.email = email
        self.tool = "ScholarAI"

    def _get_auth_headers(self) -> Dict[str, str]:
        """PubMed doesn't use headers for auth, uses query parameters"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using PubMed's ESearch API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (date range, publication type, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # Build search query with filters
        search_query = self._build_search_query(query, filters)

        # First, search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": min(limit, 10000),  # PubMed limit
            "retstart": offset,
            "sort": "relevance",
            "tool": self.tool,
            "email": self.email,
        }

        if self.api_key:
            search_params["api_key"] = self.api_key

        try:
            # Search for PMIDs
            search_response = await self._make_request(
                "GET", "/esearch.fcgi", params=search_params
            )

            # Parse XML response
            if isinstance(search_response, dict) and "content" in search_response:
                xml_content = search_response["content"]
            else:
                xml_content = str(search_response)

            root = ET.fromstring(xml_content)
            pmids = [id_elem.text for id_elem in root.findall(".//Id")]

            if not pmids:
                logger.info(f"No papers found in PubMed for query: {query}")
                return []

            logger.info(f"Found {len(pmids)} PMIDs from PubMed for query: {query}")

            # Fetch detailed information for the PMIDs
            papers = await self._fetch_paper_details(pmids)
            return papers

        except Exception as e:
            logger.error(f"Error searching PubMed: {str(e)}")
            return []

    async def get_paper_details(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific PubMed paper

        Args:
            pmid: PubMed ID

        Returns:
            Normalized paper dictionary or None if not found
        """
        papers = await self._fetch_paper_details([pmid])
        return papers[0] if papers else None

    async def get_citations(self, pmid: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given PMID using PubMed's link database

        Args:
            pmid: PubMed ID
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_citedin",
            "tool": self.tool,
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self._make_request("GET", "/elink.fcgi", params=params)

            # Parse XML response
            if isinstance(response, dict) and "content" in response:
                xml_content = response["content"]
            else:
                xml_content = str(response)

            root = ET.fromstring(xml_content)
            citing_pmids = [id_elem.text for id_elem in root.findall(".//Link/Id")]

            # Limit results
            citing_pmids = citing_pmids[:limit]

            if citing_pmids:
                logger.info(f"Found {len(citing_pmids)} citations for PMID {pmid}")
                return await self._fetch_paper_details(citing_pmids)

            return []

        except Exception as e:
            logger.error(f"Error getting citations from PubMed: {str(e)}")
            return []

    async def get_references(self, pmid: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given PMID

        Args:
            pmid: PubMed ID
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_refs",
            "tool": self.tool,
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self._make_request("GET", "/elink.fcgi", params=params)

            # Parse XML response
            if isinstance(response, dict) and "content" in response:
                xml_content = response["content"]
            else:
                xml_content = str(response)

            root = ET.fromstring(xml_content)
            ref_pmids = [id_elem.text for id_elem in root.findall(".//Link/Id")]

            # Limit results
            ref_pmids = ref_pmids[:limit]

            if ref_pmids:
                logger.info(f"Found {len(ref_pmids)} references for PMID {pmid}")
                return await self._fetch_paper_details(ref_pmids)

            return []

        except Exception as e:
            logger.error(f"Error getting references from PubMed: {str(e)}")
            return []

    async def _fetch_paper_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed paper information for a list of PMIDs

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of normalized paper dictionaries
        """
        if not pmids:
            return []

        # Batch fetch details (PubMed allows up to 200 IDs per request)
        batch_size = 200
        all_papers = []

        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]

            params = {
                "db": "pubmed",
                "id": ",".join(batch_pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "tool": self.tool,
                "email": self.email,
            }

            if self.api_key:
                params["api_key"] = self.api_key

            try:
                response = await self._make_request(
                    "GET", "/efetch.fcgi", params=params
                )

                # Parse XML response
                if isinstance(response, dict) and "content" in response:
                    xml_content = response["content"]
                else:
                    xml_content = str(response)

                root = ET.fromstring(xml_content)

                # Extract paper data from each article
                for article in root.findall(".//PubmedArticle"):
                    try:
                        paper_data = XMLParser.parse_pubmed_article(article)
                        normalized_paper = self.normalize_paper(paper_data)
                        if normalized_paper:
                            all_papers.append(normalized_paper)
                    except Exception as e:
                        logger.warning(f"Error parsing PubMed article: {str(e)}")

            except Exception as e:
                logger.error(f"Error fetching PubMed batch: {str(e)}")

        logger.info(f"Successfully parsed {len(all_papers)} PubMed papers")
        return all_papers

    def _build_search_query(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build PubMed search query with filters

        Args:
            query: Base search query
            filters: Additional filters

        Returns:
            Formatted search query string
        """
        search_parts = [query]

        if filters:
            if "date_range" in filters:
                date_range = filters["date_range"]
                if "start" in date_range:
                    search_parts.append(
                        f'("{date_range["start"]}"[Date - Publication] : "3000"[Date - Publication])'
                    )
                if "end" in date_range:
                    search_parts.append(
                        f'("1900"[Date - Publication] : "{date_range["end"]}"[Date - Publication])'
                    )

            if "publication_type" in filters:
                pub_type = filters["publication_type"]
                search_parts.append(f'"{pub_type}"[Publication Type]')

            if "mesh_terms" in filters:
                for mesh_term in filters["mesh_terms"]:
                    search_parts.append(f'"{mesh_term}"[Mesh]')

            if "journal" in filters:
                journal = filters["journal"]
                search_parts.append(f'"{journal}"[Journal]')

            if "author" in filters:
                author = filters["author"]
                search_parts.append(f'"{author}"[Author]')

        return " AND ".join(search_parts)
