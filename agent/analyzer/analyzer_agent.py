"""
Analyzer Agent Module.

Computes aggregations, buildability statistics, category distributions,
and average confidence levels over compiled research datasets.
"""

import time
from typing import Dict, List
from agent.base import BaseAgent
from core.logger import logger
from core.models import AppResearch, BuildabilityVerdict, ResearchStatistics


class AnalyzerAgent(BaseAgent):
    """Analytics agent responsible for aggregating and compiling statistics over research items."""

    def __init__(self):
        """Initialize AnalyzerAgent."""
        logger.debug("AnalyzerAgent initialized.")

    async def run(self, research_list: List[AppResearch], total_inputs: int, elapsed_time: float) -> ResearchStatistics:
        """Process bulk research records and output aggregate pipeline analytics.

        Args:
            research_list: List of verified AppResearch records.
            total_inputs: The initial total size of SaaS apps list.
            elapsed_time: Pipeline execution time in seconds.

        Returns:
            ResearchStatistics: Summarized aggregations, categories, counts, and metrics.
        """
        logger.info(f"Analyzing {len(research_list)} records for statistics compilation.")

        if not research_list:
            return ResearchStatistics(
                total_apps=total_inputs,
                completed_apps=0,
                failed_apps=total_inputs,
                average_confidence=0.0,
                buildable_count=0,
                mcp_supported_count=0,
                category_distribution={},
                execution_time_seconds=elapsed_time
            )

        completed = len(research_list)
        failed = max(0, total_inputs - completed)
        
        # Calculate average confidence
        total_confidence = sum(r.confidence_score for r in research_list)
        avg_confidence = total_confidence / completed if completed > 0 else 0.0

        # Category mapping distribution
        category_dist: Dict[str, int] = {}
        buildable_count = 0
        mcp_supported_count = 0

        for r in research_list:
            # Check buildability verdict
            if r.buildability_verdict == BuildabilityVerdict.BUILDABLE:
                buildable_count += 1
                
            # Check MCP support status
            if r.mcp_support:
                mcp_supported_count += 1
                
            # Populate categories
            cat = r.category or "Uncategorized"
            category_dist[cat] = category_dist.get(cat, 0) + 1

        stats = ResearchStatistics(
            total_apps=total_inputs,
            completed_apps=completed,
            failed_apps=failed,
            average_confidence=round(avg_confidence, 2),
            buildable_count=buildable_count,
            mcp_supported_count=mcp_supported_count,
            category_distribution=category_dist,
            execution_time_seconds=round(elapsed_time, 2)
        )

        logger.info(
            f"Synthesized research statistics. "
            f"Buildable: {stats.buildable_count}, "
            f"MCP Supported: {stats.mcp_supported_count}, "
            f"Categories: {len(stats.category_distribution)}"
        )
        return stats
