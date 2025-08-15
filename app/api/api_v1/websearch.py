from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.websearch import (
    AppConfig,
    MultiSourceSearchOrchestrator,
    AIQueryRefinementService,
)


class WebSearchRequest(BaseModel):
    projectId: Optional[str] = None
    queryTerms: List[str] = Field(default_factory=list)
    domain: str = "Computer Science"
    batchSize: int = 10
    correlationId: Optional[str] = None


router = APIRouter()


@router.post("/search")
async def websearch_search(req: WebSearchRequest):
    cfg = AppConfig.from_env()
    orchestrator = MultiSourceSearchOrchestrator(cfg.search)

    ai_service = None
    if cfg.search.enable_ai_refinement and cfg.ai.api_key:
        ai_service = AIQueryRefinementService(api_key=cfg.ai.api_key, model_name=cfg.ai.model_name)
        await ai_service.initialize()
        orchestrator.set_ai_service(ai_service)

    papers = await orchestrator.search_papers(
        query_terms=req.queryTerms,
        domain=req.domain,
        target_size=req.batchSize,
    )

    await orchestrator.close() if hasattr(orchestrator, "close") else None
    if ai_service:
        await ai_service.close()

    return {
        "projectId": req.projectId,
        "correlationId": req.correlationId,
        "papers": papers,
        "batchSize": len(papers),
        "queryTerms": req.queryTerms,
        "domain": req.domain,
        "status": "COMPLETED",
        "searchStrategy": "multi_source_modular",
    }


@router.get("/stats")
async def websearch_stats():
    cfg = AppConfig.from_env()
    orchestrator = MultiSourceSearchOrchestrator(cfg.search)
    stats = orchestrator.get_search_stats()
    return stats

