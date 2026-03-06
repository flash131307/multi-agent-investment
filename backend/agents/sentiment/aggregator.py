"""
Layer 3 — Weighted sentiment aggregation and signal generation.
"""
import logging
import math
import statistics
from typing import Sequence

from backend.models.sentiment import AggregationResult, ArticleSentiment, SentimentLabel
from backend.models.signals import AgentSignal, Direction, Strength

logger = logging.getLogger(__name__)

# Thresholds for directional classification
_BUY_THRESHOLD = 0.15
_SELL_THRESHOLD = -0.15

# Strength thresholds (absolute weighted_sentiment)
_STRONG_THRESHOLD = 0.5
_MODERATE_THRESHOLD = 0.25

# Confidence clamp bounds
_CONFIDENCE_MIN = 0.1
_CONFIDENCE_MAX = 0.95

# Number of articles for full coverage
_FULL_COVERAGE_COUNT = 10

# Numeric mapping for SentimentLabel
_SENTIMENT_NUMERIC: dict[SentimentLabel, float] = {
    SentimentLabel.POSITIVE: +1.0,
    SentimentLabel.NEGATIVE: -1.0,
    SentimentLabel.NEUTRAL: 0.0,
}


def aggregate_sentiments(classified: list[ArticleSentiment]) -> AggregationResult:
    """
    Compute a weighted aggregation of classified article sentiments.

    Weighting: each article's effective_weight = confidence × time_decay × source_weight.

    Returns:
        AggregationResult with weighted_sentiment, confidence, and factors.
    """
    if not classified:
        return AggregationResult(
            weighted_sentiment=0.0,
            confidence=0.0,
            article_count=0,
            consistency_factor=1.0,
            coverage_factor=0.0,
        )

    article_count = len(classified)
    coverage_factor = min(article_count / _FULL_COVERAGE_COUNT, 1.0)

    weights: list[float] = []
    numerics: list[float] = []
    for item in classified:
        w = item.effective_weight
        n = _SENTIMENT_NUMERIC[item.label]
        weights.append(w)
        numerics.append(n)

    total_weight = sum(weights)
    if total_weight == 0.0:
        weighted_sentiment = 0.0
    else:
        weighted_sentiment = sum(n * w for n, w in zip(numerics, weights)) / total_weight

    # Clamp to [-1, 1] to satisfy Pydantic field constraint
    weighted_sentiment = max(-1.0, min(1.0, weighted_sentiment))

    # Consistency factor: low standard deviation → high consistency
    if len(numerics) > 1:
        std_dev = statistics.stdev(numerics)
    else:
        std_dev = 0.0
    clamped_std = max(0.0, min(1.0, std_dev))
    consistency_factor = 1.0 - clamped_std

    # Base confidence from signal strength and factors
    base_confidence = abs(weighted_sentiment)
    final_confidence = base_confidence * consistency_factor * coverage_factor

    # Clamp to valid Pydantic range [0, 1]
    final_confidence = max(0.0, min(1.0, final_confidence))

    return AggregationResult(
        weighted_sentiment=weighted_sentiment,
        confidence=final_confidence,
        article_count=article_count,
        consistency_factor=consistency_factor,
        coverage_factor=coverage_factor,
    )


def to_agent_signal(result: AggregationResult) -> AgentSignal:
    """
    Convert an AggregationResult into a tradeable AgentSignal.

    Direction thresholds: >+0.15 → BUY, <-0.15 → SELL, else NEUTRAL.
    Strength: |ws| > 0.5 → STRONG, > 0.25 → MODERATE, else WEAK.
    """
    ws = result.weighted_sentiment

    # Direction
    if ws > _BUY_THRESHOLD:
        direction = Direction.BUY
    elif ws < _SELL_THRESHOLD:
        direction = Direction.SELL
    else:
        direction = Direction.NEUTRAL

    # Strength
    abs_ws = abs(ws)
    if abs_ws > _STRONG_THRESHOLD:
        strength = Strength.STRONG
    elif abs_ws > _MODERATE_THRESHOLD:
        strength = Strength.MODERATE
    else:
        strength = Strength.WEAK

    # AgentSignal validation: NEUTRAL direction cannot have STRONG strength
    if direction == Direction.NEUTRAL and strength == Strength.STRONG:
        strength = Strength.MODERATE

    # Clamp confidence
    confidence = max(_CONFIDENCE_MIN, min(_CONFIDENCE_MAX, result.confidence))

    reasoning = (
        f"Analyzed {result.article_count} articles. "
        f"Weighted sentiment: {result.weighted_sentiment:.3f}. "
        f"Consistency: {result.consistency_factor:.2f}."
    )

    return AgentSignal(
        agent_name="sentiment",
        direction=direction,
        strength=strength,
        confidence=confidence,
        reasoning=reasoning,
    )
