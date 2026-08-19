"""Base class shared by all Driftsagent module agents."""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    All module agents inherit from this base.
    Enforces the human-in-the-loop contract: agents recommend and explain,
    never take automated actions on external systems.
    """

    module_name: str = "base"

    @abstractmethod
    def analyser(self, poster: list[dict], **kwargs) -> dict[str, Any]:
        """Run domain analysis and return structured result."""
        ...

    @abstractmethod
    def besvar_sporsmal(self, sporsmal: str, analyse: dict) -> str:
        """Answer a freetext question using Claude, given the analysis context."""
        ...

    def _format_nok(self, value: float | int) -> str:
        """Format a value as NOK with space as thousands separator."""
        return f"{int(value):,}".replace(",", " ") + " kr"
