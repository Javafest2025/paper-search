from typing import List, Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

MANDATORY_FIELDS = [
    "doi",
    "abstract",
    "authors",
    "publicationDate",
]


class PaperMetadataEnrichmentService:
    """Enrich papers with missing metadata using existing API clients."""

    def __init__(self, api_clients: Dict[str, Any], max_concurrent: int = 5):
        self.api_clients = api_clients
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def enrich_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich a list of papers concurrently."""
        tasks = [self._enrich_single_paper(paper) for paper in papers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        enriched = []
        for original, result in zip(papers, results):
            if isinstance(result, Exception):
                logger.debug(
                    f"Enrichment failed for paper '{original.get('title','')[:60]}': {result}"
                )
                enriched.append(original)
            else:
                enriched.append(result)
        return enriched

    async def _enrich_single_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to fill missing mandatory fields for a single paper."""
        async with self.semaphore:
            missing = self._get_missing_fields(paper)
            if not missing:
                return paper  # Already complete

            # Prefer DOI based enrichment via Crossref/Unpaywall
            doi = paper.get("doi")
            if doi and "Crossref" in self.api_clients:
                enriched = await self._fetch_from_crossref(doi)
                if enriched:
                    paper = self._merge(paper, enriched)
                    missing = self._get_missing_fields(paper)
                    if not missing:
                        return paper

            # arXiv based enrichment
            arxiv_id = paper.get("arxivId") or paper.get("arxiv_id")
            if arxiv_id and "arXiv" in self.api_clients:
                enriched = await self._safe_call(
                    self.api_clients["arXiv"].get_paper_details, arxiv_id
                )
                if enriched:
                    paper = self._merge(paper, enriched)
                    missing = self._get_missing_fields(paper)
                    if not missing:
                        return paper

            # Semantic Scholar enrichment using paperId or DOI
            ss_id = paper.get("semanticScholarId") or paper.get("paperId") or doi
            if ss_id and "Semantic Scholar" in self.api_clients:
                enriched = await self._safe_call(
                    self.api_clients["Semantic Scholar"].get_paper_details, ss_id
                )
                if enriched:
                    paper = self._merge(paper, enriched)
                    missing = self._get_missing_fields(paper)
                    if not missing:
                        return paper

            # Fallback: Crossref title search to resolve DOI and metadata
            if "Crossref" in self.api_clients and paper.get("title"):
                search_res = await self._safe_call(
                    self.api_clients["Crossref"].search_papers,
                    paper["title"],
                    1,
                    0,
                    None,
                )
                if search_res:
                    paper = self._merge(paper, search_res[0])

            return paper

    async def _fetch_from_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        if "Crossref" not in self.api_clients:
            return None
        return await self._safe_call(
            self.api_clients["Crossref"].get_paper_details, doi
        )

    @staticmethod
    async def _safe_call(func, *args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Safe call error: {e}")
            return None

    @staticmethod
    def _merge(original: Dict[str, Any], enrichment: Dict[str, Any]) -> Dict[str, Any]:
        """Merge enrichment data over the original paper without losing existing values."""
        merged = original.copy()
        for key, value in enrichment.items():
            if key not in merged or merged[key] in (None, "", [], {}):
                merged[key] = value
        return merged

    @staticmethod
    def _get_missing_fields(paper: Dict[str, Any]) -> List[str]:
        missing = []
        for field in MANDATORY_FIELDS:
            val = paper.get(field)
            if (
                val is None
                or (isinstance(val, str) and not val.strip())
                or (isinstance(val, list) and not val)
            ):
                missing.append(field)
        return missing
