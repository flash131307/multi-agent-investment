"""
Shared pytest fixtures for all test suites.
"""
import os

# Set required env vars before any backend imports trigger settings validation
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-pytest")
os.environ.setdefault("SEC_EDGAR_USER_AGENT", "TestSuite tests@example.com")

import pytest
from datetime import datetime, timezone

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.technical import MarketRegime, RegimeType
from backend.models.sentiment import NewsArticle


# ---------------------------------------------------------------------------
# AgentSignal fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bullish_signal() -> AgentSignal:
    return AgentSignal(
        agent_name="technical",
        direction=Direction.BUY,
        strength=Strength.STRONG,
        confidence=0.85,
        reasoning="Strong uptrend with volume confirmation.",
    )


@pytest.fixture
def bearish_signal() -> AgentSignal:
    return AgentSignal(
        agent_name="fundamental",
        direction=Direction.SELL,
        strength=Strength.WEAK,
        confidence=0.55,
        reasoning="Elevated debt-to-equity ratio.",
    )


@pytest.fixture
def moderate_bullish_signal() -> AgentSignal:
    return AgentSignal(
        agent_name="sentiment",
        direction=Direction.BUY,
        strength=Strength.MODERATE,
        confidence=0.72,
        reasoning="Positive earnings coverage from Reuters.",
    )


@pytest.fixture
def neutral_signal() -> AgentSignal:
    return AgentSignal(
        agent_name="sentiment",
        direction=Direction.NEUTRAL,
        strength=Strength.WEAK,
        confidence=0.50,
        reasoning="Mixed news sentiment with no clear trend.",
    )


@pytest.fixture
def design_doc_signals(
    bullish_signal: AgentSignal,
    moderate_bullish_signal: AgentSignal,
    bearish_signal: AgentSignal,
) -> list[AgentSignal]:
    """The exact signals from the design doc worked example:
    Technical BUY/STRONG/0.85, Sentiment BUY/MODERATE/0.72, Fundamental SELL/WEAK/0.55
    """
    return [bullish_signal, moderate_bullish_signal, bearish_signal]


# ---------------------------------------------------------------------------
# Market regime fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def trending_regime() -> MarketRegime:
    return MarketRegime(
        regime_type=RegimeType.TRENDING,
        trend_strength=0.8,
        volatility=0.5,
        interpretation="Strong upward trend with moderate volatility.",
    )


@pytest.fixture
def ranging_regime() -> MarketRegime:
    return MarketRegime(
        regime_type=RegimeType.RANGING,
        trend_strength=0.2,
        volatility=0.3,
        interpretation="Sideways market with low directional bias.",
    )


# ---------------------------------------------------------------------------
# News article fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def reuters_article() -> NewsArticle:
    return NewsArticle(
        headline="Apple beats quarterly earnings expectations",
        summary="Apple reported EPS of $2.10, beating consensus of $1.95.",
        source="reuters",
        published_at=datetime.now(tz=timezone.utc),
        url="https://reuters.com/fake",
    )
