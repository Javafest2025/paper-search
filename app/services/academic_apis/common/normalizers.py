"""
Paper data normalizers for academic API clients.
"""

from typing import Dict, Any, Optional
from .utils import (
    extract_doi,
    extract_date,
    clean_title,
    parse_authors,
    extract_urls,
    extract_metrics,
)


class PaperNormalizer:
    """
    Unified paper data normalizer for all academic APIs.
    Converts API-specific paper data to a standardized format.
    """

    @staticmethod
    def normalize(raw_paper: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Normalize paper data to standard format.

        Args:
            raw_paper: Raw paper data from API
            source: Source API name (semantic_scholar, pubmed, etc.)

        Returns:
            Normalized paper dictionary
        """
        if not raw_paper or not raw_paper.get("title"):
            return {}

        # Extract basic information
        title = clean_title(raw_paper.get("title", ""))
        doi = extract_doi(raw_paper)
        pub_date = extract_date(raw_paper)
        authors = parse_authors(raw_paper.get("authors", []))
        urls = extract_urls(raw_paper)
        metrics = extract_metrics(raw_paper)

        # Extract venue information
        venue_name = PaperNormalizer._extract_venue(raw_paper)
        publisher = PaperNormalizer._extract_publisher(raw_paper)

        # Extract abstract
        abstract = PaperNormalizer._extract_abstract(raw_paper)

        # Extract additional metadata based on source
        source_specific_data = PaperNormalizer._extract_source_specific(
            raw_paper, source
        )

        # Build normalized paper
        normalized = {
            "title": title,
            "doi": doi,
            "publicationDate": pub_date,
            "venueName": venue_name,
            "publisher": publisher,
            "peerReviewed": PaperNormalizer._is_peer_reviewed(raw_paper, source),
            "authors": authors,
            "citationCount": metrics["citationCount"],
            "referenceCount": metrics["referenceCount"],
            "influentialCitationCount": metrics["influentialCitationCount"],
            "isOpenAccess": PaperNormalizer._is_open_access(raw_paper),
            "abstract": abstract,
            "paperUrl": urls["paperUrl"],
            "pdfUrl": urls["pdfUrl"],
            "pdfContentUrl": None,  # To be filled by PDF processing service
            "source": source,
        }

        # Add source-specific fields
        normalized.update(source_specific_data)

        return normalized

    @staticmethod
    def _extract_venue(raw_paper: Dict[str, Any]) -> Optional[str]:
        """Extract venue/journal name from paper data."""
        venue_fields = [
            "venue",
            "venueName",
            "journal.name",
            "container-title",
            "journalName",
            "publication",
            "booktitle",
            "source",
        ]

        for field in venue_fields:
            value = raw_paper.get(field)
            if isinstance(value, list) and value:
                value = value[0]
            if value and isinstance(value, str):
                return value.strip()

        # Check nested journal object
        journal = raw_paper.get("journal", {})
        if isinstance(journal, dict):
            name = journal.get("name") or journal.get("title")
            if name:
                return str(name).strip()

        return None

    @staticmethod
    def _extract_publisher(raw_paper: Dict[str, Any]) -> Optional[str]:
        """Extract publisher from paper data."""
        publisher_fields = ["publisher", "journal.publisher", "publisherName"]

        for field in publisher_fields:
            if "." in field:
                # Handle nested fields
                parts = field.split(".")
                value = raw_paper
                for part in parts:
                    value = value.get(part, {}) if isinstance(value, dict) else None
                    if value is None:
                        break
            else:
                value = raw_paper.get(field)

            if value and isinstance(value, str):
                return value.strip()

        return None

    @staticmethod
    def _extract_abstract(raw_paper: Dict[str, Any]) -> Optional[str]:
        """Extract abstract from paper data (allow even short abstracts)."""
        import re
        abstract_fields = ["abstract", "summary", "description"]

        for field in abstract_fields:
            value = raw_paper.get(field)
            if value and isinstance(value, str):
                # Clean up abstract
                abstract = value.strip()
                # Remove common prefixes and HTML tags
                abstract = re.sub(r'<[^>]+>', '', abstract)  # Strip HTML tags
                abstract = abstract.replace("Abstract:", "").strip()
                # Unescape HTML entities
                import html
                abstract = html.unescape(abstract)
                if len(abstract) >= 1:
                    return abstract
        
        return None

    @staticmethod
    def _is_peer_reviewed(raw_paper: Dict[str, Any], source: str) -> bool:
        """Determine if paper is peer-reviewed based on source and metadata."""
        # ArXiv papers are preprints, not peer-reviewed
        if source == "arxiv":
            return False

        # Check for explicit peer review indicators
        if raw_paper.get("peerReviewed") is not None:
            return bool(raw_paper["peerReviewed"])

        # PubMed and most journal papers are peer-reviewed
        if source in ["pubmed", "crossref"]:
            return True

        # Check publication types
        pub_types = raw_paper.get("publicationTypes", [])
        if isinstance(pub_types, list):
            non_peer_reviewed = ["preprint", "technical report", "working paper"]
            for pub_type in pub_types:
                if any(npr in str(pub_type).lower() for npr in non_peer_reviewed):
                    return False

        # Default to True for most academic sources
        return source in ["semantic_scholar", "crossref", "pubmed"]

    @staticmethod
    def _is_open_access(raw_paper: Dict[str, Any]) -> bool:
        """Determine if paper is open access."""
        # Check explicit open access fields
        oa_fields = ["isOpenAccess", "is_oa", "openAccess"]
        for field in oa_fields:
            value = raw_paper.get(field)
            if isinstance(value, bool):
                return value

        # Check for PDF availability as proxy
        if raw_paper.get("openAccessPdf") or raw_paper.get("pdfUrl"):
            return True

        # ArXiv papers are generally open access
        if "arxiv" in str(raw_paper.get("paperUrl", "")).lower():
            return True

        return False

    @staticmethod
    def _extract_source_specific(
        raw_paper: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """Extract source-specific metadata."""
        source_data = {}

        if source == "semantic_scholar":
            source_data.update(
                {
                    "semanticScholarId": raw_paper.get("paperId"),
                    "externalIds": raw_paper.get("externalIds", {}),
                    "publicationTypes": raw_paper.get("publicationTypes", []),
                    "fieldsOfStudy": raw_paper.get("fieldsOfStudy", []),
                }
            )

        elif source == "pubmed":
            source_data.update(
                {
                    "pmid": raw_paper.get("pmid"),
                    "pmcid": raw_paper.get("pmcid"),
                    "meshTerms": raw_paper.get("meshTerms", []),
                    "keywords": raw_paper.get("keywords", []),
                    "publicationStatus": raw_paper.get("publicationStatus"),
                }
            )

        elif source == "arxiv":
            source_data.update(
                {
                    "arxivId": raw_paper.get("arxivId"),
                    "categories": raw_paper.get("categories", []),
                    "versions": raw_paper.get("versions", []),
                    "updatedDate": raw_paper.get("updatedDate"),
                }
            )

        elif source == "crossref":
            source_data.update(
                {
                    "type": raw_paper.get("type"),
                    "issn": raw_paper.get("ISSN", []),
                    "isbn": raw_paper.get("ISBN", []),
                    "license": raw_paper.get("license", []),
                    "funder": raw_paper.get("funder", []),
                }
            )

        return source_data
