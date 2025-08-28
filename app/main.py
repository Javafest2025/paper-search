"""
Main entry point for ScholarAI Paper Search Service

This service provides comprehensive academic paper search capabilities with:
- Multi-source academic API integration
- AI-powered query refinement
- PDF collection and B2 storage
- RabbitMQ message processing
- Paper deduplication and enrichment
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core import settings
from app.services.rabbitmq_consumer import consumer
from app.services.websearch_agent import WebSearchAgent
from app.services.pdf_processor import pdf_processor
from app.api.api_v1.authors import router as authors_router
from app.api.api_v1.arxiv_test import router as arxiv_test_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for service management
websearch_agent = None
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global websearch_agent, consumer_task
    
    # Startup
    logger.info("🚀 Starting ScholarAI Paper Search Service...")
    
    try:
        # Initialize websearch agent
        websearch_agent = WebSearchAgent()
        logger.info("✅ WebSearch agent initialized")
        
        # Initialize PDF processor
        await pdf_processor.initialize()
        logger.info("✅ PDF processor initialized")
        
        # Start RabbitMQ consumer in background
        consumer_task = asyncio.create_task(consumer.start_consuming())
        logger.info("✅ RabbitMQ consumer started")
        
        logger.info("🎉 ScholarAI Paper Search Service ready")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down ScholarAI Paper Search Service...")
        
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        
        if websearch_agent:
            await websearch_agent.close()
        
        await pdf_processor.close()
        logger.info("👋 Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="ScholarAI Paper Search Service",
    description="Comprehensive academic paper search with PDF processing and B2 storage",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(authors_router, prefix="/api/v1/authors", tags=["authors"])
app.include_router(arxiv_test_router, prefix="/api/v1/arxiv", tags=["arxiv-test"])


# Pydantic models for API
class SearchRequest(BaseModel):
    projectId: str
    queryTerms: List[str]
    domain: str = "Computer Science"
    batchSize: int = 10
    correlationId: Optional[str] = None


class SearchResponse(BaseModel):
    projectId: str
    correlationId: Optional[str]
    papers: List[Dict[str, Any]]
    batchSize: int
    queryTerms: List[str]
    domain: str
    status: str
    searchStrategy: str
    totalSourcesUsed: int
    aiEnhanced: bool
    searchRounds: int
    deduplicationStats: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    rabbitmq_connected: bool
    websearch_agent_ready: bool
    pdf_processor_ready: bool


# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "ScholarAI Paper Search Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="paper-search",
        version="1.0.0",
        rabbitmq_connected=consumer.connection_manager.is_healthy() if consumer.connection_manager else False,
        websearch_agent_ready=websearch_agent is not None,
        pdf_processor_ready=pdf_processor.is_initialized if hasattr(pdf_processor, 'is_initialized') else False
    )


@app.post("/api/v1/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """
    Search for academic papers using multiple sources
    
    This endpoint provides the same functionality as the RabbitMQ consumer
    but through a direct HTTP API for testing and integration purposes.
    """
    if not websearch_agent:
        raise HTTPException(status_code=503, detail="WebSearch agent not initialized")
    
    try:
        logger.info(f"🔍 Direct API search request: {request.projectId}")
        
        # Process the search request
        result = await websearch_agent.process_request(request.dict())
        
        logger.info(f"✅ Direct API search completed: {len(result.get('papers', []))} papers found")
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Direct API search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/v1/stats")
async def get_stats():
    """Get service statistics"""
    if not websearch_agent:
        raise HTTPException(status_code=503, detail="WebSearch agent not initialized")
    
    try:
        stats = websearch_agent.get_search_stats()
        return {
            "service": "paper-search",
            "version": "1.0.0",
            "websearch_stats": stats,
            "consumer_status": consumer.consumer.get_status() if consumer.consumer else None
        }
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn
    
    # Run the service
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
