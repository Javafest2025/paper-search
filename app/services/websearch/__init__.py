"""
WebSearch service module for ScholarAI

This module provides comprehensive academic paper search capabilities across
multiple sources with AI-powered query refinement and intelligent deduplication.
"""

from .config import AppConfig, SearchConfig, AIConfig, RabbitMQConfig
from .deduplication import PaperDeduplicationService
from .search_orchestrator import MultiSourceSearchOrchestrator
from .ai_refinement import AIQueryRefinementService
from .filter_service import SearchFilterService
from .metadata_enrichment import PaperMetadataEnrichmentService

__all__ = [
    "AppConfig",
    "SearchConfig",
    "AIConfig",
    "RabbitMQConfig",
    "PaperDeduplicationService",
    "MultiSourceSearchOrchestrator",
    "AIQueryRefinementService",
    "PaperMetadataEnrichmentService",
    "SearchFilterService",
]
