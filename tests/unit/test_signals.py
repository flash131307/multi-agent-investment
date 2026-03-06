"""Unit tests for Pydantic signal models and enums."""

import pytest
from pydantic import ValidationError

from backend.models.signals import AgentSignal, Direction, Strength


class TestDirection:
    def test_values(self):
        assert Direction.BUY.value == "BUY"
        assert Direction.NEUTRAL.value == "NEUTRAL"
        assert Direction.SELL.value == "SELL"

    def test_all_members(self):
        assert set(Direction) == {Direction.BUY, Direction.NEUTRAL, Direction.SELL}


class TestStrength:
    def test_numeric_strong(self):
        assert Strength.STRONG.numeric == 1.0

    def test_numeric_moderate(self):
        assert Strength.MODERATE.numeric == 0.7

    def test_numeric_weak(self):
        assert Strength.WEAK.numeric == 0.4

    def test_all_members(self):
        assert set(Strength) == {Strength.STRONG, Strength.MODERATE, Strength.WEAK}


class TestAgentSignal:
    def test_valid_buy_signal(self):
        sig = AgentSignal(
            agent_name="technical",
            direction=Direction.BUY,
            strength=Strength.STRONG,
            confidence=0.9,
            reasoning="Clear uptrend.",
        )
        assert sig.direction == Direction.BUY
        assert sig.strength == Strength.STRONG
        assert sig.confidence == 0.9

    def test_valid_sell_signal(self):
        sig = AgentSignal(
            agent_name="fundamental",
            direction=Direction.SELL,
            strength=Strength.MODERATE,
            confidence=0.65,
            reasoning="Overvalued.",
        )
        assert sig.direction == Direction.SELL

    def test_valid_neutral_weak(self):
        sig = AgentSignal(
            agent_name="sentiment",
            direction=Direction.NEUTRAL,
            strength=Strength.WEAK,
            confidence=0.5,
            reasoning="Mixed signals.",
        )
        assert sig.direction == Direction.NEUTRAL

    def test_valid_neutral_moderate(self):
        """NEUTRAL with MODERATE strength is allowed."""
        sig = AgentSignal(
            agent_name="technical",
            direction=Direction.NEUTRAL,
            strength=Strength.MODERATE,
            confidence=0.4,
            reasoning="Ranging market.",
        )
        assert sig.strength == Strength.MODERATE

    def test_invalid_neutral_strong_raises(self):
        """NEUTRAL/STRONG is not allowed."""
        with pytest.raises(ValidationError):
            AgentSignal(
                agent_name="technical",
                direction=Direction.NEUTRAL,
                strength=Strength.STRONG,
                confidence=0.8,
                reasoning="Should fail.",
            )

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            AgentSignal(
                agent_name="technical",
                direction=Direction.BUY,
                strength=Strength.WEAK,
                confidence=-0.1,
                reasoning="Bad confidence.",
            )

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            AgentSignal(
                agent_name="technical",
                direction=Direction.BUY,
                strength=Strength.WEAK,
                confidence=1.1,
                reasoning="Bad confidence.",
            )

    def test_empty_reasoning_raises(self):
        with pytest.raises(ValidationError):
            AgentSignal(
                agent_name="technical",
                direction=Direction.BUY,
                strength=Strength.WEAK,
                confidence=0.5,
                reasoning="",
            )

    def test_frozen_immutability(self, bullish_signal):
        """AgentSignal must be immutable."""
        with pytest.raises(Exception):
            bullish_signal.confidence = 0.0  # type: ignore[misc]

    def test_confidence_boundary_zero(self):
        sig = AgentSignal(
            agent_name="test",
            direction=Direction.NEUTRAL,
            strength=Strength.WEAK,
            confidence=0.0,
            reasoning="Minimum confidence.",
        )
        assert sig.confidence == 0.0

    def test_confidence_boundary_one(self):
        sig = AgentSignal(
            agent_name="test",
            direction=Direction.BUY,
            strength=Strength.STRONG,
            confidence=1.0,
            reasoning="Maximum confidence.",
        )
        assert sig.confidence == 1.0

    def test_enum_string_coercion(self):
        """Pydantic should coerce string values to enums."""
        sig = AgentSignal(
            agent_name="test",
            direction="BUY",  # type: ignore[arg-type]
            strength="STRONG",  # type: ignore[arg-type]
            confidence=0.8,
            reasoning="String coercion test.",
        )
        assert sig.direction == Direction.BUY
        assert sig.strength == Strength.STRONG

    def test_fixture_bullish_signal(self, bullish_signal):
        assert bullish_signal.agent_name == "technical"
        assert bullish_signal.direction == Direction.BUY
        assert bullish_signal.strength == Strength.STRONG
        assert bullish_signal.confidence == 0.85

    def test_fixture_bearish_signal(self, bearish_signal):
        assert bearish_signal.agent_name == "fundamental"
        assert bearish_signal.direction == Direction.SELL
        assert bearish_signal.strength == Strength.WEAK
