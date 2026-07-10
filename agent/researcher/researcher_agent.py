import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from agent.base import BaseAgent
from core.logger import logger
from core.models import AppResearch, Evidence
from core.prompts import SEARCH_QUERY_GENERATION_PROMPT
from services.browser_service import BrowserService
from services.extractor_service import ExtractorService
from services.search_service import SearchService


class ResearcherAgent(BaseAgent):
    """Orchestrator agent responsible for crawling web contents and compiling raw SaaS profiles."""

    def __init__(
        self,
        search_service: SearchService,
        browser_service: BrowserService,
        extractor_service: ExtractorService
    ):
        """Initialize ResearcherAgent.

        Args:
            search_service: Handles search engine requests.
            browser_service: Crawls text bodies from pages.
            extractor_service: Synthesizes structured data from textual contexts.
        """
        self.search = search_service
        self.browser = browser_service
        self.extractor = extractor_service
        logger.debug("ResearcherAgent initialized successfully.")

    async def run(self, app_name: str, homepage_url: str) -> AppResearch:
        """Execute initial SaaS research.

        Args:
            app_name: Name of the SaaS application.
            homepage_url: Base landing URL of the application.

        Returns:
            AppResearch: Initial structured research result populated with raw findings.
        """
        logger.info(f"Starting research sequence for app: '{app_name}'")

        # 1. Generate search queries
        queries = []
        try:
            llm_available = (
                self.extractor.llm.api_key is not None and 
                self.extractor.llm.api_key != "your_gemini_api_key_here" and 
                self.extractor.llm.api_key != "your_openai_api_key_here"
            )
            
            if llm_available:
                raw_queries_response = await self.extractor.llm.generate_text(
                    prompt=SEARCH_QUERY_GENERATION_PROMPT.format(num_queries=5, app_name=app_name)
                )
                cleaned_resp = self.extractor.llm._sanitize_json(raw_queries_response)
                queries = json.loads(cleaned_resp)
                if not isinstance(queries, list):
                    queries = []
        except Exception as e:
            logger.warning(f"Failed to generate search queries using LLM: {str(e)}. Falling back to static query template.")

        if not queries:
            queries = [
                f"{app_name} official website developer documentation portal",
                f"{app_name} API authentication authorization API keys OAuth",
                f"{app_name} API reference endpoint documentation",
                f"{app_name} API developer pricing plan access tiers",
                f"{app_name} Model Context Protocol MCP server support github"
            ]

        # 2. Search web for developer assets
        logger.debug(f"Searching web using queries: {queries}")
        search_results = await self.search.batch_search(queries, limit_per_query=3)

        # Store search results metadata for title and snippet fallbacks
        url_to_title = {r["url"]: r.get("title", "") for r in search_results}
        url_to_snippet = {r["url"]: r.get("snippet", "") for r in search_results}

        # Deduplicate and extract unique URLs
        unique_urls = [r["url"] for r in search_results]
        if homepage_url:
            unique_urls = [homepage_url] + unique_urls
        unique_urls = list(dict.fromkeys(unique_urls))

        # URL Rank prioritizer helper
        def get_url_priority(url: str) -> int:
            url_lower = url.lower()
            title_lower = url_to_title.get(url, "").lower()
            
            # Blogs last
            if "blog" in url_lower or "blog" in title_lower:
                return 6
                
            if homepage_url and (url == homepage_url or url_lower.rstrip('/') == homepage_url.lower().rstrip('/')):
                return 0
                
            try:
                parsed = urlparse(url_lower)
                domain_parts = parsed.netloc.split('.')
                # docs.*
                if domain_parts[0] == 'docs' or '/docs' in parsed.path:
                    return 1
                # developer.*
                if domain_parts[0] in ('developer', 'developers') or '/developer' in parsed.path:
                    return 2
                # api.*
                if domain_parts[0] == 'api' or '/api' in parsed.path:
                    return 3
            except Exception:
                pass
                
            # Official documentation
            if any(term in url_lower or term in title_lower for term in ("documentation", "reference", "docs")):
                return 4
                
            return 5

        # Sort unique URLs based on priority rank
        unique_urls.sort(key=get_url_priority)
        target_urls = unique_urls[:6]  # Limit to top 6 sources to prevent crawl storms

        # 3. Crawl target page bodies concurrently
        logger.info(f"Crawling {len(target_urls)} documentation URLs concurrently for '{app_name}'...")
        
        async def fetch_and_extract(url: str) -> Optional[Dict[str, Any]]:
            try:
                html = await self.browser.fetch_page(url)
                text = await self.browser.extract_main_text(html)
                if text:
                    snippet = text[:300] + "..." if len(text) > 300 else text
                    return {
                        "url": url,
                        "text": text,
                        "snippet": snippet
                    }
            except Exception as e:
                # Fallback to search snippet if status is 401, 403, or 429
                status_code = None
                if isinstance(e, httpx.HTTPStatusError):
                    status_code = e.response.status_code
                elif hasattr(e, "response") and e.response is not None and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code

                if status_code in (401, 403, 429):
                    fallback_snippet = url_to_snippet.get(url) or ""
                    if fallback_snippet:
                        logger.info(f"Page {url} returned status {status_code}. Falling back to search snippet.")
                        return {
                            "url": url,
                            "text": fallback_snippet,
                            "snippet": fallback_snippet
                        }
                logger.warning(f"Failed crawling documentation page {url}: {str(e)}")
            return None

        crawl_tasks = [fetch_and_extract(url) for url in target_urls]
        crawl_results = await asyncio.gather(*crawl_tasks)

        aggregated_content = []
        evidence_list = []
        
        for res in crawl_results:
            if res:
                aggregated_content.append(f"--- SOURCE: {res['url']} ---\n{res['text']}\n")
                
                # Get the actual search result title, with graceful defaults
                actual_title = url_to_title.get(res['url'])
                if not actual_title:
                    if res['url'] == homepage_url or res['url'].rstrip('/') == homepage_url.rstrip('/'):
                        actual_title = f"{app_name} Homepage"
                    else:
                        actual_title = f"Documentation Resource - {app_name}"
                        
                evidence_list.append(Evidence(
                    url=res['url'],
                    title=actual_title,
                    snippet=res['snippet'],
                    extracted_at=datetime.utcnow()
                ))

        full_context = "\n".join(aggregated_content)
        if not full_context:
            full_context = f"Fallback: Documentation for {app_name} could not be retrieved directly."

        # 4. Invoke the Extractor Service to parse structured SaaS details
        raw_research = await self.extractor.extract_features(
            app_name=app_name,
            raw_content=full_context,
            response_model=AppResearch
        )
        
        # Inject the evidence collected during scraping
        if evidence_list:
            raw_research.evidence = evidence_list

        logger.info(f"Finished raw research compilation for '{app_name}'. Confidence: {raw_research.confidence_score}%")
        return raw_research
