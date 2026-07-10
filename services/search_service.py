import asyncio
import httpx
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logger import logger
from core.utils import AsyncRateLimiter, retry_async
from services.base import BaseSearchService


class SearchService(BaseSearchService):
    """Production implementation of the Search service using Tavily/Serper APIs."""

    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 2.0):
        """Initialize SearchService.

        Args:
            api_key: Search engine API credentials (optional, defaults to environment).
            rate_limit: Queries allowed per second.
        """
        self.api_key = api_key
        self.limiter = AsyncRateLimiter(rate_limit)
        logger.debug(f"SearchService initialized with rate_limit={rate_limit} requests/sec.")

    @retry_async(max_retries=3, exceptions=(httpx.HTTPError, Exception))
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search the web for a specific query.

        Args:
            query: The search query string.
            limit: Maximum search results to retrieve.

        Returns:
            List[Dict[str, Any]]: Search results with keys 'url', 'title', 'snippet'.
        """
        await self.limiter.acquire()
        logger.info(f"Executing web search query: '{query}'")

        # 1. Check Tavily API Key
        tavily_key = self.api_key or settings.TAVILY_API_KEY
        if tavily_key:
            logger.debug("Using Tavily Search API")
            headers = {"Content-Type": "application/json"}
            payload = {
                "api_key": tavily_key,
                "query": query,
                "max_results": limit,
                "search_depth": "basic"
            }
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post("https://api.tavily.com/search", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "url": item.get("url"),
                        "title": item.get("title", ""),
                        "snippet": item.get("content", "")
                    })
                return results

        # 2. Check Serper API Key
        serper_key = settings.SERPER_API_KEY
        if serper_key:
            logger.debug("Using Serper Search API")
            headers = {
                "X-API-KEY": serper_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": limit
            }
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post("https://google.serper.dev/search", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("organic", []):
                    results.append({
                        "url": item.get("link"),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", "")
                    })
                return results

        # 3. Fallback to mock search results
        logger.warning(f"No search API keys configured. Returning mockup results for query: '{query}'")
        mock_results = [
            {
                "url": f"https://docs.example.com/{query.replace(' ', '-')}",
                "title": f"Official Documentation - {query}",
                "snippet": f"This is placeholder search evidence snippet for query: '{query}'."
            }
        ]
        return mock_results

    async def batch_search(self, queries: List[str], limit_per_query: int = 5) -> List[Dict[str, Any]]:
        """Execute a batch of queries concurrently.

        Args:
            queries: A list of search queries.
            limit_per_query: Max results to return per query.

        Returns:
            List[Dict[str, Any]]: Deduplicated combined list of search result items.
        """
        logger.info(f"Starting concurrent batch search for {len(queries)} queries.")
        
        # Run searches concurrently using asyncio.gather
        tasks = [self.search(query, limit_per_query) for query in queries]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        results: List[Dict[str, Any]] = []
        for index, rlist in enumerate(results_lists):
            if isinstance(rlist, Exception):
                logger.error(f"Search query '{queries[index]}' failed: {str(rlist)}")
                continue
            results.extend(rlist)

        # Deduplicate results by URL
        seen_urls = set()
        deduped_results = []
        for r in results:
            url_str = str(r["url"])
            if url_str not in seen_urls:
                seen_urls.add(url_str)
                deduped_results.append(r)

        return deduped_results
