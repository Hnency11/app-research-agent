"""
Base Services Module.

Defines standard abstract base interfaces for web search, document browsing/crawling,
LLM orchestration, and information extraction.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseSearchService(ABC):
    """Abstract interface for execution of web search queries."""

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Execute a single query in search engines and return result items.

        Args:
            query: The search query string.
            limit: Maximum search results to retrieve.

        Returns:
            List[Dict[str, Any]]: List of dictionary payloads with keys 'url', 'title', 'snippet'.
        """
        pass

    @abstractmethod
    async def batch_search(self, queries: List[str], limit_per_query: int = 5) -> List[Dict[str, Any]]:
        """Execute a batch of queries concurrently.

        Args:
            queries: A list of search queries.
            limit_per_query: Max results to return per query.

        Returns:
            List[Dict[str, Any]]: Deduplicated combined list of search result items.
        """
        pass


class BaseBrowserService(ABC):
    """Abstract interface for downloading and parsing webpage content."""

    @abstractmethod
    async def fetch_page(self, url: str) -> str:
        """Fetch raw HTML/text content from a target URL.

        Args:
            url: Target URL string.

        Returns:
            str: Raw webpage body contents.
        """
        pass

    @abstractmethod
    async def extract_main_text(self, html_content: str) -> str:
        """Parse raw HTML and isolate clean text content, stripping script/nav tags.

        Args:
            html_content: Raw HTML text.

        Returns:
            str: Normalized main textual content.
        """
        pass


class BaseLLMService(ABC):
    """Abstract interface for sending requests to Large Language Models."""

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate textual completion for a prompt.

        Args:
            prompt: User prompt content.
            system_prompt: Optional instructing system prompt.

        Returns:
            str: Generated text answer.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T], 
        system_prompt: Optional[str] = None
    ) -> T:
        """Generate structured data conforming to a target Pydantic schema.

        Args:
            prompt: User prompt.
            response_model: The Pydantic model subclass defining the expected structure.
            system_prompt: Optional system prompt context.

        Returns:
            T: An instance of the requested Pydantic model.
        """
        pass


class BaseExtractorService(ABC):
    """Abstract interface for extracting structured SaaS properties from webpage contexts."""

    @abstractmethod
    async def extract_app_features(self, app_name: str, raw_content: str) -> BaseModel:
        """Extract structured SaaS features from text using LLM synthesis.

        Args:
            app_name: Name of the target application.
            raw_content: The aggregated text scraped from documentation.

        Returns:
            BaseModel: A Pydantic model matching the research schema structure.
        """
        pass
