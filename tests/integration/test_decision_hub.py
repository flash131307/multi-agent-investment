"""Integration tests for Decision Hub — full pipeline, degradation, pressure scenarios."""

import pytest

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.technical import MarketRegime, RegimeType
from backend.models.decision import RiskMode
from backend.decision_hub.hub import DecisionHub


def signal(
    agent_name: str,
    direction: Direction,
    strength: Strength,
    confidence: float,
) -> AgentSignal:
    return AgentSignal(
        agent_name=agent_name,
        direction=direction,
        strength=strength,
        confidence=confidence,
        reasoning=f"{agent_name} says {direction.value}.",
    )


def trending() -> MarketRegime:
    return MarketRegime(
        regime_type=RegimeType.TRENDING,
        trend_strength=0.8,
        volatility=0.5,
        interpretation="Trending",
    )


@pytest.fixture
def hub() -> DecisionHub:
    return DecisionHub()


# ---------------------------------------------------------------------------
# Design doc worked example
# ---------------------------------------------------------------------------

class TestDesignDocFullPipeline:
    def test_full_pipeline_returns_buy(self, hub: DecisionHub):
        """Design doc: BUY/STRONG/0.85 + BUY/MODERATE/0.72 + SELL/WEAK/0.55 → BUY"""
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.MODERATE, 0.72),
            signal("fundamental", Direction.SELL, Strength.WEAK, 0.55),
        ]
        result = hub.fuse(signals, trending())
        assert result.direction == Direction.BUY

    def test_full_pipeline_risk_mode(self, hub: DecisionHub):
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.MODERATE, 0.72),
            signal("fundamental", Direction.SELL, Strength.WEAK, 0.55),
        ]
        result = hub.fuse(signals, trending())
        assert result.consistency.risk_mode == RiskMode.RISK

    def test_full_pipeline_score_positive(self, hub: DecisionHub):
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.MODERATE, 0.72),
            signal("fundamental", Direction.SELL, Strength.WEAK, 0.55),
        ]
        result = hub.fuse(signals, trending())
        assert result.aggregated_score > 0.25

    def test_full_pipeline_result_structure(self, hub: DecisionHub):
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.MODERATE, 0.72),
            signal("fundamental", Direction.SELL, Strength.WEAK, 0.55),
        ]
        result = hub.fuse(signals, trending())
        assert len(result.signals) == 3
        assert len(result.weights) == 3
        assert 0.0 <= result.confidence <= 1.0
        assert result.consistency is not None


# ---------------------------------------------------------------------------
# Pressure scenarios from design doc
# ---------------------------------------------------------------------------

class TestPressureScenarios:
    def test_scenario_unanimous_buy(self, hub: DecisionHub):
        """All 3 agents strongly agree on BUY → NORMAL mode, high confidence."""
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.92),
            signal("sentiment", Direction.BUY, Strength.STRONG, 0.88),
            signal("fundamental", Direction.BUY, Strength.MODERATE, 0.85),
        ]
        result = hub.fuse(signals, trending())
        assert result.direction == Direction.BUY
        assert result.consistency.risk_mode == RiskMode.NORMAL
        assert result.confidence > 0.7

    def test_scenario_unanimous_sell(self, hub: DecisionHub):
        """All 3 agents strongly agree on SELL → NORMAL mode."""
        signals = [
            signal("technical", Direction.SELL, Strength.STRONG, 0.90),
            signal("sentiment", Direction.SELL, Strength.STRONG, 0.85),
            signal("fundamental", Direction.SELL, Strength.MODERATE, 0.80),
        ]
        result = hub.fuse(signals, trending())
        assert result.direction == Direction.SELL
        assert result.consistency.risk_mode == RiskMode.NORMAL

    def test_scenario_tech_vs_fundamentals(self, hub: DecisionHub):
        """Technical BUY, but Sentiment+Fundamental SELL → low consistency → RISK mode."""
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.SELL, Strength.MODERATE, 0.72),
            signal("fundamental", Direction.SELL, Strength.STRONG, 0.80),
        ]
        result = hub.fuse(signals)
        assert result.consistency.risk_mode in (RiskMode.RISK, RiskMode.CAUTIOUS)

    def test_scenario_all_neutral(self, hub: DecisionHub):
        """All agents uncertain → NEUTRAL direction."""
        signals = [
            signal("technical", Direction.NEUTRAL, Strength.WEAK, 0.4),
            signal("sentiment", Direction.NEUTRAL, Strength.WEAK, 0.35),
            signal("fundamental", Direction.NEUTRAL, Strength.WEAK, 0.45),
        ]
        result = hub.fuse(signals)
        assert result.direction == Direction.NEUTRAL

    def test_scenario_mixed_high_confidence(self, hub: DecisionHub):
        """Split signals but high individual confidence → RISK mode but defined direction."""
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.95),
            signal("sentiment", Direction.SELL, Strength.MODERATE, 0.90),
            signal("fundamental", Direction.NEUTRAL, Strength.WEAK, 0.85),
        ]
        result = hub.fuse(signals, trending())
        assert result.direction in (Direction.BUY, Direction.NEUTRAL, Direction.SELL)
        assert result.consistency.risk_mode == RiskMode.RISK


