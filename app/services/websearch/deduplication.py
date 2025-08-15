"""
Paper deduplication service for academic search
"""

import hashlib
import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)


class PaperDeduplicationService:
    """
    Service for intelligent paper deduplication across multiple academic sources.

    Uses multiple identifiers (DOI, title hash, arXiv ID, etc.) to detect duplicates
    with high accuracy while maintaining paper uniqueness.
    """

    def __init__(self):
        self.seen_papers: Set[str] = set()
        self.added_papers: List[Dict[str, Any]] = []

    def reset(self):
        """Reset deduplication state for new search session"""
        self.seen_papers.clear()
        self.added_papers.clear()

    def add_papers(self, papers: List[Dict[str, Any]]) -> int:
        """
        Add papers with deduplication.

        Args:
            papers: List of paper dictionaries to add

        Returns:
            Number of unique papers added (after deduplication)
        """
        added_count = 0

        for paper in papers:
            if self._is_unique_paper(paper):
                self._mark_paper_as_seen(paper)
                self.added_papers.append(paper)
                added_count += 1

        logger.info(
            f"➕ Added {added_count} unique papers (deduplicated {len(papers) - added_count})"
        )
        return added_count

    def get_papers(self) -> List[Dict[str, Any]]:
        """Get all unique papers collected so far"""
        return self.added_papers.copy()

    def get_paper_count(self) -> int:
        """Get count of unique papers collected"""
        return len(self.added_papers)

    def _is_unique_paper(self, paper: Dict[str, Any]) -> bool:
        """Check if paper is unique based on its identifiers"""
        identifiers = self._generate_paper_identifiers(paper)

        for identifier in identifiers:
            if identifier in self.seen_papers:
                return False

        return True

    def _mark_paper_as_seen(self, paper: Dict[str, Any]):
        """Mark paper as seen by adding all its identifiers to seen set"""
        identifiers = self._generate_paper_identifiers(paper)
        for identifier in identifiers:
            self.seen_papers.add(identifier)

    def _generate_paper_identifiers(self, paper: Dict[str, Any]) -> List[str]:
        """
        Generate multiple identifiers for a paper to enable robust deduplication.

        Uses various paper metadata including DOI, title hash, arXiv ID, PubMed ID,
        and Semantic Scholar ID for comprehensive duplicate detection.
        """
        identifiers = []

        # DOI - most reliable identifier
        doi = paper.get("doi") or paper.get("DOI")
        if doi:
            normalized_doi = doi.lower().strip()
            identifiers.append(f"doi:{normalized_doi}")

        # Title hash - for papers without DOI
        title = paper.get("title", "").strip()
        if title:
            # Normalize title: lowercase, remove extra spaces, common punctuation
            normalized_title = self._normalize_title(title)
            title_hash = hashlib.md5(normalized_title.encode()).hexdigest()
            identifiers.append(f"title:{title_hash}")

        # arXiv ID
        arxiv_id = paper.get("arxiv_id") or paper.get("arXivId")
        if arxiv_id:
            identifiers.append(f"arxiv:{arxiv_id.strip()}")

        # PubMed ID
        pubmed_id = paper.get("pubmed_id") or paper.get("pmid")
        if pubmed_id:
            identifiers.append(f"pubmed:{pubmed_id}")

        # Semantic Scholar ID
        ss_id = paper.get("paperId") or paper.get("semanticScholarId")
        if ss_id:
            identifiers.append(f"ss:{ss_id}")

        # URL-based identifiers for additional matching
        url = paper.get("url") or paper.get("pdf_url")
        if url:
            url_hash = hashlib.md5(url.lower().strip().encode()).hexdigest()
            identifiers.append(f"url:{url_hash}")

        return identifiers

    def _normalize_title(self, title: str) -> str:
        """
        Normalize title for consistent hashing.

        Removes common variations that might cause false negatives in deduplication.
        """
        import re

        # Convert to lowercase
        normalized = title.lower()

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove common punctuation at the end
        normalized = re.sub(r"[.!?]+$", "", normalized)

        # Remove quotes and brackets
        normalized = re.sub(r'["\'\[\](){}]', "", normalized)

        return normalized.strip()

    def get_deduplication_stats(self) -> Dict[str, int]:
        """Get statistics about deduplication process"""
        return {
            "unique_papers": len(self.added_papers),
            "total_identifiers": len(self.seen_papers),
            "avg_identifiers_per_paper": len(self.seen_papers)
            / max(len(self.added_papers), 1),
        }
