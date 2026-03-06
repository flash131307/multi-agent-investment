"""
Consistency scoring for the Decision Hub.

Measures how much three (or fewer) agent signals agree with each other.
The score drives risk mode selection which dampens final confidence.

Formula:
    raw_consistency = direction_score^1.5 × (0.6 × strength_score + 0.4 × confidence_score)
    final_consistency = raw_consistency × risk_mode.multiplier
"""

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.decision import ConsistencyScore, RiskMode

# ---------------------------------------------------------------------------
# Direction gate lookup tables
# Key: (n_buy, n_neutral, n_sell) — ordered counts
# ---------------------------------------------------------------------------

# 3-agent gate — scores from design doc
_GATE_3: dict[tuple[int, int, int], float] = {
    (3, 0, 0): 1.0,   # All BUY
    (0, 0, 3): 1.0,   # All SELL
    (2, 1, 0): 0.7,   # 2 BUY + 1 NEUTRAL
    (0, 1, 2): 0.7,   # 2 SELL + 1 NEUTRAL
    (1, 2, 0): 0.4,   # 1 BUY + 2 NEUTRAL
    (0, 2, 1): 0.4,   # 1 SELL + 2 NEUTRAL
    (2, 0, 1): 0.3,   # 2 BUY + 1 SELL (majority BUY, minority SELL)
    (1, 0, 2): 0.0,   # 1 BUY + 2 SELL (minority BUY, majority SELL — extra caution)
    (1, 1, 1): 0.1,   # Complete three-way split
    (0, 3, 0): 0.5,   # All NEUTRAL
}

# 2-agent gate — derived logically from 3-agent rules
_GATE_2: dict[tuple[int, int, int], float] = {
    (2, 0, 0): 1.0,   # Both BUY
    (0, 0, 2): 1.0,   # Both SELL
    (1, 1, 0): 0.7,   # 1 BUY + 1 NEUTRAL
    (0, 1, 1): 0.7,   # 1 SELL + 1 NEUTRAL
    (0, 2, 0): 0.5,   # Both NEUTRAL
    (1, 0, 1): 0.0,   # BUY vs SELL — complete conflict
}

# 1-agent gate — single agent, medium confidence regardless of direction
_GATE_1: dict[tuple[int, int, int], float] = {
    (1, 0, 0): 0.5,
    (0, 0, 1): 0.5,
    (0, 1, 0): 0.5,
}

_GATE_BY_COUNT = {1: _GATE_1, 2: _GATE_2, 3: _GATE_3}

# Risk mode thresholds
_RISK_THRESHOLDS = [
    (0.7, RiskMode.NORMAL),
    (0.4, RiskMode.CAUTIOUS),
    (0.0, RiskMode.RISK),
]


def _direction_key(signals: list[AgentSignal]) -> tuple[int, int, int]:
    """Return (n_buy, n_neutral, n_sell) for the gate lookup."""
    n_buy = sum(1 for s in signals if s.direction == Direction.BUY)
    n_neutral = sum(1 for s in signals if s.direction == Direction.NEUTRAL)
    n_sell = sum(1 for s in signals if s.direction == Direction.SELL)
    return (n_buy, n_neutral, n_sell)


def _compute_direction_score(signals: list[AgentSignal]) -> float:
    """Look up the direction gate score for the given signals."""
    n = len(signals)
    gate = _GATE_BY_COUNT.get(n)
    if gate is None:
        raise ValueError(f"Unsupported number of signals: {n}. Expected 1–3.")
    key = _direction_key(signals)
    return gate[key]


def _compute_strength_score(signals: list[AgentSignal]) -> float:
    """
    Strength agreement among directional (non-NEUTRAL) agents.

    Score = 1.0 - |max_strength - min_strength| / 2.0

    If all agents are NEUTRAL, return 1.0 (no strength disagreement).
    """
    directional = [s for s in signals if s.direction != Direction.NEUTRAL]
    if len(directional) <= 1:
        return 1.0
    strengths = [s.strength.numeric for s in directional]
    gap = (max(strengths) - min(strengths)) / 2.0
    return 1.0 - gap


def _compute_confidence_score(signals: list[AgentSignal]) -> float:
    """
    Confidence spread across all agents.

    Score = 1.0 - (max_confidence - min_confidence)
    """
    confidences = [s.confidence for s in signals]
    if len(confidences) <= 1:
        return 1.0
    return 1.0 - (max(confidences) - min(confidences))


def _risk_mode(raw_consistency: float) -> RiskMode:
    for threshold, mode in _RISK_THRESHOLDS:
        if raw_consistency >= threshold:
            return mode
    return RiskMode.RISK


def compute_consistency(signals: list[AgentSignal]) -> ConsistencyScore:
    """
    Compute consistency score for 1–3 agent signals.

    Args:
        signals: Non-empty list of AgentSignal (1–3 items).

    Returns:
        ConsistencyScore with all intermediate values and final result.

    Raises:
        ValueError: If signals is empty or has more than 3 items.
    """
    if not signals:
        raise ValueError("At least one signal is required.")
    if len(signals) > 3:
        raise ValueError(f"Maximum 3 signals supported, got {len(signals)}.")

    direction_score = _compute_direction_score(signals)
    strength_score = _compute_strength_score(signals)
    confidence_score = _compute_confidence_score(signals)

    raw_consistency = (
        direction_score ** 1.5
        * (0.6 * strength_score + 0.4 * confidence_score)
    )
    # Clamp to [0, 1] to guard against floating-point edge cases
    raw_consistency = min(1.0, max(0.0, raw_consistency))

    mode = _risk_mode(raw_consistency)
    final_consistency = min(1.0, raw_consistency * mode.multiplier)

    return ConsistencyScore(
        direction_score=direction_score,
        strength_score=strength_score,
        confidence_score=confidence_score,
        raw_consistency=raw_consistency,
        risk_mode=mode,
        final_consistency=final_consistency,
    )
