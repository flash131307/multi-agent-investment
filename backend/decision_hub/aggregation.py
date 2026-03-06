"""
Weighted signal aggregation for the Decision Hub.

Computes a scalar score from agent signals and their weights,
then maps it to a Direction and confidence value.

Formula:
    score = Σ(direction_numeric × strength_numeric × final_weight)
    direction: BUY if score > +0.25, SELL if score < -0.25, else NEUTRAL
    confidence = weighted_avg(agent_confidences) × risk_mode.multiplier
"""

from backend.models.signals import AgentSignal, Direction
from backend.models.decision import WeightAllocation, ConsistencyScore, RiskMode

# Numeric mapping for direction
_DIRECTION_NUMERIC: dict[Direction, float] = {
    Direction.BUY: +1.0,
    Direction.NEUTRAL: 0.0,
    Direction.SELL: -1.0,
}

# Thresholds for direction classification
_BUY_THRESHOLD = +0.25
_SELL_THRESHOLD = -0.25


def aggregate(
    signals: list[AgentSignal],
    weights: list[WeightAllocation],
    consistency: ConsistencyScore,
) -> tuple[Direction, float, float]:
    """
    Aggregate weighted signals into a final direction and confidence.

    Args:
        signals: Agent signals (ordered to match weights).
        weights: Normalized weight allocations (same order as signals).
        consistency: Computed consistency score (provides risk_mode).

    Returns:
        Tuple of (direction, confidence, aggregated_score).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals length ({len(signals)}) must match weights length ({len(weights)})."
        )

    # Map agent_name → weight for fast lookup
    weight_map = {w.agent_name: w.final_weight for w in weights}

    # Compute weighted score
    score = 0.0
    weighted_confidence_sum = 0.0
    for sig in signals:
        w = weight_map[sig.agent_name]
        score += _DIRECTION_NUMERIC[sig.direction] * sig.strength.numeric * w
        weighted_confidence_sum += sig.confidence * w

    # Classify direction
    if score > _BUY_THRESHOLD:
        direction = Direction.BUY
    elif score < _SELL_THRESHOLD:
        direction = Direction.SELL
    else:
        direction = Direction.NEUTRAL

    # Confidence = weighted average of agent confidences × risk mode multiplier
    raw_confidence = weighted_confidence_sum
    final_confidence = min(1.0, max(0.0, raw_confidence * consistency.risk_mode.multiplier))

    return direction, final_confidence, score
