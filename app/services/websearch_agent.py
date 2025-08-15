"""
🚀 REFACTORED MULTI-SOURCE ACADEMIC PAPER FETCHING AGENT 🚀

A clean, modular implementation using separate services for different concerns:
- Configuration management
- Paper deduplication
- Search filtering
- AI-powered query refinement
- Multi-source orchestration

Maintains full backward compatibility while providing improved maintainability,
testability, and separation of concerns.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .websearch import (
    AppConfig,
    AIQueryRefinementService,
    MultiSourceSearchOrchestrator,
)

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """
    🎯 Clean, modular academic paper fetching agent.

    Orchestrates multiple services to provide comprehensive paper search
    across academic sources with AI-powered refinement and deduplication.
    """

    def __init__(self, config: AppConfig = None):
        # Initialize configuration
        self.config = config or AppConfig.from_env()

        # Initialize search orchestrator
        self.orchestrator = MultiSourceSearchOrchestrator(self.config.search)

        # Initialize AI service if enabled
        self.ai_service = None
        if self.config.search.enable_ai_refinement:
            self.ai_service = AIQueryRefinementService(
                api_key=self.config.ai.api_key, model_name=self.config.ai.model_name
            )
            self.orchestrator.set_ai_service(self.ai_service)

        logger.info("🤖 WebSearchAgent ready")

    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Main entry point for multi-source paper fetching.

        Maintains backward compatibility with the original interface.
        """
        # Extract request parameters
        project_id = request_data.get("projectId")
        query_terms = request_data.get("queryTerms", [])
        domain = request_data.get("domain", "Computer Science")
        batch_size = request_data.get("batchSize", 10)
        correlation_id = request_data.get("correlationId")

        logger.info(
            f"🔍 Searching papers for project {project_id}: {', '.join(query_terms)} (target: {batch_size})"
        )

        # Initialize AI service if needed
        if self.ai_service and not self.ai_service.is_ready():
            await self.ai_service.initialize()

        # Execute the search
        papers = await self.orchestrator.search_papers(
            query_terms=query_terms, domain=domain, target_size=batch_size
        )

        # Get search statistics
        search_stats = self.orchestrator.get_search_stats()

        # Build response (maintaining backward compatibility)
        result = {
            "projectId": project_id,
            "correlationId": correlation_id,
            "papers": papers,
            "batchSize": len(papers),
            "queryTerms": query_terms,
            "domain": domain,
            "status": "COMPLETED",
            "searchStrategy": "multi_source_modular",
            "totalSourcesUsed": len(search_stats["active_sources"]),
            "aiEnhanced": search_stats["ai_enabled"],
            "searchRounds": self.config.search.max_search_rounds,
            "deduplicationStats": {
                "unique_papers": search_stats["unique_papers"],
                "total_identifiers": search_stats["total_identifiers"],
            },
        }

        logger.info(f"✅ Found {len(papers)} papers for project {project_id}")
        return result

    async def close(self):
        """🔒 Clean up all resources"""
        logger.info("🔒 Closing WebSearchAgent...")

        if self.orchestrator:
            await self.orchestrator.close()

        logger.info("✅ WebSearchAgent closed")

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self.config

    def get_search_stats(self) -> Dict[str, Any]:
        """Get current search statistics"""
        base_stats = self.orchestrator.get_search_stats() if self.orchestrator else {}

        return {
            **base_stats,
            "config": {
                "papers_per_source": self.config.search.papers_per_source,
                "max_search_rounds": self.config.search.max_search_rounds,
                "enable_ai_refinement": self.config.search.enable_ai_refinement,
                "recent_years_filter": self.config.search.recent_years_filter,
            },
            "ai_status": (
                self.ai_service.get_status() if self.ai_service else {"ready": False}
            ),
        }


# Backward compatibility aliases
class MultiSourcePaperFetcher(WebSearchAgent):
    """
    🔄 Backward compatibility alias for the old class name
    """

    pass


# Global instance for backward compatibility
websearch_agent = WebSearchAgent()


# Legacy functions for backward compatibility (if needed)
async def initialize_websearch_agent(config: AppConfig = None) -> WebSearchAgent:
    """Initialize and return a new WebSearchAgent instance"""
    agent = WebSearchAgent(config)
    if agent.ai_service:
        await agent.ai_service.initialize()
    return agent
