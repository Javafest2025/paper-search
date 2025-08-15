"""
Common utilities and base classes for academic API clients.
"""

from .base_client import BaseAcademicClient
from .normalizers import PaperNormalizer
from .utils import (
    extract_doi,
    extract_date,
    clean_title,
    parse_authors,
    extract_urls,
)
from .exceptions import (
    RateLimitError,
    APIError,
    InvalidResponseError,
)

__all__ = [
    "BaseAcademicClient",
    "PaperNormalizer",
    "extract_doi",
    "extract_date",
    "clean_title",
    "parse_authors",
    "extract_urls",
    "RateLimitError",
    "APIError",
    "InvalidResponseError",
]
