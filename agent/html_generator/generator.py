"""
HTML Generator Agent Module.

Handles loading research datasets and statistics summaries, loading Jinja2 templates,
and rendering premium visual dashboard reports.
"""

from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from agent.base import BaseAgent
from core.config import settings
from core.logger import logger
from core.models import AppResearch, ResearchStatistics


class HTMLReportGenerator(BaseAgent):
    """HTML report generator agent that formats results into an interactive dashboard."""

    def __init__(self, templates_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """Initialize HTMLReportGenerator.

        Args:
            templates_dir: Path to directory containing report HTML templates.
            output_dir: Path to directory where case study report is rendered.
        """
        self.templates_dir = templates_dir or (settings.BASE_DIR / settings.TEMPLATES_DIR)
        self.output_dir = output_dir or (settings.BASE_DIR / settings.REPORTS_DIR)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"])
        )
        logger.debug(f"HTMLReportGenerator setup complete. Templates={self.templates_dir}")

    async def run(self, research_list: List[AppResearch], stats: ResearchStatistics) -> Path:
        """Render the SaaS Research Pipeline interactive dashboard case study.

        Args:
            research_list: List of verified SaaS research records.
            stats: Summarized analytics data.

        Returns:
            Path: Absolute path to the generated HTML case study report.
        """
        output_file_path = self.output_dir / "case_study.html"
        logger.info(f"Rendering report case_study.html to {output_file_path.relative_to(settings.BASE_DIR)}")

        template_vars = {
            "apps": [r.model_dump(mode="json") for r in research_list],
            "stats": stats.model_dump(mode="json"),
            "generated_at": stats.category_distribution.get("date_placeholder") or "2026-07-09T18:55:00Z"
        }

        # 2. Load and render template
        try:
            template = self.env.get_template("report_template.html")
            html_content = template.render(**template_vars)
            
            # Ensure parents exist
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            logger.info("HTML dashboard report generated successfully.")
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error rendering HTML template: {str(e)}")
            raise
