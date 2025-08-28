"""
API v1 router.
"""

from fastapi import APIRouter

from .websearch import router as websearch_router
from .authors import router as authors_router
from .arxiv_test import router as arxiv_test_router

api_router = APIRouter()

api_router.include_router(websearch_router, prefix="/websearch", tags=["websearch"])
api_router.include_router(authors_router, prefix="/authors", tags=["authors"])
api_router.include_router(arxiv_test_router, prefix="/arxiv", tags=["arxiv-test"])

