"""
Integration tests for TechnicalAgent with mocked yfinance and OpenAI.
"""
import json
from typing import Optional
from unittest.mock import MagicMock, patch, AsyncMock

import numpy as np
import pandas as pd
import pytest

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.technical import RegimeType


# ---------------------------------------------------------------------------
# Synthetic data helper (reuse from unit tests)
# ---------------------------------------------------------------------------

def make_ohlcv(n: int = 100, trend: str = "flat", seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")

    if trend == "up":
        close_changes = rng.normal(loc=0.5, scale=0.3, size=n)
    elif trend == "down":
        close_changes = rng.normal(loc=-0.5, scale=0.3, size=n)
    else:
        close_changes = rng.normal(loc=0.0, scale=0.2, size=n)

    close = np.zeros(n)
    close[0] = 100.0
    for i in range(1, n):
        close[i] = close[i - 1] * (1 + close_changes[i] / 100)

    daily_range = close * rng.uniform(0.005, 0.02, size=n)
    high = close + daily_range / 2
    low = close - daily_range / 2
    open_ = close - rng.uniform(-1, 1, size=n) * daily_range / 4
    volume = rng.integers(1_000_000, 5_000_000, size=n).astype(float)

    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


# ---------------------------------------------------------------------------
# OpenAI response mocking helpers
# ---------------------------------------------------------------------------

def _make_tool_call(call_id: str, name: str, args: dict) -> MagicMock:
    """Create a mock tool call object matching openai SDK structure."""
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(args)
    return tc


def _make_openai_response(tool_calls: list) -> MagicMock:
    """Create a mock OpenAI chat completion response."""
    msg = MagicMock()
    msg.tool_calls = tool_calls
    msg.content = None
    msg.model_dump = MagicMock(return_value={
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in tool_calls
        ],
    })

    choice = MagicMock()
    choice.message = msg

    response = MagicMock()
    response.choices = [choice]
    return response


def _make_synthesis_args(
    direction: str = "BUY",
    strength: str = "MODERATE",
    confidence: float = 0.75,
    reasoning: str = "RSI oversold + bullish MACD crossover.",
) -> dict:
    return {
        "direction": direction,
        "strength": strength,
        "confidence": confidence,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_df() -> pd.DataFrame:
    return make_ohlcv(n=150, trend="up", seed=1)


@pytest.fixture
def synthetic_df_flat() -> pd.DataFrame:
    return make_ohlcv(n=150, trend="flat", seed=2)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTechnicalAgentMarketRegimeFirstStep:
    """market_regime must be called as the mandatory first step."""

    def test_market_regime_computed_before_llm_loop(self, synthetic_df):
        """
        Verify that market_regime is always run before the LLM loop starts.
        The agent injects the regime result into the first message.
        """
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()

        # LLM immediately calls synthesize_signal after market_regime
        synth_args = _make_synthesis_args()
        synth_response = _make_openai_response([
            _make_tool_call("call_synth", "synthesize_signal", synth_args)
        ])
        mock_client.chat.completions.create.return_value = synth_response

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            with patch(
                "backend.agents.technical.agent.compute_market_regime",
            ) as mock_regime:
                fake_regime = MagicMock()
                fake_regime.regime_type = RegimeType.TRENDING
                fake_regime.trend_strength = 0.65
                fake_regime.volatility = 0.012
                fake_regime.interpretation = "Trending market."
                fake_regime.model_dump.return_value = {
                    "regime_type": "TRENDING",
                    "trend_strength": 0.65,
                    "volatility": 0.012,
                    "interpretation": "Trending market.",
                }
                mock_regime.return_value = fake_regime
                import asyncio
                result = asyncio.run(agent.run("AAPL"))

        # market_regime tool should have been called
        mock_regime.assert_called_once()


class TestTechnicalAgentMaxSteps:
    """Agent should stop after max 5 steps total."""

    def test_agent_stops_at_max_steps(self, synthetic_df):
        """
        If the LLM keeps requesting tools (never synthesizes), agent should stop
        at max 5 steps and return the fallback signal.
        """
        from backend.agents.technical.agent import TechnicalAgent, _MAX_STEPS

        mock_client = MagicMock()

        # LLM always requests rsi_analysis (never synthesizes)
        endless_response = _make_openai_response([
            _make_tool_call("call_rsi", "rsi_analysis", {})
        ])
        mock_client.chat.completions.create.return_value = endless_response

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            import asyncio
            result = asyncio.run(agent.run("TSLA"))

        # Should return fallback (NEUTRAL/WEAK/0.3) after max steps exhausted
        assert result is not None
        assert result.direction == Direction.NEUTRAL
        assert result.strength == Strength.WEAK
        assert result.confidence == pytest.approx(0.3)

        # LLM should have been called at most _MAX_STEPS - 1 times
        # (step 1 is forced market_regime; steps 2-5 are LLM-driven)
        assert mock_client.chat.completions.create.call_count <= _MAX_STEPS - 1


class TestTechnicalAgentOutputIsValidAgentSignal:
    """Agent must always return a valid AgentSignal (or None on hard failure)."""

    def test_successful_run_returns_agent_signal(self, synthetic_df):
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        synth_args = _make_synthesis_args(direction="BUY", strength="STRONG", confidence=0.9)
        mock_client.chat.completions.create.return_value = _make_openai_response([
            _make_tool_call("call_rsi", "rsi_analysis", {}),
            _make_tool_call("call_synth", "synthesize_signal", synth_args),
        ])

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            import asyncio
            result = asyncio.run(agent.run("AAPL"))

        assert result is not None
        assert isinstance(result, AgentSignal)
        assert result.agent_name == "technical"
        assert result.direction in (Direction.BUY, Direction.NEUTRAL, Direction.SELL)
        assert result.strength in (Strength.STRONG, Strength.MODERATE, Strength.WEAK)
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.reasoning) > 0

    def test_neutral_direction_cannot_have_strong_strength(self, synthetic_df):
        """NEUTRAL + STRONG is invalid; agent should fix it to MODERATE."""
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        invalid_synth = _make_synthesis_args(
            direction="NEUTRAL", strength="STRONG", confidence=0.6,
            reasoning="Conflicting signals."
        )
        mock_client.chat.completions.create.return_value = _make_openai_response([
            _make_tool_call("call_synth", "synthesize_signal", invalid_synth),
        ])

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            import asyncio
            result = asyncio.run(agent.run("GOOGL"))

        assert result is not None
        if result.direction == Direction.NEUTRAL:
            assert result.strength != Strength.STRONG

    def test_confidence_is_clamped_to_valid_range(self, synthetic_df):
        """Confidence values out of [0, 1] should be clamped."""
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        bad_synth = _make_synthesis_args(
            direction="BUY", strength="MODERATE", confidence=1.5,  # out of range
            reasoning="Over-confident signal."
        )
        mock_client.chat.completions.create.return_value = _make_openai_response([
            _make_tool_call("call_synth", "synthesize_signal", bad_synth),
        ])

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            import asyncio
            result = asyncio.run(agent.run("MSFT"))

        assert result is not None
        assert 0.0 <= result.confidence <= 1.0


