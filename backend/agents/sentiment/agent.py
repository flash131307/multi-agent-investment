"""
Sentiment analysis agent — three-layer FinBERT funnel.
"""
import logging
from typing import Optional

from backend.agents.base import BaseAgent
from backend.models.signals import AgentSignal, Direction, Strength
from backend.services.finbert_service import get_finbert_service

from .news_fetcher import fetch_news
from .filter import filter_articles
from .classifier import classify_articles
from .aggregator import aggregate_sentiments, to_agent_signal

logger = logging.getLogger(__name__)

_FALLBACK_SIGNAL = AgentSignal(
    agent_name="sentiment",
    direction=Direction.NEUTRAL,
    strength=Strength.WEAK,
    confidence=0.3,
    reasoning="No news articles available for analysis.",
)


class SentimentAgent(BaseAgent):
    """
    News sentiment agent using the FinBERT three-layer funnel:

    Layer 1 — Fetch & filter (relevance, deduplication, limit)
    Layer 2 — FinBERT classification with time-decay weighting
    Layer 3 — Weighted aggregation → AgentSignal
    """

    def __init__(self, timeout: float = 20.0) -> None:
        super().__init__(agent_name="sentiment", timeout=timeout)

    async def _execute(self, ticker: str) -> Optional[AgentSignal]:
        """
        Orchestrate the three-layer sentiment analysis funnel.

        Returns:
            AgentSignal on success, or NEUTRAL/WEAK fallback if no articles.

        Raises:
            RuntimeError: If FinBERT is not available.
        """
        finbert = get_finbert_service()
        if not finbert.is_available():
            raise RuntimeError(
                "FinBERT (transformers/torch) is not installed; "
                "cannot run SentimentAgent."
            )

        # Layer 0 — Fetch raw articles
        articles = fetch_news(ticker)
        logger.info("Fetched %d articles for %s", len(articles), ticker)

        # Layer 1 — Filter
        filtered = filter_articles(articles, ticker)
        logger.info("After filtering: %d articles for %s", len(filtered), ticker)

        if not filtered:
            logger.info("No articles after filtering for %s; returning fallback.", ticker)
            return _FALLBACK_SIGNAL

        # Layer 2 — Classify
        classified = classify_articles(filtered, finbert)
        logger.info("Classified %d articles for %s", len(classified), ticker)

        # Layer 3 — Aggregate → Signal
        result = aggregate_sentiments(classified)
        signal = to_agent_signal(result)

        logger.info(
            "SentimentAgent signal for %s: %s/%s (conf=%.2f)",
            ticker,
            signal.direction,
            signal.strength,
            signal.confidence,
        )
        return signal
