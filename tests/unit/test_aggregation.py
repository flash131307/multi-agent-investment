"""Unit tests for aggregation.py — score computation and direction thresholds."""

import pytest

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.decision import WeightAllocation, ConsistencyScore, RiskMode
from backend.decision_hub.aggregation import aggregate


def make_signal(
    agent_name: str,
    direction: Direction,
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


def make_weight(agent_name: str, final_weight: float) -> WeightAllocation:
    return WeightAllocation(
        agent_name=agent_name,
        base_weight=0.33,
        regime_modifier=1.0,
        confidence=0.7,
        final_weight=final_weight,
    )


def make_consistency(risk_mode: RiskMode = RiskMode.NORMAL) -> ConsistencyScore:
    return ConsistencyScore(
        direction_score=0.8,
        strength_score=0.8,
        confidence_score=0.8,
        raw_consistency=0.8,
        risk_mode=risk_mode,
        final_consistency=0.8,
    )


class TestDesignDocWorkedExample:
    """Exact numbers from the design doc must pass."""

    def setup_method(self):
        self.signals = [
            AgentSignal(agent_name="technical", direction=Direction.BUY,
                        strength=Strength.STRONG, confidence=0.85, reasoning="r"),
            AgentSignal(agent_name="sentiment", direction=Direction.BUY,
                        strength=Strength.MODERATE, confidence=0.72, reasoning="r"),
            AgentSignal(agent_name="fundamental", direction=Direction.SELL,
                        strength=Strength.WEAK, confidence=0.55, reasoning="r"),
        ]
        self.weights = [
            make_weight("technical", 0.547),
            make_weight("sentiment", 0.232),
            make_weight("fundamental", 0.221),
        ]
        self.consistency = ConsistencyScore(
            direction_score=0.3,
            strength_score=0.7,
            confidence_score=0.70,
            raw_consistency=0.115,
            risk_mode=RiskMode.RISK,
            final_consistency=0.069,
        )

    def test_direction_is_buy(self):
        direction, _, _ = aggregate(self.signals, self.weights, self.consistency)
        assert direction == Direction.BUY

    def test_score_matches_design_doc(self):
        """Design doc: score = +0.547 + +0.162 - 0.088 = +0.621"""
        _, _, score = aggregate(self.signals, self.weights, self.consistency)
        # tech: +1 × 1.0 × 0.547 = +0.547
        # sent: +1 × 0.7 × 0.232 = +0.1624
        # fund: -1 × 0.4 × 0.221 = -0.0884
        expected_score = +0.547 + (0.7 * 0.232) - (0.4 * 0.221)
        assert pytest.approx(score, abs=0.001) == expected_score

    def test_confidence_is_dampened_by_risk_mode(self):
        """Risk mode RISK → multiplier 0.6 → confidence < raw."""
        _, confidence, _ = aggregate(self.signals, self.weights, self.consistency)
        # Confidence should be reduced by RISK multiplier (0.6)
        assert confidence < 0.8


class TestDirectionThresholds:
    def _run(self, score_setup: list[tuple]) -> Direction:
        """Helper: build signals+weights with matching scores, run aggregate."""
        signals = []
        weights = []
        for agent_name, direction, strength, confidence, weight in score_setup:
            signals.append(make_signal(agent_name, direction, strength, confidence))
            weights.append(make_weight(agent_name, weight))
        consistency = make_consistency(RiskMode.NORMAL)
        direction, _, _ = aggregate(signals, weights, consistency)
        return direction

    def test_score_above_threshold_is_buy(self):
        """score = +1.0 × 1.0 × 1.0 = +1.0 → BUY"""
        d = self._run([("technical", Direction.BUY, Strength.STRONG, 0.9, 1.0)])
        assert d == Direction.BUY

    def test_score_below_threshold_is_sell(self):
        """score = -1.0 × 1.0 × 1.0 = -1.0 → SELL"""
        d = self._run([("technical", Direction.SELL, Strength.STRONG, 0.9, 1.0)])
        assert d == Direction.SELL

    def test_neutral_signal_gives_neutral(self):
        d = self._run([("technical", Direction.NEUTRAL, Strength.WEAK, 0.5, 1.0)])
        assert d == Direction.NEUTRAL

    def test_balanced_buy_sell_gives_neutral(self):
        """Equal BUY and SELL with equal weights → score ≈ 0 → NEUTRAL."""
        d = self._run([
            ("technical", Direction.BUY, Strength.STRONG, 0.8, 0.5),
            ("sentiment", Direction.SELL, Strength.STRONG, 0.8, 0.5),
        ])
        assert d == Direction.NEUTRAL

    def test_buy_threshold_boundary(self):
        """score just above +0.25 → BUY (MODERATE × 1.0 × weight = 0.7 × w)"""
        # Need score > 0.25: weight > 0.25/0.7 ≈ 0.357, so use weight 0.4
        signals = [
            make_signal("a", Direction.BUY, Strength.MODERATE, 0.8),
            make_signal("b", Direction.NEUTRAL, Strength.WEAK, 0.5),
        ]
        weights = [make_weight("a", 0.4), make_weight("b", 0.6)]
        consistency = make_consistency(RiskMode.NORMAL)
        direction, _, score = aggregate(signals, weights, consistency)
        # score = +1 × 0.7 × 0.4 + 0 × 0.4 × 0.6 = 0.28 > 0.25
        assert score == pytest.approx(0.28, abs=1e-9)
        assert direction == Direction.BUY


class TestConfidenceComputation:
    def test_confidence_dampened_by_risk_mode(self):
        sigs = [make_signal("a", Direction.BUY, Strength.STRONG, 0.9)]
        weights = [make_weight("a", 1.0)]
        consistency_risk = make_consistency(RiskMode.RISK)
        consistency_normal = make_consistency(RiskMode.NORMAL)
        _, conf_risk, _ = aggregate(sigs, weights, consistency_risk)
        _, conf_normal, _ = aggregate(sigs, weights, consistency_normal)
        assert conf_risk < conf_normal

    def test_confidence_bounded_zero_to_one(self):
        sigs = [make_signal("a", Direction.BUY, Strength.STRONG, 0.95)]
        weights = [make_weight("a", 1.0)]
        consistency = make_consistency(RiskMode.NORMAL)
        _, confidence, _ = aggregate(sigs, weights, consistency)
        assert 0.0 <= confidence <= 1.0


class TestEdgeCases:
    def test_mismatched_signals_and_weights_raises(self):
        sigs = [make_signal("a", Direction.BUY)]
        weights = [make_weight("a", 0.5), make_weight("b", 0.5)]
        consistency = make_consistency()
        with pytest.raises(ValueError, match="must match"):
            aggregate(sigs, weights, consistency)

    def test_all_neutral_score_is_zero(self):
        sigs = [
            make_signal("a", Direction.NEUTRAL, Strength.WEAK, 0.5),
            make_signal("b", Direction.NEUTRAL, Strength.WEAK, 0.5),
        ]
        weights = [make_weight("a", 0.5), make_weight("b", 0.5)]
        consistency = make_consistency()
        _, _, score = aggregate(sigs, weights, consistency)
        assert score == pytest.approx(0.0, abs=1e-9)
