"""
Step 4 of Plan-and-Solve: synthesize SubConclusions into a final AgentSignal.
"""
import logging
import math

from backend.models.fundamental import CompanyProfile, AnalysisTask, SubConclusion
from backend.models.signals import AgentSignal, Direction, Strength

logger = logging.getLogger(__name__)

_BUY_THRESHOLD = 0.2
_SELL_THRESHOLD = -0.2
_STRONG_THRESHOLD = 0.5
_MODERATE_THRESHOLD = 0.25
_CONSISTENCY_HIGH_STD = 0.3


def synthesize(
    profile: CompanyProfile,
    conclusions: list[SubConclusion],
    tasks: list[AnalysisTask],
) -> AgentSignal:
    """
    Cross-task synthesis: compute weighted sentiment, direction, and confidence.

    Args:
        profile: CompanyProfile from Step 1.
        conclusions: List of SubConclusion from Step 3.
        tasks: List of AnalysisTask from Step 2 (provides weights).

    Returns:
        Frozen AgentSignal.
    """
    if not conclusions:
        return AgentSignal(
            agent_name="fundamental",
            direction=Direction.NEUTRAL,
            strength=Strength.WEAK,
            confidence=0.0,
            reasoning="No analysis conclusions available.",
        )

    # Build weight lookup
    weight_by_id = {t.task_id: t.weight for t in tasks}

    # Weighted sentiment
    weighted_sum = 0.0
    weight_total = 0.0
    scores: list[float] = []

    for conclusion in conclusions:
        task_weight = weight_by_id.get(conclusion.task_id, 1.0 / len(conclusions))
        effective_weight = task_weight * conclusion.confidence
        weighted_sum += effective_weight * conclusion.sentiment_score
        weight_total += effective_weight
        scores.append(conclusion.sentiment_score)

    if weight_total == 0:
        weighted_sentiment = 0.0
    else:
        weighted_sentiment = weighted_sum / weight_total

    # Cross-task consistency via std dev
    consistency_factor = _compute_consistency_factor(scores)

    # Direction
    direction = _map_direction(weighted_sentiment)

    # Strength
    strength = _map_strength(abs(weighted_sentiment), direction)

    # Overall confidence
    mean_confidence = sum(c.confidence for c in conclusions) / len(conclusions)
    final_confidence = float(min(1.0, max(0.0, mean_confidence * consistency_factor)))

    # Reasoning: top 2 conclusions by confidence
    top_conclusions = sorted(conclusions, key=lambda c: c.confidence, reverse=True)[:2]
    reasoning_parts = [c.conclusion for c in top_conclusions if c.conclusion]
    reasoning = " | ".join(reasoning_parts) if reasoning_parts else (
        f"Weighted sentiment score: {weighted_sentiment:.3f}"
    )

    return AgentSignal(
        agent_name="fundamental",
        direction=direction,
        strength=strength,
        confidence=final_confidence,
        reasoning=reasoning,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_consistency_factor(scores: list[float]) -> float:
    """
    Compute a consistency factor from the std dev of sentiment scores.

    Low std (< 0.3)  → factor close to 1.0 (high consistency)
    High std         → factor < 1.0 (reduces confidence)
    """
    if len(scores) < 2:
        return 1.0

    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = math.sqrt(variance)

    if std < _CONSISTENCY_HIGH_STD:
        return 1.0

    # Linear decay: std=0.3 → 1.0, std=1.0 → ~0.57
    return float(max(0.3, 1.0 - (std - _CONSISTENCY_HIGH_STD)))


def _map_direction(score: float) -> Direction:
    if score > _BUY_THRESHOLD:
        return Direction.BUY
    if score < _SELL_THRESHOLD:
        return Direction.SELL
    return Direction.NEUTRAL


def _map_strength(abs_score: float, direction: Direction) -> Strength:
    if direction == Direction.NEUTRAL:
        return Strength.WEAK

    if abs_score > _STRONG_THRESHOLD:
        return Strength.STRONG
    if abs_score > _MODERATE_THRESHOLD:
        return Strength.MODERATE
    return Strength.WEAK
