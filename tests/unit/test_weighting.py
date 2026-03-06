"""Unit tests for weighting.py — regime modifiers, normalization, degradation."""

import pytest

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.technical import MarketRegime, RegimeType
from backend.decision_hub.weighting import compute_weights, BASE_WEIGHTS, REGIME_MODIFIERS


def make_signal(
    agent_name: str,
    direction: Direction = Direction.BUY,
    strength: Strength = Strength.MODERATE,
    confidence: float = 0.7,
) -> AgentSignal:
    return AgentSignal(
        agent_name=agent_name,
        direction=direction,
        strength=strength,
        confidence=confidence,
        reasoning="test",
    )


def trending_regime() -> MarketRegime:
    return MarketRegime(
        regime_type=RegimeType.TRENDING,
        trend_strength=0.8,
        volatility=0.5,
        interpretation="Trending",
    )


def ranging_regime() -> MarketRegime:
    return MarketRegime(
        regime_type=RegimeType.RANGING,
        trend_strength=0.2,
        volatility=0.3,
        interpretation="Ranging",
    )


def high_vol_regime() -> MarketRegime:
    return MarketRegime(
        regime_type=RegimeType.HIGH_VOLATILITY,
        trend_strength=0.5,
        volatility=2.5,
        interpretation="High volatility",
    )


class TestWeightNormalization:
    def test_weights_sum_to_one(self):
        sigs = [
            make_signal("technical", confidence=0.85),
            make_signal("sentiment", confidence=0.72),
            make_signal("fundamental", confidence=0.55),
        ]
        allocs = compute_weights(sigs, trending_regime())
        total = sum(a.final_weight for a in allocs)
        assert pytest.approx(total, abs=1e-9) == 1.0

    def test_weights_sum_to_one_no_regime(self):
        sigs = [
            make_signal("technical", confidence=0.7),
            make_signal("sentiment", confidence=0.6),
        ]
        allocs = compute_weights(sigs)
        assert pytest.approx(sum(a.final_weight for a in allocs), abs=1e-9) == 1.0

    def test_weights_sum_to_one_single_agent(self):
        sigs = [make_signal("technical", confidence=0.9)]
        allocs = compute_weights(sigs)
        assert pytest.approx(allocs[0].final_weight, abs=1e-9) == 1.0


class TestRegimeModifiers:
    def test_trending_boosts_technical(self):
        """In trending regime, technical should get the highest weight."""
        sigs = [
            make_signal("technical", confidence=0.8),
            make_signal("sentiment", confidence=0.8),
            make_signal("fundamental", confidence=0.8),
        ]
        allocs = compute_weights(sigs, trending_regime())
        weight_map = {a.agent_name: a.final_weight for a in allocs}
        assert weight_map["technical"] > weight_map["sentiment"]
        assert weight_map["technical"] > weight_map["fundamental"]

    def test_trending_reduces_sentiment(self):
        sigs = [
            make_signal("technical", confidence=0.8),
            make_signal("sentiment", confidence=0.8),
            make_signal("fundamental", confidence=0.8),
        ]
        allocs_trending = compute_weights(sigs, trending_regime())
        allocs_no_regime = compute_weights(sigs)
        map_trending = {a.agent_name: a.final_weight for a in allocs_trending}
        map_default = {a.agent_name: a.final_weight for a in allocs_no_regime}
        # In trending, sentiment should have lower weight than default
        assert map_trending["sentiment"] < map_default["sentiment"]

    def test_high_vol_boosts_fundamental(self):
        sigs = [
            make_signal("technical", confidence=0.75),
            make_signal("sentiment", confidence=0.75),
            make_signal("fundamental", confidence=0.75),
        ]
        allocs = compute_weights(sigs, high_vol_regime())
        weight_map = {a.agent_name: a.final_weight for a in allocs}
        assert weight_map["fundamental"] > weight_map["sentiment"]

    def test_regime_modifier_recorded(self):
        sigs = [make_signal("technical", confidence=0.85)]
        allocs = compute_weights(sigs, trending_regime())
        assert allocs[0].regime_modifier == REGIME_MODIFIERS[RegimeType.TRENDING]["technical"]

    def test_no_regime_modifier_is_one(self):
        sigs = [make_signal("technical", confidence=0.85)]
        allocs = compute_weights(sigs, regime=None)
        assert allocs[0].regime_modifier == 1.0


