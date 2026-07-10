"""
Base Storage Module.

Defines standard abstract interface for reading/writing research outputs
and aggregate analytics records.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import AppResearch, ResearchStatistics


class BaseStorage(ABC):
    """Abstract interface for persisting SaaS app research pipelines outputs."""

    @abstractmethod
    async def save_app_research(self, research: AppResearch, stage: str = "raw") -> None:
        """Persist a single AppResearch document to file.

        Args:
            research: The AppResearch data model.
            stage: Storage pipeline stage ('raw', 'processed', 'verified').
        """
        pass

    @abstractmethod
    async def load_app_research(self, app_name: str, stage: str = "raw") -> Optional[AppResearch]:
        """Load a single AppResearch document from storage.

        Args:
            app_name: Name of target SaaS app.
            stage: Storage stage.

        Returns:
            Optional[AppResearch]: Loaded research object, or None if not found.
        """
        pass

    @abstractmethod
    async def save_bulk_research(self, research_list: List[AppResearch], file_name: str) -> None:
        """Save a list of AppResearch items to a single consolidated file.

        Args:
            research_list: List of AppResearch models.
            file_name: Name of target output file (e.g. 'research.json' or 'research.csv').
        """
        pass

    @abstractmethod
    async def save_statistics(self, stats: ResearchStatistics) -> None:
        """Persist aggregate metrics and calculations.

        Args:
            stats: Calculated ResearchStatistics model.
        """
        pass