# ---------------------------------------------------------------------------
# Degradation modes
# ---------------------------------------------------------------------------

class TestDegradationModes:
    def test_three_agents_no_warning(self, hub: DecisionHub):
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.MODERATE, 0.72),
            signal("fundamental", Direction.BUY, Strength.MODERATE, 0.68),
        ]
        result = hub.fuse(signals)
        assert len(result.warnings) == 0

    def test_two_agents_has_warning(self, hub: DecisionHub):
        signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.MODERATE, 0.72),
        ]
        result = hub.fuse(signals)
        assert len(result.warnings) == 1
        assert "2 of 3" in result.warnings[0]

    def test_one_agent_has_warning(self, hub: DecisionHub):
        signals = [signal("technical", Direction.BUY, Strength.STRONG, 0.85)]
        result = hub.fuse(signals)
        assert len(result.warnings) == 1
        assert "1 of 3" in result.warnings[0]

    def test_two_agent_confidence_lower_than_three(self, hub: DecisionHub):
        """2-agent mode applies ×0.8 degradation on top of math."""
        three_signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.STRONG, 0.85),
            signal("fundamental", Direction.BUY, Strength.STRONG, 0.85),
        ]
        two_signals = three_signals[:2]
        result_three = hub.fuse(three_signals)
        result_two = hub.fuse(two_signals)
        assert result_two.confidence <= result_three.confidence

    def test_one_agent_confidence_is_lowest(self, hub: DecisionHub):
        """1-agent mode applies ×0.5 — lowest confidence multiplier."""
        three_signals = [
            signal("technical", Direction.BUY, Strength.STRONG, 0.85),
            signal("sentiment", Direction.BUY, Strength.STRONG, 0.85),
            signal("fundamental", Direction.BUY, Strength.STRONG, 0.85),
        ]
        one_signal = three_signals[:1]
        result_three = hub.fuse(three_signals)
        result_one = hub.fuse(one_signal)
        assert result_one.confidence < result_three.confidence

    def test_zero_agents_raises(self, hub: DecisionHub):
        with pytest.raises(ValueError, match="Cannot fuse zero signals"):
            hub.fuse([])

    def test_too_many_agents_raises(self, hub: DecisionHub):
        sigs = [signal(f"agent{i}", Direction.BUY, Strength.MODERATE, 0.7) for i in range(4)]
        with pytest.raises(ValueError, match="Maximum 3"):
            hub.fuse(sigs)


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------

class TestOutputContract:
    def test_result_is_immutable(self, hub: DecisionHub):
        signals = [signal("technical", Direction.BUY, Strength.STRONG, 0.85)]
        result = hub.fuse(signals)
        with pytest.raises(Exception):
            result.direction = Direction.SELL  # type: ignore[misc]

    def test_confidence_always_in_bounds(self, hub: DecisionHub):
        for direction in Direction:
            for strength in Strength:
                if direction == Direction.NEUTRAL and strength == Strength.STRONG:
                    continue
                sigs = [signal("technical", direction, strength, 0.5)]
                result = hub.fuse(sigs)
                assert 0.0 <= result.confidence <= 1.0

    def test_reasoning_placeholder_is_empty_string(self, hub: DecisionHub):
        """Hub sets reasoning=''; reasoning.py fills it in afterwards."""
        sigs = [signal("technical", Direction.BUY, Strength.STRONG, 0.85)]
        result = hub.fuse(sigs)
        assert result.reasoning == ""

    def test_no_regime_still_works(self, hub: DecisionHub):
        sigs = [signal("technical", Direction.BUY, Strength.STRONG, 0.85)]
        result = hub.fuse(sigs, regime=None)
        assert result.direction is not None
