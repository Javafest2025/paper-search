"""
AI-powered search query refinement service
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Check for AI availability
try:
    import google.generativeai as genai

    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    AI_IMPORT_ERROR = str(e)
    logger.warning(
        f"Gemini AI not available: {AI_IMPORT_ERROR}. Query refinement disabled."
    )


class AIQueryRefinementService:
    """
    Service for AI-powered search query refinement using Google's Gemini.

    Analyzes existing search results to generate refined search queries that can
    discover additional relevant papers in subsequent search rounds.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self.is_initialized = False
        self.is_available = AI_AVAILABLE

        if not AI_AVAILABLE:
            logger.warning("AI refinement service initialized but AI not available")

    async def initialize(self) -> bool:
        """
        Initialize the Gemini AI client.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.is_available:
            logger.info("🤖 AI not available, query refinement disabled")
            return False

        try:
            logger.info("🤖 Initializing Gemini for query refinement...")
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            self.is_initialized = True
            logger.info("✅ Gemini initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.client = None
            self.is_initialized = False
            self.is_available = False
            return False

    async def generate_refined_queries(
        self,
        original_terms: List[str],
        domain: str,
        sample_papers: List[Dict[str, Any]],
        max_queries: int = 3,
    ) -> List[str]:
        """
        Generate refined search queries based on found papers.

        Args:
            original_terms: Original search terms used
            domain: Research domain/field
            sample_papers: Sample of papers found to analyze
            max_queries: Maximum number of refined queries to generate

        Returns:
            List of refined search query strings
        """
        if not self.is_available or not self.is_initialized:
            logger.debug("AI refinement not available, returning empty list")
            return []

        if not sample_papers:
            logger.debug("No sample papers provided for refinement")
            return []

        try:
            # Prepare context from sample papers
            paper_context = self._prepare_paper_context(sample_papers)

            # Generate refinement prompt
            prompt = self._build_refinement_prompt(
                original_terms, domain, paper_context, max_queries
            )

            # Call Gemini API
            response = await asyncio.to_thread(self.client.generate_content, prompt)

            if response and response.text:
                refined_queries = self._parse_response(response.text, max_queries)
                logger.info(f"🤖 Generated {len(refined_queries)} refined queries")
                return refined_queries
            else:
                logger.warning("No response from Gemini AI")
                return []

        except Exception as e:
            logger.error(f"Error generating refined queries: {str(e)}")
            return []

    def _prepare_paper_context(
        self, papers: List[Dict[str, Any]], max_papers: int = 5
    ) -> str:
        """
        Prepare context string from sample papers for AI analysis.

        Args:
            papers: List of paper dictionaries
            max_papers: Maximum number of papers to include in context

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, paper in enumerate(papers[:max_papers]):
            title = paper.get("title", "").strip()
            abstract = paper.get("abstract", "").strip()

            # Truncate abstract if too long
            if len(abstract) > 300:
                abstract = abstract[:300] + "..."

            paper_info = f"{i+1}. **{title}**"
            if abstract:
                paper_info += f"\n   Abstract: {abstract}"

            # Add other relevant metadata
            authors = paper.get("authors", [])
            if authors and isinstance(authors, list):
                author_names = [
                    a.get("name", str(a)) if isinstance(a, dict) else str(a)
                    for a in authors[:3]
                ]
                paper_info += f"\n   Authors: {', '.join(author_names)}"

            year = paper.get("year") or paper.get("published_year")
            if year:
                paper_info += f"\n   Year: {year}"

            context_parts.append(paper_info)

        return "\n\n".join(context_parts)

    def _build_refinement_prompt(
        self,
        original_terms: List[str],
        domain: str,
        paper_context: str,
        max_queries: int,
    ) -> str:
        """
        Build the prompt for AI query refinement.

        Args:
            original_terms: Original search terms
            domain: Research domain
            paper_context: Formatted context from sample papers
            max_queries: Maximum queries to generate

        Returns:
            Formatted prompt string
        """
        return f"""
You are an expert research assistant helping to find relevant academic papers.

Original search terms: {', '.join(original_terms)}
Research domain: {domain}

Based on these {len(paper_context.split('**'))-1} relevant papers found:

{paper_context}

Generate {max_queries} refined search queries that could help discover MORE relevant papers in this research area.

Guidelines:
1. Use different terminology and synonyms from the original terms
2. Focus on specific aspects, methodologies, or subtopics mentioned in the papers
3. Consider related concepts and emerging trends in the field
4. Keep queries concise (3-8 words each)
5. Avoid repeating the exact original terms

Return ONLY the refined search queries, one per line, without numbering, bullets, or explanations.
Example format:
neural network optimization techniques
deep learning computational efficiency
machine learning model compression
"""

    def _parse_response(self, response_text: str, max_queries: int) -> List[str]:
        """
        Parse the AI response to extract refined queries.

        Args:
            response_text: Raw response from AI
            max_queries: Maximum number of queries to return

        Returns:
            List of cleaned query strings
        """
        # Split response into lines and clean them
        lines = response_text.strip().split("\n")

        refined_queries = []
        for line in lines:
            # Clean the line
            cleaned = line.strip()

            # Skip empty lines
            if not cleaned:
                continue

            # Remove common prefixes (numbers, bullets, etc.)
            if cleaned.startswith(("1.", "2.", "3.", "4.", "5.", "-", "*", "•")):
                # Find the first space after the prefix and take the rest
                space_idx = cleaned.find(" ")
                if space_idx != -1:
                    cleaned = cleaned[space_idx:].strip()

            # Remove quotes if present
            cleaned = cleaned.strip("\"'")

            # Validate query length (not too short or too long)
            if 3 <= len(cleaned.split()) <= 10 and len(cleaned) > 10:
                refined_queries.append(cleaned)

            # Stop if we have enough queries
            if len(refined_queries) >= max_queries:
                break

        return refined_queries[:max_queries]

    def is_ready(self) -> bool:
        """Check if the AI service is ready to use"""
        return self.is_available and self.is_initialized

    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "ai_available": self.is_available,
            "initialized": self.is_initialized,
            "model_name": self.model_name,
            "ready": self.is_ready(),
        }

    async def close(self):
        """Clean up resources"""
        self.client = None
        self.is_initialized = False
        logger.info("🔒 AI refinement service closed")
