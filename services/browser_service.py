"""
Browser Service Module.

Handles fetching content from web pages using HTTPX, and parses/cleans HTML
using BeautifulSoup.
"""

import httpx
from bs4 import BeautifulSoup
from core.logger import logger
from core.utils import retry_async
from services.base import BaseBrowserService


class BrowserService(BaseBrowserService):
    """Production implementation of web page retrieval and content parser."""

    def __init__(self, timeout: int = 30):
        """Initialize BrowserService.

        Args:
            timeout: Default HTTP request timeout.
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        logger.debug("BrowserService initialized with standard headers.")

    @retry_async(max_retries=3, exceptions=(httpx.HTTPError,))
    async def fetch_page(self, url: str) -> str:
        """Fetch raw HTML/text content from a target URL.

        Args:
            url: Target URL string.

        Returns:
            str: Raw webpage body contents.
        """
        logger.info(f"Crawling webpage: {url}")
        
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def extract_main_text(self, html_content: str) -> str:
        """Parse raw HTML and isolate clean text content, stripping script/nav/header tags.

        Args:
            html_content: Raw HTML text.

        Returns:
            str: Normalized main textual content.
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Strip navigation, header, footer, script, and style tags
        for element in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            element.extract()

        # Extract text and normalize spaces
        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)

        return clean_text
