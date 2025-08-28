"""
Multi-Source Author Search API endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.multi_source_author_service import MultiSourceAuthorService, MultiSourceAuthorSearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# Multi-source author search endpoints
@router.get("/multi-source/{name}", response_model=MultiSourceAuthorSearchResponse)
async def search_author_multi_source(
    name: str,
    strategy: str = Query(default="fast", description="Search strategy: 'fast', 'comprehensive', or 'semantic_scholar_only'")
):
    """
    Search for an author using multiple academic data sources
    
    This endpoint combines data from Semantic Scholar, OpenAlex, ORCID, DBLP, and Crossref 
    to provide comprehensive author information with enhanced reliability.
    
    Args:
        name: Author name to search for
        strategy: Search strategy to use:
            - 'fast': Quick search using Semantic Scholar + OpenAlex
            - 'comprehensive': Search all available sources (slower but more complete)
            - 'semantic_scholar_only': Use only Semantic Scholar (fastest)
    
    Returns:
        Combined author information from multiple sources including:
        - Enhanced metrics with best available data
        - Multiple identifiers (Semantic Scholar, ORCID, OpenAlex)
        - Comprehensive affiliation history
        - Publication timeline and research areas
        - Data quality score and source attribution
    """
    try:
        multi_source_service = MultiSourceAuthorService()
        
        try:
            result = await multi_source_service.search_author(name, strategy)
            return result
        finally:
            multi_source_service.close()
            
    except Exception as e:
        logger.error(f"Error in multi-source author search endpoint: {str(e)}")
        return MultiSourceAuthorSearchResponse(
            success=False,
            error=f"Multi-source search failed: {str(e)}",
            search_strategy=strategy,
            sources_attempted=[],
            sources_successful=[]
        )


@router.post("/multi-source/batch", response_model=List[MultiSourceAuthorSearchResponse])
async def search_authors_multi_source_batch(
    request: Dict[str, Any]
):
    """
    Search for multiple authors using multi-source approach
    
    Request body format:
    {
        "author_names": ["Author 1", "Author 2", "Author 3"],
        "strategy": "fast"  // optional, defaults to "fast"
    }
    
    Args:
        request: Dictionary containing author_names list and optional strategy
        
    Returns:
        List of multi-source author search results
    """
    try:
        author_names = request.get("author_names", [])
        strategy = request.get("strategy", "fast")
        
        if not author_names:
            raise HTTPException(status_code=400, detail="author_names list is required")
        
        if len(author_names) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 authors per batch request")
        
        multi_source_service = MultiSourceAuthorService()
        
        try:
            results = await multi_source_service.search_authors_batch(author_names, strategy)
            return results
        finally:
            multi_source_service.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-source batch author search endpoint: {str(e)}")
        return [MultiSourceAuthorSearchResponse(
            success=False,
            error=f"Batch search failed: {str(e)}",
            search_strategy=strategy,
            sources_attempted=[],
            sources_successful=[]
        ) for _ in range(len(author_names) if 'author_names' in locals() else 1)]


@router.get("/multi-source/health")
async def multi_source_health():
    """
    Health check for multi-source author search service
    """
    try:
        multi_source_service = MultiSourceAuthorService()
        
        try:
            # Test with a well-known author using fast strategy
            result = await multi_source_service.search_author("Geoffrey Hinton", "fast")
            
            return {
                "status": "healthy" if result.success else "partial",
                "service": "multi-source-author-search",
                "test_query": "successful" if result.success else "failed",
                "sources_attempted": result.sources_attempted,
                "sources_successful": result.sources_successful,
                "data_quality": result.author.data_quality_score if result.author else 0.0,
                "error": result.error if not result.success else None
            }
        finally:
            multi_source_service.close()
            
    except Exception as e:
        logger.error(f"Multi-source health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "multi-source-author-search",
            "error": str(e)
        }