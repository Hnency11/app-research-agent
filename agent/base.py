"""
Base Agent Module.

Defines standard abstract interface for the research, verification, and analytical
agents within the pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract interface defining the execution protocol for all Pipeline Agents."""

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the agent's core task sequence.

        Args:
            *args: Generics positional arguments.
            **kwargs: Generics keyword arguments.

        Returns:
            Any: Structured execution result.
        """
        pass
