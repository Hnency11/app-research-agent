"""
Extractor Service Module.

Orchestrates raw webpage information crawling, main content text pruning,
and structured SaaS research schema generation.
"""

from typing import Type, TypeVar
from pydantic import BaseModel
from core.logger import logger
from core.prompts import EXTRACTOR_SYSTEM_PROMPT, EXTRACTOR_USER_PROMPT
from services.base import BaseBrowserService, BaseExtractorService, BaseLLMService

T = TypeVar("T", bound=BaseModel)


class ExtractorService(BaseExtractorService):
    """Integrates browsing scrapers and LLMs to compile AppResearch data models."""

    def __init__(self, browser_service: BaseBrowserService, llm_service: BaseLLMService):
        """Initialize ExtractorService.

        Args:
            browser_service: Crawler service instance.
            llm_service: LLM service instance.
        """
        self.browser = browser_service
        self.llm = llm_service
        logger.debug("ExtractorService initialized.")

    async def extract_app_features(self, app_name: str, raw_content: str) -> BaseModel:
        """Helper placeholder that maps to general BaseExtractorService."""
        # This calls the implementation in extract_features with the default AppResearch model
        from core.models import AppResearch
        return await self.extract_features(app_name, raw_content, AppResearch)

    def select_relevant_content(self, content: str, max_chars: int = 15000) -> str:
        """Select lines/sections matching API, OAuth, SDK, REST, GraphQL, Webhooks, MCP keywords.

        Preserves source headers and structural context.
        """
        keywords = ["api", "oauth", "sdk", "rest", "graphql", "webhooks", "mcp"]
        
        # Split content by source blocks to preserve source-attribution headers
        parts = content.split("--- SOURCE: ")
        selected_parts = []
        
        for part in parts:
            if not part.strip():
                continue
            # Split the source header from the page text
            header_line, *lines = part.split("\n")
            source_header = "--- SOURCE: " + header_line
            
            relevant_lines = []
            for line in lines:
                line_strip = line.strip()
                if not line_strip:
                    continue
                # Keep lines with keywords
                line_lower = line_strip.lower()
                if any(kw in line_lower for kw in keywords):
                    relevant_lines.append(line_strip)
            
            if relevant_lines:
                selected_parts.append(source_header + "\n" + "\n".join(relevant_lines))
                
        if not selected_parts:
            # Fallback to simple slice if no lines matched keywords
            return content[:max_chars]
            
        joined = "\n\n".join(selected_parts)
        if len(joined) > max_chars:
            return joined[:max_chars] + "\n... [truncated]"
        return joined

    async def extract_features(self, app_name: str, raw_content: str, response_model: Type[T]) -> T:
        """Parse text segments, trim whitespace, and invoke structural LLM extraction.

        Args:
            app_name: Name of target app.
            raw_content: Large raw dump of text or documents.
            response_model: Expected Pydantic model response type (typically AppResearch).

        Returns:
            T: Extracted model instance.
        """
        logger.info(f"Extracting SaaS features for: {app_name}")
        
        # 1. Clean scraped documentation using smart selection
        cleaned_text = self.select_relevant_content(raw_content)
        
        # 2. Formulate prompts
        user_prompt = EXTRACTOR_USER_PROMPT.format(app_name=app_name, content=cleaned_text)
        
        # 3. Call structured LLM endpoint
        extracted_result = await self.llm.generate_structured(
            prompt=user_prompt,
            response_model=response_model,
            system_prompt=EXTRACTOR_SYSTEM_PROMPT
        )
        
        return extracted_result
