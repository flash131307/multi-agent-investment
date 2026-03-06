"""Unit tests for consistency.py — direction gate, formula, risk mode boundaries."""

import math
import pytest

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.decision import RiskMode
from backend.decision_hub.consistency import (
    compute_consistency,
    _compute_direction_score,
    _compute_strength_score,
    _compute_confidence_score,
)


def make_signal(
    direction: Direction,
    strength: Strength = Strength.MODERATE,
    confidence: float = 0.7,
    agent_name: str = "test",
) -> AgentSignal:
    return AgentSignal(
        agent_name=agent_name,
        direction=direction,
        strength=strength,
        confidence=confidence,
        reasoning="Test signal.",
    )


B = Direction.BUY
S = Direction.SELL
N = Direction.NEUTRAL


# ---------------------------------------------------------------------------
# Direction gate — 3 agents
# ---------------------------------------------------------------------------

class TestDirectionGate3Agents:
    def _signals(self, *dirs: Direction) -> list[AgentSignal]:
        return [make_signal(d, agent_name=f"a{i}") for i, d in enumerate(dirs)]

    def test_all_buy(self):
        assert _compute_direction_score(self._signals(B, B, B)) == 1.0

    def test_all_sell(self):
        assert _compute_direction_score(self._signals(S, S, S)) == 1.0

    def test_two_buy_one_neutral(self):
        assert _compute_direction_score(self._signals(B, B, N)) == 0.7

    def test_two_sell_one_neutral(self):
        assert _compute_direction_score(self._signals(S, S, N)) == 0.7

    def test_one_buy_two_neutral(self):
        assert _compute_direction_score(self._signals(B, N, N)) == 0.4

    def test_one_sell_two_neutral(self):
        assert _compute_direction_score(self._signals(S, N, N)) == 0.4

    def test_two_buy_one_sell(self):
        assert _compute_direction_score(self._signals(B, B, S)) == 0.3

    def test_one_buy_two_sell(self):
        assert _compute_direction_score(self._signals(B, S, S)) == 0.0

    def test_complete_split(self):
        assert _compute_direction_score(self._signals(B, S, N)) == 0.1

    def test_all_neutral(self):
        assert _compute_direction_score(self._signals(N, N, N)) == 0.5

    def test_order_independent_two_buy_one_neutral(self):
        """Gate should give same result regardless of agent ordering."""
        sigs1 = self._signals(B, N, B)
        sigs2 = self._signals(N, B, B)
        assert _compute_direction_score(sigs1) == _compute_direction_score(sigs2) == 0.7


# ---------------------------------------------------------------------------
# Direction gate — 2 agents
# ---------------------------------------------------------------------------

class TestDirectionGate2Agents:
    def _signals(self, *dirs: Direction) -> list[AgentSignal]:
        return [make_signal(d, agent_name=f"a{i}") for i, d in enumerate(dirs)]

    def test_both_buy(self):
        assert _compute_direction_score(self._signals(B, B)) == 1.0

    def test_both_sell(self):
        assert _compute_direction_score(self._signals(S, S)) == 1.0

    def test_buy_and_neutral(self):
        assert _compute_direction_score(self._signals(B, N)) == 0.7

    def test_sell_and_neutral(self):
        assert _compute_direction_score(self._signals(S, N)) == 0.7

    def test_both_neutral(self):
        assert _compute_direction_score(self._signals(N, N)) == 0.5

    def test_buy_vs_sell(self):
        assert _compute_direction_score(self._signals(B, S)) == 0.0


# ---------------------------------------------------------------------------
# Direction gate — 1 agent
# ---------------------------------------------------------------------------

class TestDirectionGate1Agent:
    def test_single_buy(self):
        assert _compute_direction_score([make_signal(B)]) == 0.5

    def test_single_sell(self):
        assert _compute_direction_score([make_signal(S)]) == 0.5

    def test_single_neutral(self):
        assert _compute_direction_score([make_signal(N)]) == 0.5


# ---------------------------------------------------------------------------
# Strength score
# ---------------------------------------------------------------------------

class TestStrengthScore:
    def test_all_strong(self):
        sigs = [make_signal(B, Strength.STRONG), make_signal(B, Strength.STRONG)]
        assert _compute_strength_score(sigs) == 1.0

    def test_strong_vs_weak(self):
        # |1.0 - 0.4| / 2.0 = 0.3, score = 0.7
        sigs = [
            make_signal(B, Strength.STRONG),
            make_signal(S, Strength.WEAK),
        ]
        assert pytest.approx(_compute_strength_score(sigs), abs=1e-9) == 0.7

    def test_strong_vs_moderate(self):
        # |1.0 - 0.7| / 2.0 = 0.15, score = 0.85
        sigs = [
            make_signal(B, Strength.STRONG),
            make_signal(B, Strength.MODERATE),
        ]
        assert pytest.approx(_compute_strength_score(sigs), abs=1e-9) == 0.85

    def test_all_neutral_returns_one(self):
        """All neutral agents — no directional strength to compare."""
        sigs = [make_signal(N, Strength.WEAK), make_signal(N, Strength.WEAK)]
        assert _compute_strength_score(sigs) == 1.0

    def test_excludes_neutral_agents(self):
        """Neutral agent's strength is excluded from the calculation."""
        sigs = [
            make_signal(B, Strength.STRONG),
            make_signal(N, Strength.WEAK),    # excluded
        ]
        # Only one directional agent → strength score = 1.0
        assert _compute_strength_score(sigs) == 1.0

    def test_design_doc_example(self):
        """Design doc: STRONG vs WEAK (with MODERATE in between, excluded here)."""
        sigs = [
            make_signal(B, Strength.STRONG, agent_name="technical"),
            make_signal(B, Strength.MODERATE, agent_name="sentiment"),
            make_signal(S, Strength.WEAK, agent_name="fundamental"),
        ]
        # max=1.0 (STRONG), min=0.4 (WEAK), gap=0.3, score=0.7
        assert pytest.approx(_compute_strength_score(sigs), abs=1e-9) == 0.7


