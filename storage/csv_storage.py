"""
CSV Storage Engine.

Implements storage and export capabilities for tabular structures using Pandas
and flat dictionary mappings.
"""

import asyncio
from pathlib import Path
from typing import List, Optional
import pandas as pd
from core.config import settings
from core.logger import logger
from core.models import AppResearch, ResearchStatistics
from storage.base import BaseStorage


class CSVStorage(BaseStorage):
    """File storage engine that saves and loads CSV exports."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize CSVStorage.

        Args:
            base_dir: Absolute path of project root directory.
        """
        self.base_dir = base_dir or settings.BASE_DIR
        self.lock = asyncio.Lock()
        logger.debug(f"CSVStorage initialized. Base directory={self.base_dir}")

    async def save_app_research(self, research: AppResearch, stage: str = "raw") -> None:
        """Not recommended for single CSV items. Redirects to JSON stage or appends.

        Args:
            research: The AppResearch data model.
            stage: Storage pipeline stage.
        """
        logger.warning("save_app_research is not optimized for CSV engine. Use JSONStorage for staged items.")
        pass

    async def load_app_research(self, app_name: str, stage: str = "raw") -> Optional[AppResearch]:
        """Not implemented for CSV storage. JSON storage is preferred for staging.

        Args:
            app_name: Name of target SaaS app.
            stage: Storage stage.

        Returns:
            Optional[AppResearch]: None.
        """
        logger.error("load_app_research is not supported by CSV storage.")
        return None

    async def save_bulk_research(self, research_list: List[AppResearch], file_name: str) -> None:
        """Consolidates research results into a tabular CSV structure using Pandas.

        Flattening is achieved using the custom `to_csv_dict` method in AppResearch.

        Args:
            research_list: List of AppResearch models.
            file_name: Name of target output file (e.g. 'research.csv').
        """
        output_path = self.base_dir / settings.OUTPUT_DIR / file_name
        logger.info(f"Consolidating bulk research into CSV: {output_path.relative_to(self.base_dir)}")

        async with self.lock:
            # Create output directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 1. Flatten each AppResearch record
            flat_records = [r.to_csv_dict() for r in research_list]
            
            # 2. Build DataFrame
            df = pd.DataFrame(flat_records)
            
            # 3. Export to CSV
            df.to_csv(output_path, index=False, encoding="utf-8")

    async def save_statistics(self, stats: ResearchStatistics) -> None:
        """CSV storage doesn't support structured statistics outputs.

        Args:
            stats: Calculated ResearchStatistics model.
        """
        # Exposing metrics in tabular format could be done if requested
        logger.warning("save_statistics is not supported by CSV storage. Use JSONStorage instead.")
        pass
