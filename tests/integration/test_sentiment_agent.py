"""
Integration tests for the SentimentAgent three-layer funnel.

FinBERT and Finnhub are mocked so no network or GPU is required.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from backend.models.sentiment import (
    NewsArticle,
    PublicSentimentSnapshot,
    PublicSentimentSource,
    SentimentLabel,
    SourceAlignment,
)
from backend.models.signals import AgentSignal, Direction
from backend.agents.sentiment.agent import SentimentAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_raw_article(
    headline: str,
    summary: str,
    source: str = "reuters",
    days_ago: int = 0,
) -> dict:
    ts = int((datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).timestamp())
    return {
        "headline": headline,
        "summary": summary,
        "source": source,
        "datetime": ts,
        "url": f"https://example.com/{headline[:10]}",
    }


def _positive_articles(ticker: str, count: int = 5) -> list[dict]:
    return [
        _make_raw_article(
            headline=f"{ticker} reports strong Q{i} earnings",
            summary=f"{ticker} beat expectations with EPS above consensus for Q{i}.",
            source="reuters",
            days_ago=i,
        )
        for i in range(count)
    ]


def _public_snapshot(
    ticker: str,
    *,
    average_buzz: float = 82.0,
    average_bullish_pct: float = 68.0,
    coverage_factor: float = 1.0,
    alignment_factor: float = 1.0,
    source_alignment: SourceAlignment = SourceAlignment.ALIGNED,
) -> PublicSentimentSnapshot:
    return PublicSentimentSnapshot(
        ticker=ticker,
        days_back=7,
        sources=[
            PublicSentimentSource(
                source="reddit",
                buzz_score=80.0,
                bullish_pct=64.0,
                trend="rising",
                mentions=420,
            ),
            PublicSentimentSource(
                source="x",
                buzz_score=84.0,
                bullish_pct=72.0,
                trend="rising",
                mentions=1100,
            ),
            PublicSentimentSource(
                source="polymarket",
                buzz_score=82.0,
                bullish_pct=68.0,
                trend="stable",
                trade_count=500,
            ),
        ],
        average_buzz=average_buzz,
        average_bullish_pct=average_bullish_pct,
        coverage_factor=coverage_factor,
        alignment_factor=alignment_factor,
        source_alignment=source_alignment,
    )


# ---------------------------------------------------------------------------
# Full pipeline integration test
# ---------------------------------------------------------------------------

class TestSentimentAgentFullPipeline:
    """Mock both Finnhub and FinBERT; test full pipeline execution."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_valid_signal(self):
        ticker = "AAPL"
        raw_articles = _positive_articles(ticker, count=5)
        articles = _convert_raw_to_articles(raw_articles)

        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True
        mock_finbert.classify.return_value = [
            (SentimentLabel.POSITIVE, 0.9) for _ in range(len(articles))
        ]

        with (
            patch(
                "backend.agents.sentiment.agent.fetch_news",
                return_value=articles,
            ),
            patch(
                "backend.agents.sentiment.agent.fetch_public_sentiment",
                return_value=None,
            ),
            patch(
                "backend.agents.sentiment.agent.get_finbert_service",
                return_value=mock_finbert,
            ),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run(ticker)

        assert signal is not None
        assert isinstance(signal, AgentSignal)
        assert signal.agent_name == "sentiment"
        assert signal.direction in (Direction.BUY, Direction.NEUTRAL, Direction.SELL)
        assert 0.0 <= signal.confidence <= 1.0
        assert len(signal.reasoning) > 0

    @pytest.mark.asyncio
    async def test_positive_news_produces_buy_signal(self):
        ticker = "MSFT"
        raw_articles = _positive_articles(ticker, count=10)
        articles = _convert_raw_to_articles(raw_articles)

        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True
        mock_finbert.classify.return_value = [
            (SentimentLabel.POSITIVE, 0.95) for _ in range(len(articles))
        ]

        with (
            patch(
                "backend.agents.sentiment.agent.fetch_news",
                return_value=articles,
            ),
            patch(
                "backend.agents.sentiment.agent.fetch_public_sentiment",
                return_value=None,
            ),
            patch(
                "backend.agents.sentiment.agent.get_finbert_service",
                return_value=mock_finbert,
            ),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run(ticker)

        assert signal is not None
        assert signal.direction == Direction.BUY


# ---------------------------------------------------------------------------
# Empty news fallback test
# ---------------------------------------------------------------------------

class TestSentimentAgentEmptyNews:
    @pytest.mark.asyncio
    async def test_empty_news_returns_neutral_signal(self):
        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True

        with (
            patch(
                "backend.agents.sentiment.agent.fetch_news",
                return_value=[],
            ),
            patch(
                "backend.agents.sentiment.agent.fetch_public_sentiment",
                return_value=None,
            ),
            patch(
                "backend.agents.sentiment.agent.get_finbert_service",
                return_value=mock_finbert,
            ),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run("FAKE")

        assert signal is not None
        assert signal.direction == Direction.NEUTRAL

    @pytest.mark.asyncio
    async def test_no_articles_after_filter_returns_neutral(self):
        """When filter_articles returns empty, agent returns NEUTRAL fallback."""
        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True

        with (
            patch("backend.agents.sentiment.agent.fetch_news", return_value=[]),
            patch("backend.agents.sentiment.agent.fetch_public_sentiment", return_value=None),
            patch("backend.agents.sentiment.agent.get_finbert_service", return_value=mock_finbert),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run("FAKE")

        assert signal is not None
        assert signal.direction == Direction.NEUTRAL
        assert signal.strength.value == "WEAK"


# ---------------------------------------------------------------------------
# FinBERT unavailable test
# ---------------------------------------------------------------------------

class TestSentimentAgentFinBERTUnavailable:
    @pytest.mark.asyncio
    async def test_finbert_unavailable_causes_runtime_error(self):
        """When FinBERT is unavailable, BaseAgent.run catches RuntimeError → returns None."""
        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = False

        with patch(
            "backend.agents.sentiment.agent.get_finbert_service",
            return_value=mock_finbert,
        ):
            agent = SentimentAgent(timeout=10.0)
            # BaseAgent.run catches all exceptions and returns None
            signal = await agent.run("AAPL")

        assert signal is None


# ---------------------------------------------------------------------------
# Mixed sentiment integration test
# ---------------------------------------------------------------------------

class TestSentimentAgentMixedNews:
    @pytest.mark.asyncio
    async def test_mixed_news_produces_signal(self):
        ticker = "TSLA"
        raw_articles = [
            _make_raw_article(
                f"{ticker} positive news item {i}",
                f"{ticker} beats expectations in area {i}.",
                days_ago=i,
            )
            for i in range(6)
        ]
        articles = _convert_raw_to_articles(raw_articles)

        # Return alternating positive/negative
        labels = [
            (SentimentLabel.POSITIVE, 0.8) if i % 2 == 0 else (SentimentLabel.NEGATIVE, 0.8)
            for i in range(len(articles))
        ]

        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True
        mock_finbert.classify.return_value = labels

        with (
            patch(
                "backend.agents.sentiment.agent.fetch_news",
                return_value=articles,
            ),
            patch(
                "backend.agents.sentiment.agent.fetch_public_sentiment",
                return_value=None,
            ),
            patch(
                "backend.agents.sentiment.agent.get_finbert_service",
                return_value=mock_finbert,
            ),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run(ticker)

        assert signal is not None
        assert isinstance(signal, AgentSignal)
        assert signal.agent_name == "sentiment"

    @pytest.mark.asyncio
    async def test_public_sentiment_can_drive_signal_when_no_news_is_available(self):
        ticker = "NVDA"
        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True

        with (
            patch("backend.agents.sentiment.agent.fetch_news", return_value=[]),
            patch(
                "backend.agents.sentiment.agent.fetch_public_sentiment",
                return_value=_public_snapshot(ticker, average_buzz=84.0, average_bullish_pct=74.0),
            ),
            patch("backend.agents.sentiment.agent.get_finbert_service", return_value=mock_finbert),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run(ticker)

        assert signal is not None
        assert signal.direction == Direction.BUY
        assert "Public sentiment" in signal.reasoning

    @pytest.mark.asyncio
    async def test_public_sentiment_is_additive_but_does_not_override_strong_news_signal(self):
        ticker = "AAPL"
        articles = _convert_raw_to_articles(_positive_articles(ticker, count=8))

        mock_finbert = MagicMock()
        mock_finbert.is_available.return_value = True
        mock_finbert.classify.return_value = [
            (SentimentLabel.POSITIVE, 0.92) for _ in range(len(articles))
        ]

        with (
            patch("backend.agents.sentiment.agent.fetch_news", return_value=articles),
            patch(
                "backend.agents.sentiment.agent.fetch_public_sentiment",
                return_value=_public_snapshot(
                    ticker,
                    average_buzz=88.0,
                    average_bullish_pct=22.0,
                    alignment_factor=0.8,
                    source_alignment=SourceAlignment.MIXED,
                ),
            ),
            patch("backend.agents.sentiment.agent.get_finbert_service", return_value=mock_finbert),
        ):
            agent = SentimentAgent(timeout=10.0)
            signal = await agent.run(ticker)

        assert signal is not None
        assert signal.direction == Direction.BUY


# ---------------------------------------------------------------------------
# Helper: convert raw dicts to NewsArticle models (for tests that bypass
# the real fetch_news)
# ---------------------------------------------------------------------------

def _convert_raw_to_articles(raw_articles: list[dict]) -> list[NewsArticle]:
    """Convert Finnhub raw article dicts into NewsArticle Pydantic models."""
    result = []
    for raw in raw_articles:
        headline = (raw.get("headline") or "").strip()
        summary = (raw.get("summary") or "").strip()
        if not headline or not summary:
            continue
        ts = raw.get("datetime") or 0
        published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        source = (raw.get("source") or "").strip().lower()
        url = raw.get("url") or ""
        result.append(
            NewsArticle(
                headline=headline,
                summary=summary,
                source=source,
                published_at=published_at,
                url=url,
            )
        )
    return result