class TestTechnicalAgentToolFailureFallback:
    """On tool failure, agent should return NEUTRAL fallback."""

    def test_data_fetch_failure_returns_fallback(self):
        """If get_technical_data raises ValueError, agent returns NEUTRAL fallback."""
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            side_effect=ValueError("Ticker not found"),
        ):
            import asyncio
            result = asyncio.run(agent.run("INVALID_TICKER"))

        assert result is not None
        assert result.direction == Direction.NEUTRAL
        assert result.strength == Strength.WEAK
        assert result.confidence == pytest.approx(0.3)

    def test_openai_api_failure_returns_fallback(self, synthetic_df):
        """If OpenAI API call fails for all steps, agent returns fallback."""
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API down")

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            import asyncio
            result = asyncio.run(agent.run("AAPL"))

        assert result is not None
        assert result.direction == Direction.NEUTRAL

    def test_market_regime_failure_returns_fallback(self, synthetic_df):
        """If market_regime tool itself fails, agent returns NEUTRAL fallback."""
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            with patch(
                "backend.agents.technical.agent.compute_market_regime",
                side_effect=ValueError("Insufficient data"),
            ):
                import asyncio
                result = asyncio.run(agent.run("AAPL"))

        assert result is not None
        assert result.direction == Direction.NEUTRAL
        assert result.strength == Strength.WEAK

    def test_individual_tool_error_continues_loop(self, synthetic_df):
        """
        If an individual tool (e.g., rsi_analysis) errors, the agent should
        continue and still produce a signal (or fallback).
        """
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()

        # First call: LLM requests rsi_analysis + synthesize_signal
        synth_args = _make_synthesis_args(
            direction="NEUTRAL", strength="WEAK", confidence=0.3,
            reasoning="RSI failed but other signals are neutral."
        )
        mock_client.chat.completions.create.return_value = _make_openai_response([
            _make_tool_call("call_rsi", "rsi_analysis", {}),
            _make_tool_call("call_synth", "synthesize_signal", synth_args),
        ])

        agent = TechnicalAgent(openai_client=mock_client)

        with patch(
            "backend.agents.technical.agent.get_technical_data",
            return_value=synthetic_df,
        ):
            with patch(
                "backend.agents.technical.agent.compute_rsi_signal",
                side_effect=ValueError("RSI NaN"),
            ):
                import asyncio
                result = asyncio.run(agent.run("AAPL"))

        # Agent should survive the RSI failure and return a signal
        assert result is not None
        assert isinstance(result, AgentSignal)


class TestTechnicalAgentBaseClassTimeout:
    """BaseAgent.run() should handle timeouts gracefully."""

    def test_timeout_returns_none(self, synthetic_df):
        """If _execute takes too long, BaseAgent.run() returns None."""
        import asyncio
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        agent = TechnicalAgent(openai_client=mock_client, timeout=0.001)

        async def slow_execute(ticker):
            await asyncio.sleep(10)  # simulate very slow execution
            return None

        agent._execute = slow_execute

        result = asyncio.run(agent.run("AAPL"))
        assert result is None

    def test_exception_in_execute_returns_none(self, synthetic_df):
        """If _execute raises an unexpected exception, BaseAgent.run() returns None."""
        import asyncio
        from backend.agents.technical.agent import TechnicalAgent

        mock_client = MagicMock()
        agent = TechnicalAgent(openai_client=mock_client)

        async def failing_execute(ticker):
            raise RuntimeError("Unexpected crash")

        agent._execute = failing_execute

        result = asyncio.run(agent.run("AAPL"))
        assert result is None
