"""
Tests for SaaS Research Pipeline Services.

Validates operations, parameters, mock endpoints, and html parser cleanups.
"""

import pytest
from services.browser_service import BrowserService
from services.search_service import SearchService
from services.llm_service import LLMService


@pytest.mark.asyncio
async def test_browser_html_extraction():
    """Verifies BrowserService HTML tag pruning and whitespace normalization."""
    browser = BrowserService()
    
    html_input = """
    <html>
        <head><title>Test Doc</title></head>
        <body>
            <header><nav>Home link</nav></header>
            <main>
                <h1>Main Heading</h1>
                <p>This is standard description text.</p>
            </main>
            <script>console.log('strip me');</script>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    
    clean_text = await browser.extract_main_text(html_input)
    
    assert "Home link" not in clean_text
    assert "strip me" not in clean_text
    assert "Main Heading" in clean_text
    assert "This is standard description text." in clean_text


@pytest.mark.asyncio
async def test_search_service_mock():
    """Verifies that search service completes requests and formats schema fields."""
    search = SearchService()
    results = await search.search("stripe docs")
    
    assert len(results) > 0
    assert "url" in results[0]
    assert "title" in results[0]
    assert "snippet" in results[0]
