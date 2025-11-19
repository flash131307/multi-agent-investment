"""
Base agent class for all LangGraph agents.
Provides common functionality and error handling.
"""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
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

    Enhanced features:
    - Reasoning chain tracking for explainability
    - Smart retry mechanism with exponential backoff
    - Performance metrics (execution time, tokens)
    """

    def __init__(self, name: str, max_retries: int = 2, retry_delay: float = 1.0):
        """
        Initialize base agent.

        Args:
            name: Agent name for logging
            max_retries: Maximum number of retries on transient errors
            retry_delay: Initial retry delay in seconds (exponential backoff)
        """
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.reasoning_steps: List[str] = []  # Track reasoning for current execution

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
        Wrapper for execute() with error handling, metrics, and smart retry.

        Args:
            state: Current agent state

        Returns:
            Modified agent state (with errors if any)
        """
        self.logger.info(f"🤖 {self.name} agent starting...")

        # Reset reasoning steps for this execution
        self.reasoning_steps = []

        # Track performance metrics
        start_time = time.time()
        tokens_used = 0

        # Smart retry logic
        for attempt in range(self.max_retries + 1):
            try:
                # Execute agent logic
                new_state = await self.execute(state)

                # Calculate execution time
                execution_time = time.time() - start_time

                # Track successful execution
                self.logger.info(
                    f"✅ {self.name} agent completed successfully "
                    f"(time: {execution_time:.2f}s, attempt: {attempt + 1}/{self.max_retries + 1})"
                )

                # Build metrics
                metrics = {
                    "execution_time": execution_time,
                    "tokens_used": tokens_used,
                    "attempts": attempt + 1,
                    "success": True
                }

                # Prepare updates (use operator.or_ for dict merging in LangGraph)
                updates = {
                    **new_state,
                    "executed_agents": [self.name],
                    "agent_metrics": {self.name: metrics}
                }

                # Add reasoning chain if present
                if self.reasoning_steps:
                    updates["reasoning_chains"] = {self.name: self.reasoning_steps}

                return updates

            except Exception as e:
                # Classify error type
                is_transient = self._is_transient_error(e)
                is_last_attempt = attempt == self.max_retries

                if is_transient and not is_last_attempt:
                    # Retry with exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"⚠️  {self.name} agent encountered transient error: {str(e)}. "
                        f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries + 1})..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Handle final failure
                    error_msg = f"{self.name} agent error: {str(e)}"
                    self.logger.error(f"❌ {error_msg} (attempt {attempt + 1}/{self.max_retries + 1})")

                    # Calculate execution time
                    execution_time = time.time() - start_time

                    # Build failure metrics
                    metrics = {
                        "execution_time": execution_time,
                        "tokens_used": tokens_used,
                        "attempts": attempt + 1,
                        "success": False,
                        "error_type": type(e).__name__,
                        "is_transient": is_transient
                    }

                    # Prepare error state updates
                    updates = {
                        "errors": [error_msg],
                        "executed_agents": [self.name],
                        "agent_errors": {self.name: str(e)},
                        "agent_metrics": {self.name: metrics},
                        "retry_count": state.get("retry_count", 0) + 1
                    }

                    # Add reasoning chain with error
                    if self.reasoning_steps:
                        updates["reasoning_chains"] = {
                            self.name: self.reasoning_steps + [f"ERROR: {str(e)}"]
                        }

                    return updates

        # Should never reach here, but safety fallback
        return {
            "errors": [f"{self.name} agent: unexpected execution path"],
            "executed_agents": [self.name]
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

    def _add_reasoning_step(self, step: str):
        """
        Add a reasoning step for explainability.

        Args:
            step: Description of reasoning step
        """
        self.reasoning_steps.append(step)
        self.logger.debug(f"💭 Reasoning: {step}")

    def _is_transient_error(self, error: Exception) -> bool:
        """
        Classify if an error is transient (retryable).

        Transient errors:
        - API rate limits
        - Network timeouts
        - Temporary service unavailability

        Non-transient errors:
        - Authentication failures
        - Invalid input/parameters
        - Logic errors

        Args:
            error: Exception to classify

        Returns:
            True if error is transient and should be retried
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Network/API transient errors
        transient_keywords = [
            "timeout",
            "rate limit",
            "429",  # HTTP 429 Too Many Requests
            "503",  # HTTP 503 Service Unavailable
            "502",  # HTTP 502 Bad Gateway
            "connection",
            "temporary",
            "unavailable"
        ]

        # Non-transient error types
        non_transient_types = [
            "ValueError",
            "TypeError",
            "KeyError",
            "AttributeError",
            "AuthenticationError",
            "PermissionError"
        ]

        # Check if error type is non-transient
        if error_type in non_transient_types:
            return False

        # Check if error message contains transient keywords
        for keyword in transient_keywords:
            if keyword in error_str:
                return True

        # Default: non-transient (safer to not retry unknown errors)
        return False
