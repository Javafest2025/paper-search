"""
arXiv API Test Endpoint

This endpoint allows testing the arXiv API specifically with the full workflow
(excluding PDF processing and storage) to match the RabbitMQ response structure.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.academic_apis.clients.arxiv_client import ArxivClient
from app.services.websearch.deduplication import PaperDeduplicationService
from app.services.websearch.filter_service import SearchFilterService
from app.services.websearch.ai_refinement import AIQueryRefinementService
from app.services.websearch.metadata_enrichment import PaperMetadataEnrichmentService
from app.services.websearch.config import SearchConfig, AIConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ArxivTestRequest(BaseModel):
    """Request model for arXiv API testing (same as RabbitMQ except no projectId)"""
    queryTerms: List[str] = Field(..., description="Search terms")
    domain: str = Field(default="Computer Science", description="Research domain")
    batchSize: int = Field(default=10, description="Target number of papers")
    correlationId: Optional[str] = Field(default=None, description="Correlation ID for tracking")


class ArxivTestResponse(BaseModel):
    """Response model matching RabbitMQ response structure"""
    projectId: Optional[str] = None
    correlationId: Optional[str] = None
    papers: List[Dict[str, Any]] = Field(default_factory=list)
    batchSize: int = 0
    queryTerms: List[str] = Field(default_factory=list)
    domain: str = "Computer Science"
    status: str = "COMPLETED"
    searchStrategy: str = "arxiv_only"
    totalSourcesUsed: int = 1
    aiEnhanced: bool = False
    searchRounds: int = 1
    deduplicationStats: Dict[str, Any] = Field(default_factory=dict)


class ArxivTestService:
    """Service for testing arXiv API with full workflow"""
    
    def __init__(self):
        self.arxiv_client = ArxivClient()
        self.deduplication_service = PaperDeduplicationService()
        self.filter_service = SearchFilterService(recent_years_filter=5)
        self.enrichment_service = PaperMetadataEnrichmentService({"arXiv": self.arxiv_client})
        
        # AI service (optional)
        self.ai_service = None
        self.ai_config = AIConfig()
        if self.ai_config.api_key:
            self.ai_service = AIQueryRefinementService(
                api_key=self.ai_config.api_key,
                model_name=self.ai_config.model_name
            )
    
    async def initialize(self):
        """Initialize the service"""
        if self.ai_service:
            await self.ai_service.initialize()
        logger.info("✅ ArxivTestService initialized")
    
    async def search_papers(self, request: ArxivTestRequest) -> ArxivTestResponse:
        """
        Search papers using arXiv with full workflow
        
        Args:
            request: Search request parameters
            
        Returns:
            Response matching RabbitMQ structure
        """
        search_start_time = datetime.now()
        logger.info(f"🔍 Starting arXiv search: {request.queryTerms}")
        
        # Reset deduplication service
        self.deduplication_service.reset()
        
        # Build search query
        search_query = " ".join(request.queryTerms)
        
        # Search arXiv
        papers = await self.arxiv_client.search_papers(
            query=search_query,
            limit=request.batchSize * 2,  # Get more to account for filtering
            filters=self.filter_service.build_filters("arXiv", request.domain, search_query)
        )
        
        # Add source metadata
        for paper in papers:
            paper["source"] = "arXiv"
        
        # Add papers with deduplication
        added_count = self.deduplication_service.add_papers(papers)
        unique_papers = self.deduplication_service.get_papers()
        
        # Enrich metadata
        enriched_papers = await self.enrichment_service.enrich_papers(unique_papers)
        
        # Rank papers by relevance
        ranked_papers = self._rank_papers(enriched_papers, request.queryTerms)
        
        # Limit to requested batch size
        final_papers = ranked_papers[:request.batchSize]
        
        # Get statistics
        dedup_stats = self.deduplication_service.get_deduplication_stats()
        total_papers_found = len(papers)
        unique_papers_found = len(final_papers)
        duplicates_removed = total_papers_found - unique_papers_found
        
        search_duration = (datetime.now() - search_start_time).total_seconds()
        logger.info(f"✅ ArXiv search completed in {search_duration:.1f}s: {len(final_papers)} papers")
        
        return ArxivTestResponse(
            projectId=None,  # Not needed for testing
            correlationId=request.correlationId,
            papers=final_papers,
            batchSize=len(final_papers),
            queryTerms=request.queryTerms,
            domain=request.domain,
            status="COMPLETED",
            searchStrategy="arxiv_only",
            totalSourcesUsed=1,
            aiEnhanced=False,  # No AI refinement for single source
            searchRounds=1,
            deduplicationStats={
                "unique_papers": dedup_stats.get("unique_papers", 0),
                "total_identifiers": dedup_stats.get("total_identifiers", 0),
                "duplicates_removed": duplicates_removed
            }
        )
    
    def _rank_papers(self, papers: List[Dict[str, Any]], query_terms: List[str]) -> List[Dict[str, Any]]:
        """Rank papers by relevance to query terms"""
        if not papers:
            return papers
        
        terms = [t.lower() for t in query_terms]
        
        def score(paper):
            text = ((paper.get("title") or "") + " " + (paper.get("abstract") or "")).lower()
            return sum(text.count(term) for term in terms)
        
        return sorted(papers, key=score, reverse=True)
    
    async def close(self):
        """Clean up resources"""
        if self.ai_service:
            await self.ai_service.close()
        logger.info("🔒 ArxivTestService closed")


# Global service instance
arxiv_test_service = ArxivTestService()


@router.post("/test", response_model=ArxivTestResponse)
async def test_arxiv_api(request: ArxivTestRequest):
    """
    Test arXiv API with full workflow
    
    This endpoint tests the arXiv API specifically, running the complete
    workflow including deduplication, filtering, enrichment, and ranking,
    but excluding PDF processing and storage.
    
    The response structure matches what would be sent via RabbitMQ.
    """
    try:
        # Initialize service if needed
        if not arxiv_test_service.ai_service or not arxiv_test_service.ai_service.is_ready():
            await arxiv_test_service.initialize()
        
        # Execute search
        result = await arxiv_test_service.search_papers(request)
        
        logger.info(f"✅ ArXiv test completed: {len(result.papers)} papers found")
        return result
        
    except Exception as e:
        logger.error(f"❌ ArXiv test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ArXiv test failed: {str(e)}")


@router.get("/health")
async def arxiv_health_check():
    """Health check for arXiv API"""
    try:
        # Test basic connectivity
        test_client = ArxivClient()
        test_papers = await test_client.search_papers("test", limit=1)
        
        return {
            "status": "healthy",
            "service": "arxiv-test",
            "connectivity": "ok",
            "test_query_results": len(test_papers)
        }
    except Exception as e:
        logger.error(f"❌ ArXiv health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"ArXiv health check failed: {str(e)}")


@router.get("/stats")
async def arxiv_stats():
    """Get arXiv test service statistics"""
    return {
        "service": "arxiv-test",
        "ai_available": arxiv_test_service.ai_service is not None,
        "ai_ready": arxiv_test_service.ai_service.is_ready() if arxiv_test_service.ai_service else False,
        "config": {
            "recent_years_filter": arxiv_test_service.filter_service.recent_years_filter,
            "ai_model": arxiv_test_service.ai_config.model_name if arxiv_test_service.ai_config else None
        }
    }
