"""
Base agent class for all LangGraph agents.
Provides common functionality and error handling.
"""
import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    All agents should:
    1. Inherit from this class
    2. Implement the execute() method
    3. Return modified AgentState
    4. Handle errors gracefully
    """

    def __init__(self, name: str):
        """
        Initialize base agent.

        Args:
            name: Agent name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute agent logic and return modified state.

        Args:
            state: Current agent state

        Returns:
            Modified agent state
        """
        pass

    async def __call__(self, state: AgentState) -> AgentState:
        """
        Wrapper for execute() with error handling and logging.

        Args:
            state: Current agent state

        Returns:
            Modified agent state (with errors if any)
        """
        self.logger.info(f"🤖 {self.name} agent starting...")

        try:
            # Execute agent logic
            new_state = await self.execute(state)

            self.logger.info(f"✅ {self.name} agent completed successfully")
            return new_state

        except Exception as e:
            # Handle errors gracefully
            error_msg = f"{self.name} agent error: {str(e)}"
            self.logger.error(f"❌ {error_msg}")

            # Add error to state
            errors = state.get("errors", [])
            errors.append(error_msg)

            # Return state with error
            return {
                **state,
                "errors": errors,
                "retry_count": state.get("retry_count", 0) + 1
            }

    def _update_state(self, state: AgentState, updates: Dict[str, Any]) -> AgentState:
        """
        Helper to update state immutably.

        Args:
            state: Current state
            updates: Fields to update

        Returns:
            New state with updates
        """
        return {**state, **updates}

    def _log_state(self, state: AgentState, prefix: str = ""):
        """
        Helper to log current state (for debugging).

        Args:
            state: Current state
            prefix: Optional prefix for log message
        """
        self.logger.debug(
            f"{prefix}State: "
            f"session={state.get('session_id')}, "
            f"intent={state.get('intent')}, "
            f"tickers={state.get('tickers')}, "
            f"errors={len(state.get('errors', []))}"
        )
