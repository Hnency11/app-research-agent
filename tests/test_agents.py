"""
Tests for SaaS Research Pipeline Agents.

Validates initialization, signature compatibility, and outputs of research, verifier,
analyzer, and report generator agents.
"""

import pytest
from core.models import AppResearch, ResearchStatistics
from agent.researcher.researcher_agent import ResearcherAgent
from agent.verifier.verifier_agent import VerifierAgent
from agent.analyzer.analyzer_agent import AnalyzerAgent
from agent.html_generator.generator import HTMLReportGenerator
from services.search_service import SearchService
from services.browser_service import BrowserService
from services.llm_service import LLMService
from services.extractor_service import ExtractorService


@pytest.mark.asyncio
async def test_analyzer_agent(mock_app_research):
    """Verifies AnalyzerAgent properly compiles statistics over app research lists."""
    analyzer = AnalyzerAgent()
    stats = await analyzer.run(
        research_list=[mock_app_research],
        total_inputs=1,
        elapsed_time=2.5
    )

    assert isinstance(stats, ResearchStatistics)
    assert stats.total_apps == 1
    assert stats.completed_apps == 1
    assert stats.buildable_count == 1
    assert stats.average_confidence == 95.0
    assert "Payment Gateway" in stats.category_distribution


@pytest.mark.asyncio
async def test_agent_initializations():
    """Verifies that all pipeline agents can be initialized with service structures."""
    search = SearchService()
    browser = BrowserService()
    llm = LLMService()
    extractor = ExtractorService(browser, llm)

    researcher = ResearcherAgent(search, browser, extractor)
    verifier = VerifierAgent(browser, llm)
    analyzer = AnalyzerAgent()
    generator = HTMLReportGenerator()

    assert researcher is not None
    assert verifier is not None
    assert analyzer is not None
    assert generator is not None