# ---------------------------------------------------------------------------
# Confidence score
# ---------------------------------------------------------------------------

class TestConfidenceScore:
    def test_equal_confidence(self):
        sigs = [make_signal(B, confidence=0.8), make_signal(B, confidence=0.8)]
        assert _compute_confidence_score(sigs) == 1.0

    def test_design_doc_example(self):
        # max=0.85, min=0.55, gap=0.30, score=0.70
        sigs = [
            make_signal(B, confidence=0.85),
            make_signal(B, confidence=0.72),
            make_signal(S, confidence=0.55),
        ]
        assert pytest.approx(_compute_confidence_score(sigs), abs=1e-9) == 0.70

    def test_single_signal(self):
        assert _compute_confidence_score([make_signal(B, confidence=0.9)]) == 1.0

    def test_wide_spread(self):
        # max=1.0, min=0.0, score=0.0
        sigs = [make_signal(B, confidence=1.0), make_signal(S, confidence=0.0)]
        assert pytest.approx(_compute_confidence_score(sigs), abs=1e-9) == 0.0


# ---------------------------------------------------------------------------
# Full consistency formula + risk mode
# ---------------------------------------------------------------------------

class TestConsistency:
    def _three_signals(self) -> list[AgentSignal]:
        return [
            AgentSignal(agent_name="technical", direction=B, strength=Strength.STRONG,
                        confidence=0.85, reasoning="r"),
            AgentSignal(agent_name="sentiment", direction=B, strength=Strength.MODERATE,
                        confidence=0.72, reasoning="r"),
            AgentSignal(agent_name="fundamental", direction=S, strength=Strength.WEAK,
                        confidence=0.55, reasoning="r"),
        ]

    def test_design_doc_direction_score(self):
        result = compute_consistency(self._three_signals())
        assert result.direction_score == 0.3

    def test_design_doc_strength_score(self):
        result = compute_consistency(self._three_signals())
        assert pytest.approx(result.strength_score, abs=1e-9) == 0.7

    def test_design_doc_confidence_score(self):
        result = compute_consistency(self._three_signals())
        assert pytest.approx(result.confidence_score, abs=1e-9) == 0.70

    def test_design_doc_raw_consistency(self):
        result = compute_consistency(self._three_signals())
        expected = 0.3 ** 1.5 * (0.6 * 0.7 + 0.4 * 0.70)
        assert pytest.approx(result.raw_consistency, abs=1e-6) == expected

    def test_design_doc_risk_mode(self):
        result = compute_consistency(self._three_signals())
        assert result.risk_mode == RiskMode.RISK

    def test_high_consistency_is_normal(self):
        sigs = [
            AgentSignal(agent_name="technical", direction=B, strength=Strength.STRONG,
                        confidence=0.9, reasoning="r"),
            AgentSignal(agent_name="sentiment", direction=B, strength=Strength.STRONG,
                        confidence=0.88, reasoning="r"),
            AgentSignal(agent_name="fundamental", direction=B, strength=Strength.MODERATE,
                        confidence=0.85, reasoning="r"),
        ]
        result = compute_consistency(sigs)
        assert result.risk_mode == RiskMode.NORMAL
        assert result.final_consistency >= 0.7

    def test_medium_consistency_is_cautious(self):
        """2 BUY + 1 NEUTRAL with moderate agreement → CAUTIOUS band."""
        sigs = [
            AgentSignal(agent_name="technical", direction=B, strength=Strength.MODERATE,
                        confidence=0.7, reasoning="r"),
            AgentSignal(agent_name="sentiment", direction=B, strength=Strength.WEAK,
                        confidence=0.55, reasoning="r"),
            AgentSignal(agent_name="fundamental", direction=N, strength=Strength.WEAK,
                        confidence=0.4, reasoning="r"),
        ]
        result = compute_consistency(sigs)
        assert result.risk_mode == RiskMode.CAUTIOUS

    def test_risk_mode_boundary_normal(self):
        """raw_consistency exactly 0.7 → NORMAL."""
        # All agree BUY with perfect strength/confidence alignment → direction_score=1.0
        # strength_score=1.0, confidence_score=1.0 → raw=1.0 → NORMAL
        sigs = [
            AgentSignal(agent_name="a", direction=B, strength=Strength.STRONG,
                        confidence=0.9, reasoning="r"),
            AgentSignal(agent_name="b", direction=B, strength=Strength.STRONG,
                        confidence=0.9, reasoning="r"),
            AgentSignal(agent_name="c", direction=B, strength=Strength.STRONG,
                        confidence=0.9, reasoning="r"),
        ]
        result = compute_consistency(sigs)
        assert result.risk_mode == RiskMode.NORMAL

    def test_zero_signals_raises(self):
        with pytest.raises(ValueError, match="At least one signal"):
            compute_consistency([])

    def test_too_many_signals_raises(self):
        sigs = [make_signal(B, agent_name=f"a{i}") for i in range(4)]
        with pytest.raises(ValueError, match="Maximum 3"):
            compute_consistency(sigs)

    def test_final_consistency_never_exceeds_one(self):
        sigs = [make_signal(B, Strength.STRONG, 1.0, agent_name=f"a{i}") for i in range(3)]
        result = compute_consistency(sigs)
        assert result.final_consistency <= 1.0

    def test_final_consistency_non_negative(self):
        sigs = [make_signal(B, agent_name="a"), make_signal(S, agent_name="b")]
        result = compute_consistency(sigs)
        assert result.final_consistency >= 0.0
