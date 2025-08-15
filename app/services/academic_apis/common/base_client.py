"""
Base client for academic API interactions with sophisticated error handling,
rate limiting, and response processing.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
# from ratelimit import limits, sleep_and_retry  # REMOVED: Conflicted with tenacity
import time

from .exceptions import RateLimitError, APIError
from .normalizers import PaperNormalizer

logger = logging.getLogger(__name__)


class BaseAcademicClient(ABC):
    """
    Base class for all academic API clients providing:
    - Rate limiting
    - Error handling and retries
    - Response parsing
    - Caching mechanisms
    - Request standardization
    - Unified paper normalization
    """

    def __init__(
        self,
        base_url: str,
        rate_limit_calls: int = 100,
        rate_limit_period: int = 60,
        timeout: int = 30,
        max_retries: int = 3,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = api_key

        # Set source name based on class name
        self.source_name = self._get_source_name()

        # Initialize HTTP client with proper headers
        self.headers = {
            "User-Agent": "ScholarAI/1.0 (https://scholarai.dev; mailto:contact@scholarai.dev)",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.api_key:
            self.headers.update(self._get_auth_headers())

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self.headers,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

        # Cache for responses (simple in-memory cache)
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour TTL

    def _get_source_name(self) -> str:
        """Get source name from class name."""
        class_name = self.__class__.__name__.lower()
        if "semantic" in class_name:
            return "semantic_scholar"
        elif "pubmed" in class_name:
            return "pubmed"
        elif "arxiv" in class_name:
            return "arxiv"
        elif "crossref" in class_name:
            return "crossref"
        elif "openalex" in class_name:
            return "openalex"
        elif "core" in class_name:
            return "core"
        elif "unpaywall" in class_name:
            return "unpaywall"
        elif "europepmc" in class_name:
            return "europepmc"
        elif "dblp" in class_name:
            return "dblp"
        elif "biorxiv" in class_name:
            return "biorxiv"
        elif "doaj" in class_name:
            return "doaj"
        elif "base" in class_name:
            return "base"
        else:
            return "unknown"

    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers specific to the API"""
        pass

    @abstractmethod
    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for papers using the API"""
        pass

    @abstractmethod
    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific paper"""
        pass

    @abstractmethod
    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get papers that cite the given paper"""
        pass

    @abstractmethod
    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get papers referenced by the given paper"""
        pass

    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize paper data using the unified normalizer.

        Args:
            raw_paper: Raw paper data from API

        Returns:
            Normalized paper dictionary
        """
        return PaperNormalizer.normalize(raw_paper, self.source_name)

    def normalize_papers(
        self, raw_papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Normalize multiple papers.

        Args:
            raw_papers: List of raw paper data from API

        Returns:
            List of normalized paper dictionaries
        """
        normalized_papers = []
        for paper in raw_papers:
            normalized = self.normalize_paper(paper)
            if normalized:
                normalized_papers.append(normalized)
        return normalized_papers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (httpx.RequestError, httpx.HTTPStatusError, RateLimitError)
        ),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting, retries, and caching
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = f"{method}:{url}:{str(params)}:{str(data)}" if use_cache else None

        # Check cache first
        if cache_key and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for {url}")
                return cached_data

        try:
            logger.debug(f"Making {method} request to {url}")

            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2))  # Minimal wait for testing
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                raise RateLimitError("Rate limit exceeded")

            # Handle other HTTP errors
            response.raise_for_status()

            # Parse response
            try:
                result = response.json()
            except Exception:
                # Some APIs might return XML or plain text
                result = {"content": response.text, "status_code": response.status_code}

            # Cache successful responses
            if cache_key and response.status_code == 200:
                self._cache[cache_key] = (result, time.time())

            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for {url}: {e.response.text}"
            )
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {str(e)}")
            raise APIError(f"Request failed: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close the HTTP client"""
        if hasattr(self, "client"):
            await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, "client"):
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if not loop.is_closed():
                    loop.create_task(self.client.aclose())
            except Exception:
                pass
