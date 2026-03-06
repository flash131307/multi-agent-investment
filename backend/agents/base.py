"""
Abstract base class for ReAct-style analysis agents.
Provides timeout wrapping, error handling, and output validation.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

from backend.models.signals import AgentSignal

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for all analysis agents (technical, fundamental, sentiment).

    Subclasses must implement `run(ticker)` which returns an AgentSignal or None.
    This base class wraps execution with:
    - asyncio timeout
    - Exception catching with logging
    - Pydantic output validation
    """

    def __init__(self, agent_name: str, timeout: float = 30.0) -> None:
        self.agent_name = agent_name
        self.timeout = timeout
        self.logger = logging.getLogger(f"agent.{agent_name}")

    @abstractmethod
    async def _execute(self, ticker: str) -> Optional[AgentSignal]:
        """
        Core analysis logic to be implemented by subclasses.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            AgentSignal on success, None on failure.
        """
        raise NotImplementedError

    async def run(self, ticker: str) -> Optional[AgentSignal]:
        """
        Public entry point. Wraps _execute with timeout and error handling.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Validated AgentSignal, or None on timeout/error/invalid output.
        """
        try:
            result = await asyncio.wait_for(
                self._execute(ticker),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            self.logger.error(
                "Agent '%s' timed out after %.1fs for ticker '%s'",
                self.agent_name,
                self.timeout,
                ticker,
            )
            return None
        except Exception as exc:
            self.logger.error(
                "Agent '%s' raised an exception for ticker '%s': %s",
                self.agent_name,
                ticker,
                exc,
                exc_info=True,
            )
            return None

        return self._validate_output(result)

    def _validate_output(self, result: object) -> Optional[AgentSignal]:
        """
        Validate that result is a proper AgentSignal instance.

        Returns None and logs a warning if validation fails.
        """
        if result is None:
            return None
        if not isinstance(result, AgentSignal):
            self.logger.warning(
                "Agent '%s' returned unexpected type %s; expected AgentSignal",
                self.agent_name,
                type(result).__name__,
            )
            return None
        # Re-validate via Pydantic (catches any mutation that bypassed frozen=True)
        try:
            AgentSignal.model_validate(result.model_dump())
        except Exception as exc:
            self.logger.warning(
                "Agent '%s' output failed Pydantic validation: %s",
                self.agent_name,
                exc,
            )
            return None
        return result
