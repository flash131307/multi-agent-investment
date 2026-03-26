"""
Layer 3 — Weighted sentiment aggregation and signal generation.
"""
import logging
import statistics

from backend.models.sentiment import (
    AggregationResult,
    ArticleSentiment,
    PublicSentimentSnapshot,
    SentimentLabel,
)
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
_MAX_PUBLIC_SENTIMENT_WEIGHT = 0.25
_MIN_PUBLIC_FALLBACK_QUALITY = 0.25

# Numeric mapping for SentimentLabel
_SENTIMENT_NUMERIC: dict[SentimentLabel, float] = {
    SentimentLabel.POSITIVE: +1.0,
    SentimentLabel.NEGATIVE: -1.0,
    SentimentLabel.NEUTRAL: 0.0,
}


def aggregate_sentiments(
    classified: list[ArticleSentiment],
    public_sentiment: PublicSentimentSnapshot | None = None,
) -> AggregationResult:
    """
    Compute a weighted aggregation of classified article sentiments.

    Weighting: each article's effective_weight = confidence × time_decay × source_weight.

    Returns:
        AggregationResult with weighted_sentiment, confidence, and factors.
    """
    if not classified:
        if public_sentiment is not None:
            fallback = _fallback_from_public_sentiment(public_sentiment)
            if fallback is not None:
                return fallback
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

    result = AggregationResult(
        weighted_sentiment=weighted_sentiment,
        confidence=final_confidence,
        article_count=article_count,
        consistency_factor=consistency_factor,
        coverage_factor=coverage_factor,
    )
    if public_sentiment is None:
        return result
    return _blend_with_public_sentiment(result, public_sentiment)


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
    if result.public_sentiment_used:
        mode = result.public_sentiment_mode or "blended"
        if result.public_average_buzz is not None and result.public_average_bullish_pct is not None:
            reasoning += (
                f" Public sentiment ({mode}) showed avg buzz "
                f"{result.public_average_buzz:.1f}/100 and avg bullish "
                f"{result.public_average_bullish_pct:.1f}%"
            )
            if result.public_source_alignment is not None:
                reasoning += f" with {result.public_source_alignment.value.replace('_', ' ')} alignment."

    return AgentSignal(
        agent_name="sentiment",
        direction=direction,
        strength=strength,
        confidence=confidence,
        reasoning=reasoning,
    )


def _blend_with_public_sentiment(
    result: AggregationResult,
    public_sentiment: PublicSentimentSnapshot,
) -> AggregationResult:
    """Blend a small public-sentiment prior into the news-based result."""
    quality = _public_sentiment_quality(public_sentiment)
    if quality <= 0.0:
        return result

    social_score = _map_bullish_pct_to_score(public_sentiment.average_bullish_pct)
    public_weight = min(_MAX_PUBLIC_SENTIMENT_WEIGHT, _MAX_PUBLIC_SENTIMENT_WEIGHT * quality)
    blended_sentiment = ((1.0 - public_weight) * result.weighted_sentiment) + (
        public_weight * social_score
    )
    blended_sentiment = max(-1.0, min(1.0, blended_sentiment))
    blended_confidence = max(
        result.confidence,
        min(1.0, result.confidence + (0.15 * quality)),
    )

    return result.model_copy(
        update={
            "weighted_sentiment": blended_sentiment,
            "confidence": blended_confidence,
            "public_sentiment_used": True,
            "public_sentiment_mode": "blended",
            "public_average_buzz": public_sentiment.average_buzz,
            "public_average_bullish_pct": public_sentiment.average_bullish_pct,
            "public_source_alignment": public_sentiment.source_alignment,
        }
    )


def _fallback_from_public_sentiment(
    public_sentiment: PublicSentimentSnapshot,
) -> AggregationResult | None:
    """Use public sentiment as a deterministic fallback when no articles survived."""
    quality = _public_sentiment_quality(public_sentiment)
    if quality < _MIN_PUBLIC_FALLBACK_QUALITY:
        return None

    social_score = _map_bullish_pct_to_score(public_sentiment.average_bullish_pct)
    weighted_sentiment = max(-1.0, min(1.0, social_score * max(0.55, quality)))
    confidence = min(0.8, 0.2 + (0.6 * quality))

    return AggregationResult(
        weighted_sentiment=weighted_sentiment,
        confidence=confidence,
        article_count=0,
        consistency_factor=public_sentiment.alignment_factor,
        coverage_factor=public_sentiment.coverage_factor,
        public_sentiment_used=True,
        public_sentiment_mode="fallback",
        public_average_buzz=public_sentiment.average_buzz,
        public_average_bullish_pct=public_sentiment.average_bullish_pct,
        public_source_alignment=public_sentiment.source_alignment,
    )


def _public_sentiment_quality(public_sentiment: PublicSentimentSnapshot) -> float:
    """Convert public sentiment coverage/buzz/alignment into a bounded quality score."""
    buzz_factor = public_sentiment.average_buzz / 100.0
    return max(
        0.0,
        min(
            1.0,
            public_sentiment.coverage_factor
            * public_sentiment.alignment_factor
            * buzz_factor,
        ),
    )


def _map_bullish_pct_to_score(average_bullish_pct: float) -> float:
    """Map 0-100 bullish percentage to the hub-compatible [-1, 1] range."""
    return max(-1.0, min(1.0, (average_bullish_pct - 50.0) / 50.0))
