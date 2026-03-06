"""
FundamentalAgent: orchestrates the 4-step Plan-and-Solve pipeline.
"""
import logging
from typing import TYPE_CHECKING

from backend.agents.base import BaseAgent
from backend.models.signals import AgentSignal
from backend.agents.fundamental.profiler import build_profile
from backend.agents.fundamental.planner import generate_tasks
from backend.agents.fundamental.executor import execute_tasks
from backend.agents.fundamental.synthesizer import synthesize
from backend.agents.fundamental.tools.financial_data import get_financial_statements

if TYPE_CHECKING:
    from backend.rag.retriever import HybridRetriever

logger = logging.getLogger(__name__)


class FundamentalAgent(BaseAgent):
    """
    Fundamental analysis agent implementing the 4-step Plan-and-Solve framework:

    1. Profile  – build CompanyProfile from yfinance + RAG
    2. Plan     – LLM generates AnalysisTask list
    3. Execute  – run each task with RAG + LLM → SubConclusion list
    4. Synthesize – cross-task consistency check → AgentSignal

    Args:
        retriever: Optional HybridRetriever for RAG support.
        timeout: Seconds before the agent times out (default 60).
        settings_override: Optional settings object for testing (bypasses Settings()).
    """

    def __init__(
        self,
        retriever: "HybridRetriever | None" = None,
        timeout: float = 60.0,
        settings_override=None,
    ) -> None:
        super().__init__(agent_name="fundamental", timeout=timeout)
        self._retriever = retriever
        self._settings_override = settings_override

    def _get_settings(self):
        """Return settings object, using override in tests or loading from config."""
        if self._settings_override is not None:
            return self._settings_override
        from backend.config.settings import settings as app_settings
        return app_settings

    async def _execute(self, ticker: str) -> AgentSignal | None:
        """
        Run the full 4-step pipeline for the given ticker.

        Returns AgentSignal on success, None on unrecoverable error.
        """
        app_settings = self._get_settings()

        try:
            # Step 1: Profile
            logger.info("[%s] Step 1: building company profile", ticker)
            profile = build_profile(ticker, self._retriever)

            # Step 2: Plan
            logger.info("[%s] Step 2: generating analysis tasks", ticker)
            tasks = generate_tasks(profile, app_settings)

            # Step 3a: Financial data
            logger.info("[%s] Step 3a: fetching financial statements", ticker)
            financial_data = get_financial_statements(ticker)

            # Step 3b: Execute tasks
            logger.info("[%s] Step 3b: executing %d tasks", ticker, len(tasks))
            conclusions = execute_tasks(
                tasks=tasks,
                ticker=ticker,
                retriever=self._retriever,
                financial_data=financial_data,
                settings_obj=app_settings,
            )

            # Step 4: Synthesize
            logger.info("[%s] Step 4: synthesizing signal", ticker)
            signal = synthesize(profile, conclusions, tasks)

            logger.info(
                "[%s] FundamentalAgent result: %s/%s confidence=%.2f",
                ticker,
                signal.direction,
                signal.strength,
                signal.confidence,
            )
            return signal

        except Exception as exc:
            logger.error(
                "FundamentalAgent unrecoverable error for '%s': %s",
                ticker,
                exc,
                exc_info=True,
            )
            return None
