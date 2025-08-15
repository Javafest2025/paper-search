"""
Feed response parser for academic APIs.
"""

import feedparser
from typing import Dict, Any, List, Optional


class FeedParser:
    """
    Unified feed parser for academic APIs that return Atom/RSS feeds.
    """

    @staticmethod
    def parse_arxiv_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse ArXiv feed entry to dictionary.

        Args:
            entry: Feedparser entry object

        Returns:
            Dictionary with paper data
        """
        paper = {}

        # Extract arXiv ID and URLs
        if hasattr(entry, "id") and entry.id:
            arxiv_id = entry.id.split("/")[-1]  # Extract ID from URL
            paper["arxivId"] = arxiv_id
            paper["paperUrl"] = entry.id
            paper["pdfUrl"] = entry.id.replace("/abs/", "/pdf/") + ".pdf"

        # Extract title
        if hasattr(entry, "title") and entry.title:
            paper["title"] = entry.title.strip()

        # Extract summary/abstract
        if hasattr(entry, "summary") and entry.summary:
            paper["abstract"] = entry.summary.strip()

        # Extract authors
        paper["authors"] = FeedParser._extract_arxiv_authors(entry)

        # Extract categories/subjects
        paper["categories"] = FeedParser._extract_arxiv_categories(entry)

        # Extract dates
        if hasattr(entry, "published"):
            paper["published"] = entry.published

        if hasattr(entry, "updated"):
            paper["updated"] = entry.updated

        # Extract DOI if available
        if hasattr(entry, "arxiv_doi") and entry.arxiv_doi:
            paper["doi"] = entry.arxiv_doi

        # Extract links
        paper["links"] = FeedParser._extract_arxiv_links(entry)

        return paper

    @staticmethod
    def _extract_arxiv_authors(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract author information from ArXiv entry."""
        authors = []

        if hasattr(entry, "authors"):
            for author in entry.authors:
                author_name = (
                    author.get("name", "") if isinstance(author, dict) else str(author)
                )
                if author_name:
                    authors.append(
                        {
                            "name": author_name.strip(),
                            "orcid": None,
                            "gsProfileUrl": None,
                            "affiliation": None,
                            "authorId": None,
                        }
                    )

        return authors

    @staticmethod
    def _extract_arxiv_categories(entry: Dict[str, Any]) -> List[str]:
        """Extract categories/subjects from ArXiv entry."""
        categories = []

        if hasattr(entry, "tags"):
            for tag in entry.tags:
                if isinstance(tag, dict) and "term" in tag:
                    categories.append(tag["term"])
                elif isinstance(tag, str):
                    categories.append(tag)

        return categories

    @staticmethod
    def _extract_arxiv_links(entry: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract links from ArXiv entry."""
        links = []

        if hasattr(entry, "links"):
            for link in entry.links:
                if isinstance(link, dict):
                    links.append(
                        {
                            "href": link.get("href", ""),
                            "type": link.get("type", ""),
                            "title": link.get("title", ""),
                        }
                    )

        return links

    @staticmethod
    def parse_feed_content(content: str) -> List[Dict[str, Any]]:
        """
        Parse feed content and return list of entries.

        Args:
            content: Raw feed content (XML/Atom)

        Returns:
            List of parsed entries
        """
        try:
            feed = feedparser.parse(content)
            entries = []

            for entry in feed.entries:
                # Determine feed type and parse accordingly
                if "arxiv.org" in getattr(entry, "id", ""):
                    parsed_entry = FeedParser.parse_arxiv_entry(entry)
                else:
                    # Generic feed parsing
                    parsed_entry = FeedParser._parse_generic_entry(entry)

                if parsed_entry:
                    entries.append(parsed_entry)

            return entries

        except Exception as e:
            # Log error but don't crash
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error parsing feed content: {str(e)}")
            return []

    @staticmethod
    def _parse_generic_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generic feed entry."""
        paper = {}

        # Basic fields
        if hasattr(entry, "title"):
            paper["title"] = entry.title

        if hasattr(entry, "summary"):
            paper["abstract"] = entry.summary
        elif hasattr(entry, "description"):
            paper["abstract"] = entry.description

        if hasattr(entry, "link"):
            paper["paperUrl"] = entry.link

        if hasattr(entry, "published"):
            paper["published"] = entry.published

        if hasattr(entry, "authors"):
            paper["authors"] = [
                {"name": author if isinstance(author, str) else author.get("name", "")}
                for author in entry.authors
            ]

        return paper
