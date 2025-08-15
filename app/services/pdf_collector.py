"""
Enhanced PDF Collection Service with multiple techniques for obtaining PDFs.
Uses various methods including direct downloads, web scraping, and alternative URL patterns.
"""

import logging
import re
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PDFCollectorService:
    """
    Enhanced service for collecting PDFs using multiple techniques.
    Attempts various methods to obtain PDF content when direct URLs aren't available.
    """

    def __init__(self):
        self.timeout = 30.0
        self.max_size = 50 * 1024 * 1024  # 50MB
        self.min_size = 1024  # 1KB

        # Common PDF URL patterns for different platforms
        self.url_patterns = {
            "arxiv": [r"arxiv\.org/abs/(\d+\.\d+)", r"arxiv\.org/pdf/(\d+\.\d+)"],
            "biorxiv": [
                r"biorxiv\.org/content/(.+?)(?:v\d+)?(?:\.full)?(?:\.pdf)?$",
                r"biorxiv\.org/content/early/\d+/\d+/\d+/(.+?)(?:\.full)?$",
            ],
            "pubmed": [
                r"ncbi\.nlm\.nih\.gov/pmc/articles/PMC(\d+)",
                r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)",
            ],
            "doi": [r"doi\.org/(.+)", r"dx\.doi\.org/(.+)"],
        }

    async def collect_pdf(self, paper: Dict[str, Any]) -> Optional[bytes]:
        """
        Main method to collect PDF using multiple techniques.

        Args:
            paper: Paper metadata dictionary

        Returns:
            PDF content as bytes or None if failed
        """
        logger.info(f"Collecting PDF for: {paper.get('title', 'Unknown')[:50]}...")

        # Method 1: Direct PDF URL
        pdf_content = await self._try_direct_urls(paper)
        if pdf_content:
            logger.info("✅ PDF collected via direct URL")
            return pdf_content

        # Method 2: Generate alternative URLs
        pdf_content = await self._try_alternative_urls(paper)
        if pdf_content:
            logger.info("✅ PDF collected via alternative URL")
            return pdf_content

        # Method 3: Web scraping
        pdf_content = await self._try_web_scraping(paper)
        if pdf_content:
            logger.info("✅ PDF collected via web scraping")
            return pdf_content

        # Method 4: Platform-specific methods
        pdf_content = await self._try_platform_specific(paper)
        if pdf_content:
            logger.info("✅ PDF collected via platform-specific method")
            return pdf_content

        logger.warning(
            f"❌ Failed to collect PDF for: {paper.get('title', 'Unknown')[:50]}"
        )
        return None

    async def _try_direct_urls(self, paper: Dict[str, Any]) -> Optional[bytes]:
        """Try downloading from direct PDF URLs in paper metadata."""
        urls_to_try = []

        # Collect all possible PDF URLs from paper metadata
        for field in [
            "pdfUrl",
            "pdf_url",
            "pdfLink",
            "pdf_link",
            "fullTextUrl",
            "fulltext_url",
        ]:
            url = paper.get(field)
            if url and isinstance(url, str):
                urls_to_try.append(url)

        # Also check in links array
        links = paper.get("links", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    url = link.get("url") or link.get("href")
                    if url and (
                        "pdf" in url.lower() or link.get("type", "").lower() == "pdf"
                    ):
                        urls_to_try.append(url)

        # Try each URL
        for url in urls_to_try:
            pdf_content = await self._download_pdf(url)
            if pdf_content:
                return pdf_content

        return None

    async def _try_alternative_urls(self, paper: Dict[str, Any]) -> Optional[bytes]:
        """Generate and try alternative PDF URLs based on paper metadata."""
        alternative_urls = []

        # ArXiv alternatives
        arxiv_id = self._extract_arxiv_id(paper)
        if arxiv_id:
            alternative_urls.extend(
                [
                    f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    f"https://arxiv.org/pdf/{arxiv_id}v1.pdf",
                    f"https://arxiv.org/pdf/{arxiv_id}v2.pdf",
                    f"https://export.arxiv.org/pdf/{arxiv_id}.pdf",
                ]
            )

        # bioRxiv alternatives
        biorxiv_id = self._extract_biorxiv_id(paper)
        if biorxiv_id:
            alternative_urls.extend(
                [
                    f"https://www.biorxiv.org/content/biorxiv/early/{biorxiv_id}.full.pdf",
                    f"https://www.biorxiv.org/content/{biorxiv_id}.full.pdf",
                    f"https://biorxiv.org/content/biorxiv/early/{biorxiv_id}.full.pdf",
                ]
            )

        # PMC alternatives
        pmc_id = self._extract_pmc_id(paper)
        if pmc_id:
            alternative_urls.extend(
                [
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/main.pdf",
                ]
            )

        # DOI-based alternatives
        doi = paper.get("doi")
        if doi:
            # Try common publisher patterns
            if "nature.com" in paper.get("url", ""):
                alternative_urls.append(f"https://www.nature.com/articles/{doi}.pdf")
            elif "springer.com" in paper.get("url", ""):
                alternative_urls.append(
                    f"https://link.springer.com/content/pdf/{doi}.pdf"
                )
            elif "ieee.org" in paper.get("url", ""):
                alternative_urls.append(
                    f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={doi.split('/')[-1]}"
                )

        # Try each alternative URL
        for url in alternative_urls:
            pdf_content = await self._download_pdf(url)
            if pdf_content:
                return pdf_content

        return None

    async def _try_web_scraping(self, paper: Dict[str, Any]) -> Optional[bytes]:
        """Try to find PDF links by scraping the paper's webpage."""
        paper_url = paper.get("url") or paper.get("link")
        if not paper_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(paper_url, follow_redirects=True)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")

                # Look for PDF links
                pdf_links = []

                # Method 1: Direct PDF links
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.lower().endswith(".pdf") or "pdf" in href.lower():
                        full_url = urljoin(paper_url, href)
                        pdf_links.append(full_url)

                # Method 2: Look for common PDF button classes/IDs
                pdf_selectors = [
                    'a[href*="pdf"]',
                    ".pdf-download",
                    ".download-pdf",
                    "#pdf-link",
                    'a[title*="PDF"]',
                    'a[aria-label*="PDF"]',
                    ".btn-pdf",
                    ".pdf-btn",
                ]

                for selector in pdf_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get("href")
                        if href:
                            full_url = urljoin(paper_url, href)
                            pdf_links.append(full_url)

                # Method 3: Look for meta tags with PDF URLs
                for meta in soup.find_all("meta"):
                    content = meta.get("content", "")
                    if content and content.lower().endswith(".pdf"):
                        full_url = urljoin(paper_url, content)
                        pdf_links.append(full_url)

                # Try each found PDF link
                for pdf_url in set(pdf_links):  # Remove duplicates
                    pdf_content = await self._download_pdf(pdf_url)
                    if pdf_content:
                        return pdf_content

        except Exception as e:
            logger.warning(f"Web scraping failed for {paper_url}: {str(e)}")

        return None

    async def _try_platform_specific(self, paper: Dict[str, Any]) -> Optional[bytes]:
        """Try platform-specific PDF collection methods."""

        # ArXiv specific
        arxiv_id = self._extract_arxiv_id(paper)
        if arxiv_id:
            pdf_content = await self._collect_arxiv_pdf(arxiv_id)
            if pdf_content:
                return pdf_content

        # bioRxiv specific
        biorxiv_id = self._extract_biorxiv_id(paper)
        if biorxiv_id:
            pdf_content = await self._collect_biorxiv_pdf(biorxiv_id)
            if pdf_content:
                return pdf_content

        # PMC specific
        pmc_id = self._extract_pmc_id(paper)
        if pmc_id:
            pdf_content = await self._collect_pmc_pdf(pmc_id)
            if pdf_content:
                return pdf_content

        return None

    async def _collect_arxiv_pdf(self, arxiv_id: str) -> Optional[bytes]:
        """Collect PDF from ArXiv using multiple strategies."""
        urls_to_try = [
            f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            f"https://arxiv.org/pdf/{arxiv_id}v1.pdf",
            f"https://arxiv.org/pdf/{arxiv_id}v2.pdf",
            f"https://arxiv.org/pdf/{arxiv_id}v3.pdf",
            f"https://export.arxiv.org/pdf/{arxiv_id}.pdf",
        ]

        for url in urls_to_try:
            pdf_content = await self._download_pdf(url)
            if pdf_content:
                return pdf_content

        return None

    async def _collect_biorxiv_pdf(self, biorxiv_id: str) -> Optional[bytes]:
        """Collect PDF from bioRxiv using multiple strategies."""
        # First try to get the full bioRxiv URL structure
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get the abstract page to find the correct PDF URL
                abstract_url = f"https://www.biorxiv.org/content/{biorxiv_id}"
                response = await client.get(abstract_url, follow_redirects=True)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")

                # Look for PDF link in the page
                pdf_link = soup.find("a", {"class": "btn-pdf"}) or soup.find(
                    "a", href=re.compile(r"\.pdf$")
                )
                if pdf_link and pdf_link.get("href"):
                    pdf_url = urljoin(abstract_url, pdf_link["href"])
                    pdf_content = await self._download_pdf(pdf_url)
                    if pdf_content:
                        return pdf_content

        except Exception as e:
            logger.warning(f"bioRxiv specific collection failed: {str(e)}")

        return None

    async def _collect_pmc_pdf(self, pmc_id: str) -> Optional[bytes]:
        """Collect PDF from PMC using multiple strategies."""
        urls_to_try = [
            f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
            f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/main.pdf",
            f"https://europepmc.org/articles/PMC{pmc_id}?pdf=render",
        ]

        for url in urls_to_try:
            pdf_content = await self._download_pdf(url)
            if pdf_content:
                return pdf_content

        return None

    async def _download_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF content from a URL with validation."""
        if not url or not isinstance(url, str):
            return None

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            ) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                    # Sometimes PDFs are served with generic content types
                    if not response.content.startswith(b"%PDF"):
                        return None

                # Check size
                content_length = len(response.content)
                if content_length < self.min_size:
                    logger.warning(f"PDF too small: {content_length} bytes from {url}")
                    return None

                if content_length > self.max_size:
                    logger.warning(f"PDF too large: {content_length} bytes from {url}")
                    return None

                # Verify it's actually a PDF
                if not response.content.startswith(b"%PDF"):
                    logger.warning(f"Content is not a valid PDF from {url}")
                    return None

                logger.info(f"Downloaded PDF: {content_length} bytes from {url}")
                return response.content

        except Exception as e:
            logger.debug(f"Failed to download PDF from {url}: {str(e)}")
            return None

    def _extract_arxiv_id(self, paper: Dict[str, Any]) -> Optional[str]:
        """Extract ArXiv ID from paper metadata."""
        # Check direct ArXiv ID field
        arxiv_id = paper.get("arxivId") or paper.get("arxiv_id")
        if arxiv_id:
            return arxiv_id.replace("arXiv:", "")

        # Extract from URLs
        for field in ["url", "link", "pdfUrl", "pdf_url"]:
            url = paper.get(field, "")
            if isinstance(url, str) and "arxiv.org" in url:
                for pattern in self.url_patterns["arxiv"]:
                    match = re.search(pattern, url)
                    if match:
                        return match.group(1)

        return None

    def _extract_biorxiv_id(self, paper: Dict[str, Any]) -> Optional[str]:
        """Extract bioRxiv ID from paper metadata."""
        for field in ["url", "link", "pdfUrl", "pdf_url"]:
            url = paper.get(field, "")
            if isinstance(url, str) and "biorxiv.org" in url:
                for pattern in self.url_patterns["biorxiv"]:
                    match = re.search(pattern, url)
                    if match:
                        return match.group(1)

        return None

    def _extract_pmc_id(self, paper: Dict[str, Any]) -> Optional[str]:
        """Extract PMC ID from paper metadata."""
        # Check direct PMC ID field
        pmc_id = paper.get("pmcId") or paper.get("pmc_id")
        if pmc_id:
            return pmc_id.replace("PMC", "")

        # Extract from URLs
        for field in ["url", "link", "pdfUrl", "pdf_url"]:
            url = paper.get(field, "")
            if isinstance(url, str) and ("pmc" in url or "pubmed" in url):
                for pattern in self.url_patterns["pubmed"]:
                    match = re.search(pattern, url)
                    if match:
                        return match.group(1)

        return None


# Global service instance
pdf_collector = PDFCollectorService()
