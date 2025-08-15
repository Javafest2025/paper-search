"""
API v1 router.
"""

from fastapi import APIRouter

from .websearch import router as websearch_router
from .authors import router as authors_router

api_router = APIRouter()

api_router.include_router(websearch_router, prefix="/websearch", tags=["websearch"])
api_router.include_router(authors_router, prefix="/authors", tags=["authors"])

