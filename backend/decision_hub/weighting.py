"""
Dynamic weight allocation for the Decision Hub.

Each agent has a base weight that is adjusted by:
1. Market regime modifier (e.g., trend-following agents get a boost in trending markets)
2. Agent's own confidence score

Final weights are normalized to sum to 1.0.
"""

from backend.models.signals import AgentSignal
from backend.models.technical import RegimeType, MarketRegime
from backend.models.decision import WeightAllocation

# Base weights — must sum to 1.0
BASE_WEIGHTS: dict[str, float] = {
    "technical": 0.40,
    "sentiment": 0.30,
    "fundamental": 0.30,
}

# Per-regime modifiers for each agent type
# TRENDING: technical analysis is more reliable (trend is your friend)
# RANGING: fundamentals and sentiment matter more than technical momentum
# HIGH_VOLATILITY: fundamentals anchor value; sentiment is noise-heavy
REGIME_MODIFIERS: dict[RegimeType, dict[str, float]] = {
    RegimeType.TRENDING: {
        "technical": 1.2,
        "sentiment": 0.8,
        "fundamental": 1.0,
    },
    RegimeType.RANGING: {
        "technical": 0.9,
        "sentiment": 1.1,
        "fundamental": 1.0,
    },
    RegimeType.HIGH_VOLATILITY: {
        "technical": 1.0,
        "sentiment": 0.7,
        "fundamental": 1.3,
    },
}

# Default modifier when no regime is provided (neutral)
_DEFAULT_MODIFIER: dict[str, float] = {
    "technical": 1.0,
    "sentiment": 1.0,
    "fundamental": 1.0,
}


def _get_regime_modifier(agent_name: str, regime: MarketRegime | None) -> float:
    """Return the regime modifier for the given agent, defaulting to 1.0."""
    if regime is None:
        return _DEFAULT_MODIFIER.get(agent_name, 1.0)
    modifiers = REGIME_MODIFIERS.get(regime.regime_type, _DEFAULT_MODIFIER)
    return modifiers.get(agent_name, 1.0)


def _get_base_weight(agent_name: str, all_agent_names: list[str]) -> float:
    """
    Return the base weight for an agent.

    For known agent names (technical/sentiment/fundamental), use the preset table.
    For unknown agents, distribute remaining weight equally.
    """
    if agent_name in BASE_WEIGHTS:
        return BASE_WEIGHTS[agent_name]
    # Fallback: equal share of remaining weight after known agents
    known = sum(BASE_WEIGHTS[n] for n in all_agent_names if n in BASE_WEIGHTS)
    unknown_names = [n for n in all_agent_names if n not in BASE_WEIGHTS]
    remaining = max(0.0, 1.0 - known)
    if unknown_names:
        return remaining / len(unknown_names)
    return 1.0 / len(all_agent_names)


def compute_weights(
    signals: list[AgentSignal],
    regime: MarketRegime | None = None,
) -> list[WeightAllocation]:
    """
    Compute normalized dynamic weights for each agent signal.

    Args:
        signals: 1–3 agent signals.
        regime: Market regime from the technical agent (optional).

    Returns:
        List of WeightAllocation with final normalized weights summing to 1.0.
    """
    if not signals:
        raise ValueError("At least one signal is required.")

    agent_names = [s.agent_name for s in signals]

    # Step 1: raw = base_weight × regime_modifier × confidence
    raw_weights: list[tuple[AgentSignal, float, float, float]] = []
    for sig in signals:
        base = _get_base_weight(sig.agent_name, agent_names)
        modifier = _get_regime_modifier(sig.agent_name, regime)
        raw = base * modifier * sig.confidence
        raw_weights.append((sig, base, modifier, raw))

    total = sum(raw for _, _, _, raw in raw_weights)

    # Step 2: normalize
    allocations = []
    for sig, base, modifier, raw in raw_weights:
        final = raw / total if total > 0 else 1.0 / len(signals)
        allocations.append(
            WeightAllocation(
                agent_name=sig.agent_name,
                base_weight=base,
                regime_modifier=modifier,
                confidence=sig.confidence,
                final_weight=final,
            )
        )

    return allocations
