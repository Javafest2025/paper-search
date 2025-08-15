"""
Common utility functions for academic API clients.
"""

import re
from typing import Dict, Any, List, Optional, Union
from dateutil.parser import parse as parse_date
from urllib.parse import urlparse


def extract_doi(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract DOI from various possible fields in API responses.

    Args:
        data: Dictionary containing potential DOI fields

    Returns:
        Clean DOI string or None if not found
    """
    # Common DOI field names across different APIs
    doi_fields = [
        "doi",
        "DOI",
        "dc:identifier",
        "prism:doi",
        "externalIds.DOI",
        "identifiers.doi",
        "arxiv_doi",
    ]

    for field in doi_fields:
        value = _get_nested_value(data, field)
        if value:
            # Clean DOI prefixes
            clean_doi = (
                str(value)
                .replace("https://doi.org/", "")
                .replace("http://dx.doi.org/", "")
            )
            if _is_valid_doi(clean_doi):
                return clean_doi

    # Try to extract DOI from URLs
    for url_field in ["url", "link", "id", "paperId"]:
        url = _get_nested_value(data, url_field)
        if url and isinstance(url, str):
            doi_match = re.search(r"10\.\d{4,}/[^\s]+", url)
            if doi_match:
                return doi_match.group()

    return None


def extract_date(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract publication date from various possible fields.

    Args:
        data: Dictionary containing potential date fields

    Returns:
        ISO date string (YYYY-MM-DD) or None if not found
    """
    date_fields = [
        "publicationDate",
        "publishedDate",
        "date",
        "published",
        "year",
        "publicationYear",
        "datePublished",
        "created",
        "updated",
        "prism:publicationDate",
    ]

    for field in date_fields:
        value = _get_nested_value(data, field)
        if value:
            try:
                if isinstance(value, int):
                    # Handle year-only dates
                    if 1900 <= value <= 2100:
                        return f"{value}-01-01"
                elif isinstance(value, str):
                    parsed_date = parse_date(value)
                    return parsed_date.strftime("%Y-%m-%d")
            except Exception:
                continue

    return None


def clean_title(title: Union[str, List[str]]) -> str:
    """
    Clean and normalize paper titles.

    Args:
        title: Title string or list of title strings

    Returns:
        Clean title string
    """
    if isinstance(title, list):
        title = title[0] if title else ""

    if not isinstance(title, str):
        title = str(title)

    # Remove extra whitespace and newlines
    title = re.sub(r"\s+", " ", title.strip())

    # Remove common prefixes/suffixes
    title = re.sub(r"^(Title:\s*|Abstract[:\s]*)", "", title, flags=re.IGNORECASE)

    return title


def parse_authors(
    authors_data: Union[List[Dict], List[str], str],
) -> List[Dict[str, Any]]:
    """
    Parse author information from various formats.

    Args:
        authors_data: Authors in various formats (list of dicts, list of strings, or single string)

    Returns:
        List of normalized author dictionaries
    """
    if not authors_data:
        return []

    normalized_authors = []

    if isinstance(authors_data, str):
        # Single string with multiple authors
        author_names = re.split(r"[,;]|and ", authors_data)
        for name in author_names:
            name = name.strip()
            if name:
                normalized_authors.append(_create_author_dict(name))

    elif isinstance(authors_data, list):
        for author in authors_data:
            if isinstance(author, dict):
                # Author is already a dictionary
                normalized_authors.append(_normalize_author_dict(author))
            elif isinstance(author, str):
                # Author is a string name
                normalized_authors.append(_create_author_dict(author))

    return normalized_authors


def extract_urls(data: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract various URLs from paper data.

    Args:
        data: Dictionary containing potential URL fields

    Returns:
        Dictionary with paperUrl, pdfUrl, and other URLs
    """
    urls = {"paperUrl": None, "pdfUrl": None, "sourceUrl": None}

    # Extract paper URL
    for url_field in ["url", "link", "paperUrl", "id", "arxiv_url"]:
        url = _get_nested_value(data, url_field)
        if url and isinstance(url, str) and _is_valid_url(url):
            if not urls["paperUrl"]:
                urls["paperUrl"] = url
            break

    # Extract PDF URL
    pdf_fields = ["pdfUrl", "pdf", "openAccessPdf.url", "pdf_url"]
    for pdf_field in pdf_fields:
        pdf_url = _get_nested_value(data, pdf_field)
        if pdf_url and isinstance(pdf_url, str) and _is_valid_url(pdf_url):
            urls["pdfUrl"] = pdf_url
            break

    # Generate arXiv PDF URL if we have arXiv ID
    if "arxiv" in str(data).lower() and urls["paperUrl"]:
        if "arxiv.org/abs/" in urls["paperUrl"]:
            urls["pdfUrl"] = urls["paperUrl"].replace("/abs/", "/pdf/") + ".pdf"

    return urls


def extract_metrics(data: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract citation and other metrics from paper data.

    Args:
        data: Dictionary containing potential metric fields

    Returns:
        Dictionary with citation counts and other metrics
    """
    metrics = {
        "citationCount": 0,
        "referenceCount": 0,
        "influentialCitationCount": 0,
        "downloadCount": 0,
    }

    # Citation count fields
    citation_fields = [
        "citationCount",
        "cited_by_count",
        "citedByCount",
        "num_cited_by",
    ]
    for field in citation_fields:
        value = _get_nested_value(data, field)
        if isinstance(value, int):
            metrics["citationCount"] = value
            break

    # Reference count fields
    ref_fields = ["referenceCount", "reference_count", "references"]
    for field in ref_fields:
        value = _get_nested_value(data, field)
        if isinstance(value, int):
            metrics["referenceCount"] = value
            break
        elif isinstance(value, list):
            metrics["referenceCount"] = len(value)
            break

    # Influential citation count
    infl_fields = ["influentialCitationCount", "influential_citation_count"]
    for field in infl_fields:
        value = _get_nested_value(data, field)
        if isinstance(value, int):
            metrics["influentialCitationCount"] = value
            break

    return metrics


def _get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
    """Get value from nested dictionary using dot notation."""
    if "." not in field_path:
        return data.get(field_path)

    value = data
    for key in field_path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
        if value is None:
            return None
    return value


def _is_valid_doi(doi: str) -> bool:
    """Check if string is a valid DOI format."""
    doi_pattern = r"^10\.\d{4,}/[^\s]+$"
    return bool(re.match(doi_pattern, doi))


def _is_valid_url(url: str) -> bool:
    """Check if string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def _create_author_dict(name: str) -> Dict[str, Any]:
    """Create standardized author dictionary from name string."""
    return {
        "name": name.strip(),
        "orcid": None,
        "gsProfileUrl": None,
        "affiliation": None,
        "authorId": None,
    }


def _normalize_author_dict(author: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize author dictionary to standard format."""
    normalized = _create_author_dict(author.get("name", ""))

    # Map common fields
    field_mappings = {
        "orcid": ["orcid", "ORCID", "orcidId"],
        "gsProfileUrl": ["gsProfileUrl", "profileUrl", "url"],
        "affiliation": ["affiliation", "affiliations", "organization"],
        "authorId": ["authorId", "id", "scholar_id"],
    }

    for norm_field, possible_fields in field_mappings.items():
        for field in possible_fields:
            value = author.get(field)
            if value:
                normalized[norm_field] = value
                break

    return normalized
