"""
Unit tests for backend/agents/sentiment/aggregator.py

Covers all four design doc scenarios plus threshold and edge case tests.
"""
import math
import pytest
from datetime import datetime, timedelta, timezone

from backend.models.sentiment import (
    AggregationResult,
    ArticleSentiment,
    NewsArticle,
    SentimentLabel,
)
from backend.models.signals import Direction, Strength
from backend.agents.sentiment.aggregator import aggregate_sentiments, to_agent_signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_article(
    headline: str = "Headline",
    source: str = "reuters",
    days_ago: int = 0,
) -> NewsArticle:
    published_at = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return NewsArticle(
        headline=headline,
        summary="Summary text.",
        source=source,
        published_at=published_at,
    )


def _make_classified(
    label: SentimentLabel,
    confidence: float = 0.9,
    source: str = "reuters",
    days_ago: int = 0,
    headline: str = "Headline",
) -> ArticleSentiment:
    """Create an ArticleSentiment with computed time_decay and source_weight."""
    time_decay = math.exp(-0.1 * days_ago)
    from backend.agents.sentiment.filter import get_source_weight
    source_weight = get_source_weight(source)
    return ArticleSentiment(
        article=_make_article(headline=headline, source=source, days_ago=days_ago),
        label=label,
        confidence=confidence,
        source_weight=source_weight,
        time_decay=time_decay,
    )


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

class TestAggregateEmpty:
    def test_empty_list_returns_neutral_result(self):
        result = aggregate_sentiments([])
        assert result.weighted_sentiment == 0.0
        assert result.article_count == 0
        assert result.confidence == 0.0
        assert result.coverage_factor == 0.0
        assert result.consistency_factor == 1.0

    def test_empty_list_signal_is_neutral_weak(self):
        result = aggregate_sentiments([])
        signal = to_agent_signal(result)
        assert signal.direction == Direction.NEUTRAL
        assert signal.strength == Strength.WEAK


# ---------------------------------------------------------------------------
# Scenario 1 — All positive (high confidence, Reuters)
# ---------------------------------------------------------------------------

