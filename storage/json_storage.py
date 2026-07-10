"""
JSON Storage Engine.

Implements serialization, file persistence, and bulk updates using JSON formatting
and asynchronous operations.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Optional
from core.config import settings
from core.logger import logger
from core.models import AppResearch, ResearchStatistics
from storage.base import BaseStorage


class JSONStorage(BaseStorage):
    """File storage engine that saves and loads JSON records."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize JSONStorage.

        Args:
            base_dir: Absolute path of project root directory.
        """
        self.base_dir = base_dir or settings.BASE_DIR
        self.lock = asyncio.Lock()
        logger.debug(f"JSONStorage initialized. Base directory={self.base_dir}")

    def _get_stage_path(self, app_name: str, stage: str) -> Path:
        """Helper to resolve file paths for staged app research."""
        safe_name = "".join(c for c in app_name if c.isalnum() or c in ("-", "_")).lower()
        return self.base_dir / settings.DATA_DIR / stage / f"{safe_name}.json"

    async def save_app_research(self, research: AppResearch, stage: str = "raw") -> None:
        """Persist a single AppResearch document to file.

        Args:
            research: The AppResearch data model.
            stage: Storage pipeline stage ('raw', 'processed', 'verified').
        """
        file_path = self._get_stage_path(research.app_name, stage)
        logger.info(f"Saving '{research.app_name}' research to {file_path.relative_to(self.base_dir)}")
        
        async with self.lock:
            # Create parents just in case
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(research.model_dump_json(indent=2))

    async def load_app_research(self, app_name: str, stage: str = "raw") -> Optional[AppResearch]:
        """Load a single AppResearch document from storage.

        Args:
            app_name: Name of target SaaS app.
            stage: Storage stage.

        Returns:
            Optional[AppResearch]: Loaded research object, or None if not found.
        """
        file_path = self._get_stage_path(app_name, stage)
        if not file_path.exists():
            logger.debug(f"Research file not found for app '{app_name}' at {file_path}")
            return None

        async with self.lock:
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    return AppResearch.model_validate(data)
                except Exception as e:
                    logger.error(f"Error parsing research JSON for app '{app_name}': {str(e)}")
                    return None

    async def save_bulk_research(self, research_list: List[AppResearch], file_name: str) -> None:
        """Save a list of AppResearch items to a single consolidated JSON file in output directory.

        Args:
            research_list: List of AppResearch models.
            file_name: Name of target output file (e.g. 'research.json').
        """
        output_path = self.base_dir / settings.OUTPUT_DIR / file_name
        logger.info(f"Consolidating bulk research into {output_path.relative_to(self.base_dir)}")
        
        async with self.lock:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize the list of models
            serialized_list = [r.model_dump() for r in research_list]
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(serialized_list, f, indent=2, default=str)

    async def save_statistics(self, stats: ResearchStatistics) -> None:
        """Persist aggregate metrics to the output directory.

        Args:
            stats: Calculated ResearchStatistics model.
        """
        output_path = self.base_dir / settings.OUTPUT_DIR / "statistics.json"
        logger.info(f"Saving research analytics to {output_path.relative_to(self.base_dir)}")
        
        async with self.lock:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(stats.model_dump_json(indent=2))
