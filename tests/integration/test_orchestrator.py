"""Integration tests for orchestrator/runner.py."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.decision import DecisionResult, RiskMode


def make_signal(agent_name: str, direction: Direction = Direction.BUY) -> AgentSignal:
    return AgentSignal(
        agent_name=agent_name,
        direction=direction,
        strength=Strength.MODERATE,
        confidence=0.75,
        reasoning=f"{agent_name} signal.",
    )


@pytest.fixture
def bullish_signals() -> list[AgentSignal]:
    return [
        make_signal("technical", Direction.BUY),
        make_signal("sentiment", Direction.BUY),
        make_signal("fundamental", Direction.BUY),
    ]


# ---------------------------------------------------------------------------
# run_agents tests
# ---------------------------------------------------------------------------

class TestRunAgents:
    @pytest.mark.asyncio
    async def test_all_three_agents_succeed(self, bullish_signals):
        """All three agents succeed → 3 signals, 0 errors."""
        tech_sig, sent_sig, fund_sig = bullish_signals

        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = AsyncMock(return_value=tech_sig)
            MockSent.return_value.run = AsyncMock(return_value=sent_sig)
            MockFund.return_value.run = AsyncMock(return_value=fund_sig)

            from backend.orchestrator.runner import run_agents
            signals, errors = await run_agents("AAPL")

        assert len(signals) == 3
        assert errors == {}

    @pytest.mark.asyncio
    async def test_one_agent_returns_none(self, bullish_signals):
        """Agent returning None → counted as error, not as signal."""
        tech_sig, sent_sig, _ = bullish_signals

        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = AsyncMock(return_value=tech_sig)
            MockSent.return_value.run = AsyncMock(return_value=sent_sig)
            MockFund.return_value.run = AsyncMock(return_value=None)

            from backend.orchestrator.runner import run_agents
            signals, errors = await run_agents("AAPL")

        assert len(signals) == 2
        assert "fundamental" in errors

    @pytest.mark.asyncio
    async def test_one_agent_raises_exception(self, bullish_signals):
        """Agent raising exception → counted as error."""
        tech_sig, sent_sig, _ = bullish_signals

        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = AsyncMock(return_value=tech_sig)
            MockSent.return_value.run = AsyncMock(return_value=sent_sig)
            MockFund.return_value.run = AsyncMock(side_effect=RuntimeError("DB error"))

            from backend.orchestrator.runner import run_agents
            signals, errors = await run_agents("AAPL")

        assert len(signals) == 2
        assert "fundamental" in errors
        assert "DB error" in errors["fundamental"]

    @pytest.mark.asyncio
    async def test_all_agents_fail_returns_empty_signals(self):
        """All agents fail → empty signals list."""
        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = AsyncMock(return_value=None)
            MockSent.return_value.run = AsyncMock(return_value=None)
            MockFund.return_value.run = AsyncMock(return_value=None)

            from backend.orchestrator.runner import run_agents
            signals, errors = await run_agents("AAPL")

        assert signals == []
        assert len(errors) == 3

    @pytest.mark.asyncio
    async def test_agents_run_concurrently(self, bullish_signals):
        """Agents should be launched concurrently, not sequentially."""
        import time
        call_times: list[float] = []

        async def slow_agent(*args, **kwargs):
            call_times.append(time.monotonic())
            await asyncio.sleep(0.05)
            return bullish_signals[0]

        tech_sig, sent_sig, fund_sig = bullish_signals

        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = slow_agent
            MockSent.return_value.run = slow_agent
            MockFund.return_value.run = slow_agent

            start = time.monotonic()
            from backend.orchestrator.runner import run_agents
            await run_agents("AAPL")
            elapsed = time.monotonic() - start

        # If truly concurrent, total time ≈ 0.05s, not 0.15s
        assert elapsed < 0.12, f"Agents ran sequentially (elapsed={elapsed:.3f}s)"

    @pytest.mark.asyncio
    async def test_timeout_passed_to_agents(self, bullish_signals):
        """Custom timeouts are passed to agent constructors."""
        tech_sig = bullish_signals[0]

        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = AsyncMock(return_value=tech_sig)
            MockSent.return_value.run = AsyncMock(return_value=None)
            MockFund.return_value.run = AsyncMock(return_value=None)

            from backend.orchestrator.runner import run_agents
            await run_agents("AAPL", technical_timeout=45.0, sentiment_timeout=25.0, fundamental_timeout=90.0)

        MockTech.assert_called_once_with(timeout=45.0)
        MockSent.assert_called_once_with(timeout=25.0)
        MockFund.assert_called_once_with(timeout=90.0)


# ---------------------------------------------------------------------------
# analyze tests (full pipeline)
# ---------------------------------------------------------------------------

class TestAnalyze:
    @pytest.mark.asyncio
    async def test_returns_decision_result(self, bullish_signals):
        """Full pipeline returns a DecisionResult with reasoning."""
        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
            patch("backend.orchestrator.runner.generate_reasoning", return_value="Bullish consensus."),
        ):
            for mock, sig in zip([MockTech, MockSent, MockFund], bullish_signals):
                mock.return_value.run = AsyncMock(return_value=sig)

            from backend.orchestrator.runner import analyze
            result, errors = await analyze("AAPL")

        assert isinstance(result, DecisionResult)
        assert result.direction == Direction.BUY
        assert result.reasoning == "Bullish consensus."
        assert errors == {}

    @pytest.mark.asyncio
    async def test_raises_runtime_error_when_no_signals(self):
        """Zero valid signals → RuntimeError (caller returns 503)."""
        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
        ):
            MockTech.return_value.run = AsyncMock(return_value=None)
            MockSent.return_value.run = AsyncMock(return_value=None)
            MockFund.return_value.run = AsyncMock(return_value=None)

            from backend.orchestrator.runner import analyze
            with pytest.raises(RuntimeError, match="All agents failed"):
                await analyze("AAPL")

    @pytest.mark.asyncio
    async def test_two_agent_degradation_adds_warning(self, bullish_signals):
        """2 agents → DecisionResult has degradation warning."""
        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
            patch("backend.orchestrator.runner.generate_reasoning", return_value="ok"),
        ):
            MockTech.return_value.run = AsyncMock(return_value=bullish_signals[0])
            MockSent.return_value.run = AsyncMock(return_value=bullish_signals[1])
            MockFund.return_value.run = AsyncMock(return_value=None)

            from backend.orchestrator.runner import analyze
            result, errors = await analyze("AAPL")

        assert len(result.warnings) >= 1
        assert "fundamental" in errors

    @pytest.mark.asyncio
    async def test_reasoning_failure_falls_back_gracefully(self, bullish_signals):
        """LLM reasoning failure does not crash the pipeline."""
        with (
            patch("backend.orchestrator.runner.TechnicalAgent") as MockTech,
            patch("backend.orchestrator.runner.SentimentAgent") as MockSent,
            patch("backend.orchestrator.runner.FundamentalAgent") as MockFund,
            patch("backend.orchestrator.runner.generate_reasoning", side_effect=Exception("LLM down")),
        ):
            for mock, sig in zip([MockTech, MockSent, MockFund], bullish_signals):
                mock.return_value.run = AsyncMock(return_value=sig)

            from backend.orchestrator.runner import analyze
            result, errors = await analyze("AAPL")

        # Should still return a result (with empty reasoning from hub)
        assert isinstance(result, DecisionResult)