class TestDesignDocExample:
    """Verify the exact numbers from the design doc worked example."""

    def test_technical_raw_weight(self):
        """TRENDING: tech = base(0.40) × modifier(1.2) × confidence(0.85) = 0.408"""
        sigs = [
            make_signal("technical", confidence=0.85),
            make_signal("sentiment", confidence=0.72),
            make_signal("fundamental", confidence=0.55),
        ]
        allocs = compute_weights(sigs, trending_regime())
        tech = next(a for a in allocs if a.agent_name == "technical")
        raw = tech.base_weight * tech.regime_modifier * tech.confidence
        assert pytest.approx(raw, abs=1e-9) == 0.40 * 1.2 * 0.85

    def test_technical_final_weight(self):
        """Design doc: tech normalized weight ≈ 0.547"""
        sigs = [
            make_signal("technical", confidence=0.85),
            make_signal("sentiment", confidence=0.72),
            make_signal("fundamental", confidence=0.55),
        ]
        allocs = compute_weights(sigs, trending_regime())
        tech = next(a for a in allocs if a.agent_name == "technical")
        assert pytest.approx(tech.final_weight, abs=0.001) == 0.547

    def test_sentiment_final_weight(self):
        """Design doc: sent normalized weight ≈ 0.232"""
        sigs = [
            make_signal("technical", confidence=0.85),
            make_signal("sentiment", confidence=0.72),
            make_signal("fundamental", confidence=0.55),
        ]
        allocs = compute_weights(sigs, trending_regime())
        sent = next(a for a in allocs if a.agent_name == "sentiment")
        assert pytest.approx(sent.final_weight, abs=0.001) == 0.232

    def test_fundamental_final_weight(self):
        """Design doc: fund normalized weight ≈ 0.221"""
        sigs = [
            make_signal("technical", confidence=0.85),
            make_signal("sentiment", confidence=0.72),
            make_signal("fundamental", confidence=0.55),
        ]
        allocs = compute_weights(sigs, trending_regime())
        fund = next(a for a in allocs if a.agent_name == "fundamental")
        assert pytest.approx(fund.final_weight, abs=0.001) == 0.221


class TestDegradationWeights:
    def test_two_agent_weights_still_normalize(self):
        """When fundamental agent is absent, remaining two still sum to 1.0."""
        sigs = [
            make_signal("technical", confidence=0.85),
            make_signal("sentiment", confidence=0.72),
        ]
        allocs = compute_weights(sigs, trending_regime())
        assert len(allocs) == 2
        assert pytest.approx(sum(a.final_weight for a in allocs), abs=1e-9) == 1.0

    def test_one_agent_weight_is_one(self):
        sigs = [make_signal("technical", confidence=0.9)]
        allocs = compute_weights(sigs, trending_regime())
        assert allocs[0].final_weight == pytest.approx(1.0, abs=1e-9)

    def test_zero_signals_raises(self):
        with pytest.raises(ValueError):
            compute_weights([])

    def test_confidence_affects_weight_ordering(self):
        """Higher confidence → higher weight (all else equal)."""
        sigs = [
            make_signal("technical", confidence=0.9),
            make_signal("sentiment", confidence=0.5),
        ]
        allocs = compute_weights(sigs, regime=None)
        weight_map = {a.agent_name: a.final_weight for a in allocs}
        # technical base(0.40) × 1.0 × 0.9 = 0.36 vs sentiment base(0.30) × 1.0 × 0.5 = 0.15
        # so technical should dominate
        assert weight_map["technical"] > weight_map["sentiment"]
