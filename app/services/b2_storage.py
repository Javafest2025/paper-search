"""
Backblaze B2 Storage Service for PDF management.
Handles uploading, downloading, and managing PDF files in B2 cloud storage.
"""

import hashlib
import logging
import mimetypes
from typing import Optional, List, Dict, Any
from urllib.parse import quote
import httpx
from b2sdk.v2 import InMemoryAccountInfo, B2Api, Bucket
from app.core.config import settings

logger = logging.getLogger(__name__)


class B2StorageService:
    """
    Service for managing PDF files in Backblaze B2 cloud storage.
    Provides methods for uploading, downloading, and managing PDF files.
    """

    def __init__(self):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.bucket: Optional[Bucket] = None
        self._authorized = False

    async def initialize(self):
        """Initialize B2 connection and get bucket reference."""
        try:
            if not settings.b2_key_id or not settings.b2_application_key:
                raise ValueError("B2 credentials not configured")

            # Authorize the application
            self.api.authorize_account(
                "production", settings.b2_key_id, settings.b2_application_key
            )
            self._authorized = True

            # Get the bucket
            self.bucket = self.api.get_bucket_by_name(settings.b2_bucket_name)
            logger.info(
                f"Successfully connected to B2 bucket: {settings.b2_bucket_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize B2 storage: {str(e)}")
            raise

    def _ensure_authorized(self):
        """Ensure B2 is authorized before operations."""
        if not self._authorized or not self.bucket:
            raise RuntimeError("B2 storage not initialized. Call initialize() first.")

    def _generate_file_name(self, paper: Dict[str, Any]) -> str:
        """
        Generate a unique filename for the PDF based on paper identifiers.
        Priority: DOI > ArxivID > PubMed ID > Title hash
        """
        try:
            # Log paper fields for debugging
            logger.debug(f"Generating filename for paper with fields: {list(paper.keys())}")
            
            # Try DOI first (most reliable)
            doi = paper.get("doi") or paper.get("DOI")
            if doi and isinstance(doi, str) and doi.strip():
                # Clean DOI to make it filesystem-safe
                clean_doi = doi.replace("/", "_").replace(":", "_").replace(" ", "_")
                return f"doi_{clean_doi}.pdf"

            # Try ArXiv ID (multiple possible field names)
            arxiv_fields = ["arxivId", "arxiv_id", "arXivId", "external_ids.ArXiv", "externalIds.ArXiv"]
            for field in arxiv_fields:
                if "." in field:
                    # Handle nested fields like external_ids.ArXiv
                    parts = field.split(".")
                    value = paper
                    for part in parts:
                        if isinstance(value, dict):
                            value = value.get(part)
                        else:
                            value = None
                            break
                else:
                    value = paper.get(field)
                
                if value and isinstance(value, str) and value.strip():
                    clean_arxiv = value.replace("/", "_").replace(":", "_").replace(" ", "_")
                    # Remove common arXiv prefixes
                    clean_arxiv = clean_arxiv.replace("arXiv:", "").replace("arxiv:", "")
                    return f"arxiv_{clean_arxiv}.pdf"

            # Extract arXiv ID from paperUrl if available
            paper_url = paper.get("paperUrl") or paper.get("url")
            if paper_url and isinstance(paper_url, str) and "arxiv.org" in paper_url:
                import re
                match = re.search(r'arxiv\.org/abs/([^/?]+)', paper_url)
                if match:
                    arxiv_id = match.group(1)
                    clean_arxiv = arxiv_id.replace("/", "_").replace(":", "_").replace(" ", "_")
                    return f"arxiv_{clean_arxiv}.pdf"

            # Try PubMed ID
            pmid_fields = ["pmid", "pubmed_id", "PMID"]
            for field in pmid_fields:
                pmid = paper.get(field)
                if pmid and str(pmid).strip():
                    return f"pmid_{pmid}.pdf"

            # Try Semantic Scholar ID
            ss_fields = ["semanticScholarId", "paperId", "ss_id"]
            for field in ss_fields:
                ss_id = paper.get(field)
                if ss_id and isinstance(ss_id, str) and ss_id.strip():
                    clean_ss = ss_id.replace("/", "_").replace(":", "_").replace(" ", "_")
                    return f"ss_{clean_ss}.pdf"

            # Fallback to title hash
            title = paper.get("title", "")
            if title and isinstance(title, str) and title.strip():
                title_hash = hashlib.md5(title.encode()).hexdigest()
                return f"title_{title_hash}.pdf"

            # Last resort: random hash
            import uuid
            random_name = f"unknown_{uuid.uuid4().hex}.pdf"
            logger.warning(f"No identifiers found for paper, using random name: {random_name}")
            return random_name
            
        except Exception as e:
            logger.error(f"Error generating filename: {str(e)}")
            # Generate a safe fallback name
            import uuid
            fallback_name = f"error_{uuid.uuid4().hex}.pdf"
            return fallback_name

    async def upload_pdf(
        self, paper: Dict[str, Any], pdf_content: bytes
    ) -> Optional[str]:
        """
        Upload PDF content to B2 and return the download URL.

        Args:
            paper: Paper metadata dictionary
            pdf_content: PDF file content as bytes

        Returns:
            Download URL if successful, None otherwise
        """
        self._ensure_authorized()

        try:
            # Debug logging
            logger.debug(f"Uploading PDF for paper: {paper.get('title', 'Unknown')[:50]}")
            
            file_name = self._generate_file_name(paper)
            logger.debug(f"Generated filename: {file_name}")
            
            # Check if file already exists
            existing_url = await self.get_pdf_url(paper)
            if existing_url:
                logger.info(
                    f"PDF already exists for {file_name}, returning existing URL"
                )
                return existing_url

            # Validate PDF content
            if not pdf_content or len(pdf_content) < 1024:  # At least 1KB
                logger.warning(f"Invalid PDF content for {file_name}")
                return None

            # Prepare metadata safely
            paper_title = paper.get("title", "")
            if paper_title and isinstance(paper_title, str):
                paper_title = paper_title[:250]  # B2 has limits on metadata
            else:
                paper_title = ""
                
            paper_doi = paper.get("doi", "")
            if paper_doi and isinstance(paper_doi, str):
                paper_doi = paper_doi[:250]
            else:
                paper_doi = ""

            # Upload the file
            logger.debug(f"Starting B2 upload for {file_name}")
            file_info = self.bucket.upload_bytes(
                pdf_content,
                file_name,
                content_type="application/pdf",
                file_infos={
                    "paper_title": paper_title,
                    "paper_doi": paper_doi,
                    "upload_source": "scholar_ai"
                }
            )

            # Generate download URL
            if not file_info or not hasattr(file_info, 'id_'):
                logger.error(f"Invalid file_info object returned from B2 upload")
                return None
                
            download_url = self.api.get_download_url_for_fileid(file_info.id_)
            logger.info(f"Successfully uploaded PDF: {file_name} -> {download_url}")

            return download_url

        except Exception as e:
            logger.error(f"Failed to upload PDF: {str(e)}")
            logger.error(f"Paper data keys: {list(paper.keys()) if isinstance(paper, dict) else 'Not a dict'}")
            return None

    async def get_pdf_url(self, paper: Dict[str, Any]) -> Optional[str]:
        """
        Get the download URL for a PDF file if it exists in storage.

        Args:
            paper: Paper metadata dictionary

        Returns:
            Download URL if file exists, None otherwise
        """
        self._ensure_authorized()

        try:
            file_name = self._generate_file_name(paper)

            # Check if file exists
            file_versions = self.bucket.ls(file_name, latest_only=True, recursive=False)

            for file_version, _ in file_versions:
                if file_version.file_name == file_name:
                    download_url = self.api.get_download_url_for_fileid(
                        file_version.id_
                    )
                    return download_url

            return None

        except Exception as e:
            logger.error(f"Failed to get PDF URL: {str(e)}")
            return None

    async def delete_pdf(self, paper: Dict[str, Any]) -> bool:
        """
        Delete a PDF file from storage.

        Args:
            paper: Paper metadata dictionary

        Returns:
            True if deleted successfully, False otherwise
        """
        self._ensure_authorized()

        try:
            file_name = self._generate_file_name(paper)

            # Find and delete the file
            file_versions = self.bucket.ls(file_name, latest_only=True, recursive=False)

            for file_version, _ in file_versions:
                if file_version.file_name == file_name:
                    self.api.delete_file_version(
                        file_version.id_, file_version.file_name
                    )
                    logger.info(f"Deleted PDF: {file_name}")
                    return True

            logger.warning(f"PDF not found for deletion: {file_name}")
            return False

        except Exception as e:
            logger.error(f"Failed to delete PDF: {str(e)}")
            return False

    async def list_all_files(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        List all PDF files in the bucket.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of file information dictionaries
        """
        self._ensure_authorized()

        try:
            files = []
            count = 0

            for file_version, _ in self.bucket.ls(recursive=True):
                if count >= limit:
                    break

                files.append(
                    {
                        "file_name": file_version.file_name,
                        "file_id": file_version.id_,
                        "size": file_version.size,
                        "upload_timestamp": file_version.upload_timestamp,
                        "content_type": file_version.content_type,
                        "download_url": self.api.get_download_url_for_fileid(
                            file_version.id_
                        ),
                    }
                )
                count += 1

            logger.info(f"Listed {len(files)} files from B2 storage")
            return files

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []

    async def delete_all_files(self) -> Dict[str, int]:
        """
        Delete all files in the bucket. Use with caution!

        Returns:
            Dictionary with deletion statistics
        """
        self._ensure_authorized()

        try:
            deleted_count = 0
            error_count = 0

            for file_version, _ in self.bucket.ls(recursive=True):
                try:
                    self.api.delete_file_version(
                        file_version.id_, file_version.file_name
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {file_version.file_name}: {str(e)}")
                    error_count += 1

            stats = {
                "deleted": deleted_count,
                "errors": error_count,
                "total_processed": deleted_count + error_count,
            }

            logger.info(f"Bulk deletion completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to delete all files: {str(e)}")
            return {"deleted": 0, "errors": 1, "total_processed": 1}

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        self._ensure_authorized()

        try:
            total_files = 0
            total_size = 0
            file_types = {}

            for file_version, _ in self.bucket.ls(recursive=True):
                total_files += 1
                total_size += file_version.size

                # Count by file extension
                file_ext = file_version.file_name.split(".")[-1].lower()
                file_types[file_ext] = file_types.get(file_ext, 0) + 1

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "bucket_name": settings.b2_bucket_name,
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "file_types": {},
                "bucket_name": settings.b2_bucket_name,
                "error": str(e),
            }


# Global service instance
b2_storage = B2StorageService()