class TestScenario1AllPositive:
    def _build_classified(self) -> list[ArticleSentiment]:
        return [
            _make_classified(SentimentLabel.POSITIVE, confidence=0.95, source="reuters", days_ago=i)
            for i in range(10)
        ]

    def test_direction_is_buy(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        signal = to_agent_signal(result)
        assert signal.direction == Direction.BUY

    def test_strength_is_strong(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        signal = to_agent_signal(result)
        assert signal.strength == Strength.STRONG

    def test_weighted_sentiment_above_0_5(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        assert result.weighted_sentiment > 0.5

    def test_article_count_is_10(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        assert result.article_count == 10

    def test_coverage_factor_is_1(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        assert result.coverage_factor == 1.0


# ---------------------------------------------------------------------------
# Scenario 2 — Time decay flip (recent positive beats old negative)
# ---------------------------------------------------------------------------

class TestScenario2TimeDecay:
    def _build_classified(self) -> list[ArticleSentiment]:
        # 5 recent POSITIVE articles (days_ago=0..4)
        recent_positive = [
            _make_classified(SentimentLabel.POSITIVE, confidence=0.9, source="reuters", days_ago=i)
            for i in range(5)
        ]
        # 8 old NEGATIVE articles (days_ago=30..37) — heavily decayed
        old_negative = [
            _make_classified(SentimentLabel.NEGATIVE, confidence=0.9, source="reuters", days_ago=30 + i)
            for i in range(8)
        ]
        return recent_positive + old_negative

    def test_direction_is_buy(self):
        """Recent positive articles outweigh old negative ones due to time decay."""
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        signal = to_agent_signal(result)
        assert signal.direction == Direction.BUY

    def test_weighted_sentiment_is_positive(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        assert result.weighted_sentiment > 0


# ---------------------------------------------------------------------------
# Scenario 3 — Equal positive/negative split
# ---------------------------------------------------------------------------

class TestScenario3EqualSplit:
    def _build_classified(self) -> list[ArticleSentiment]:
        positives = [
            _make_classified(SentimentLabel.POSITIVE, confidence=0.8, days_ago=i)
            for i in range(5)
        ]
        negatives = [
            _make_classified(SentimentLabel.NEGATIVE, confidence=0.8, days_ago=i)
            for i in range(5)
        ]
        return positives + negatives

    def test_direction_is_neutral(self):
        """Equal positive and negative weights → neutral signal."""
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        signal = to_agent_signal(result)
        assert signal.direction == Direction.NEUTRAL

    def test_weighted_sentiment_near_zero(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        assert abs(result.weighted_sentiment) < 0.15


# ---------------------------------------------------------------------------
# Scenario 4 — Low coverage (2 articles)
# ---------------------------------------------------------------------------

class TestScenario4LowCoverage:
    def _build_classified(self) -> list[ArticleSentiment]:
        return [
            _make_classified(SentimentLabel.POSITIVE, confidence=0.8, days_ago=0),
            _make_classified(SentimentLabel.NEGATIVE, confidence=0.8, days_ago=1),
        ]

    def test_coverage_factor_is_low(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        # 2/10 = 0.2
        assert result.coverage_factor == pytest.approx(0.2)

    def test_confidence_is_low(self):
        classified = self._build_classified()
        result = aggregate_sentiments(classified)
        # With only 2 articles and mixed sentiment, final confidence should be low
        # (but note to_agent_signal clamps to [0.1, 0.95])
        assert result.confidence < 0.5


# ---------------------------------------------------------------------------
# to_agent_signal threshold tests
# ---------------------------------------------------------------------------

class TestToAgentSignalThresholds:
    def _result(self, ws: float) -> AggregationResult:
        return AggregationResult(
            weighted_sentiment=ws,
            confidence=0.5,
            article_count=10,
            consistency_factor=1.0,
            coverage_factor=1.0,
        )

    def test_just_above_buy_threshold(self):
        signal = to_agent_signal(self._result(0.16))
        assert signal.direction == Direction.BUY

    def test_exactly_at_buy_threshold_not_buy(self):
        # 0.15 is NOT > 0.15
        signal = to_agent_signal(self._result(0.15))
        assert signal.direction == Direction.NEUTRAL

    def test_just_below_sell_threshold(self):
        signal = to_agent_signal(self._result(-0.16))
        assert signal.direction == Direction.SELL

    def test_exactly_at_sell_threshold_not_sell(self):
        # -0.15 is NOT < -0.15
        signal = to_agent_signal(self._result(-0.15))
        assert signal.direction == Direction.NEUTRAL

    def test_neutral_zone(self):
        signal = to_agent_signal(self._result(0.05))
        assert signal.direction == Direction.NEUTRAL

    def test_negative_neutral_zone(self):
        signal = to_agent_signal(self._result(-0.10))
        assert signal.direction == Direction.NEUTRAL


# ---------------------------------------------------------------------------
# Strength classification tests
# ---------------------------------------------------------------------------

class TestStrengthClassification:
    def _result(self, ws: float) -> AggregationResult:
        return AggregationResult(
            weighted_sentiment=ws,
            confidence=0.5,
            article_count=10,
            consistency_factor=1.0,
            coverage_factor=1.0,
        )

    def test_strong_buy(self):
        signal = to_agent_signal(self._result(0.6))
        assert signal.strength == Strength.STRONG
        assert signal.direction == Direction.BUY

    def test_moderate_buy(self):
        signal = to_agent_signal(self._result(0.3))
        assert signal.strength == Strength.MODERATE

    def test_weak_buy(self):
        signal = to_agent_signal(self._result(0.2))
        assert signal.strength == Strength.WEAK

    def test_strong_sell(self):
        signal = to_agent_signal(self._result(-0.6))
        assert signal.strength == Strength.STRONG
        assert signal.direction == Direction.SELL

    def test_moderate_sell(self):
        signal = to_agent_signal(self._result(-0.3))
        assert signal.strength == Strength.MODERATE

    def test_weak_sell(self):
        signal = to_agent_signal(self._result(-0.2))
        assert signal.strength == Strength.WEAK

    def test_neutral_cannot_be_strong(self):
        """NEUTRAL direction with STRONG strength is invalid per AgentSignal model."""
        # weighted_sentiment=0.0 → NEUTRAL, and abs(0) > 0.5 is False anyway
        signal = to_agent_signal(self._result(0.0))
        assert signal.direction == Direction.NEUTRAL
        assert signal.strength != Strength.STRONG


# ---------------------------------------------------------------------------
# Confidence clamping
# ---------------------------------------------------------------------------

class TestConfidenceClamping:
    def test_confidence_clamped_to_min_0_1(self):
        # Near-zero confidence from aggregation should be clamped to 0.1
        result = aggregate_sentiments([])
        signal = to_agent_signal(result)
        assert signal.confidence >= 0.1

    def test_confidence_clamped_to_max_0_95(self):
        # Even perfect scenario shouldn't exceed 0.95
        classified = [
            _make_classified(SentimentLabel.POSITIVE, confidence=1.0, source="reuters", days_ago=0)
            for _ in range(10)
        ]
        result = aggregate_sentiments(classified)
        signal = to_agent_signal(result)
        assert signal.confidence <= 0.95
