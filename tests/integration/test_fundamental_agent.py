"""
Integration tests for the FundamentalAgent pipeline.
All external dependencies (yfinance, Qdrant, OpenAI) are mocked.
"""
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock

from backend.models.fundamental import (
    AnalysisTask,
    CompanyProfile,
    SubConclusion,
)
from backend.models.signals import Direction, Strength, AgentSignal
from backend.agents.fundamental.synthesizer import synthesize
from backend.agents.fundamental.planner import generate_tasks, _build_and_normalize
from backend.agents.fundamental.executor import execute_tasks, _fallback_conclusion


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile() -> CompanyProfile:
    return CompanyProfile(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        description="Apple designs and manufactures consumer electronics.",
        market_cap=3_000_000_000_000,
        pe_ratio=28.5,
        revenue_growth=0.08,
    )


@pytest.fixture
def sample_tasks() -> list[AnalysisTask]:
    return [
        AnalysisTask(
            task_id="task_1",
            description="Analyze revenue growth",
            rag_query="revenue growth trends",
            weight=0.4,
        ),
        AnalysisTask(
            task_id="task_2",
            description="Assess profitability",
            rag_query="profit margin operating income",
            weight=0.35,
        ),
        AnalysisTask(
            task_id="task_3",
            description="Evaluate balance sheet",
            rag_query="debt equity ratio",
            weight=0.25,
        ),
    ]


@pytest.fixture
def bullish_conclusions() -> list[SubConclusion]:
    return [
        SubConclusion(
            task_id="task_1",
            conclusion="Strong revenue growth trajectory",
            supporting_evidence=["Revenue grew 15% YoY"],
            sentiment_score=0.7,
            confidence=0.85,
        ),
        SubConclusion(
            task_id="task_2",
            conclusion="Excellent profit margins",
            supporting_evidence=["Operating margin 25%"],
            sentiment_score=0.6,
            confidence=0.8,
        ),
        SubConclusion(
            task_id="task_3",
            conclusion="Healthy balance sheet",
            supporting_evidence=["D/E ratio 0.3"],
            sentiment_score=0.5,
            confidence=0.75,
        ),
    ]


@pytest.fixture
def bearish_conclusions() -> list[SubConclusion]:
    return [
        SubConclusion(
            task_id="task_1",
            conclusion="Declining revenue",
            supporting_evidence=["Revenue fell 12% YoY"],
            sentiment_score=-0.7,
            confidence=0.8,
        ),
        SubConclusion(
            task_id="task_2",
            conclusion="Shrinking margins",
            supporting_evidence=["Operating margin down to 5%"],
            sentiment_score=-0.6,
            confidence=0.75,
        ),
        SubConclusion(
            task_id="task_3",
            conclusion="High debt burden",
            supporting_evidence=["D/E ratio 2.5"],
            sentiment_score=-0.5,
            confidence=0.7,
        ),
    ]


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.openai_api_key = "test-key-123"
    settings.openai_model = "gpt-4o"
    return settings


@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        {"text": "Apple has strong competitive advantages.", "metadata": {}, "score": 0.9},
        {"text": "Revenue growth driven by services segment.", "metadata": {}, "score": 0.8},
    ]
    return retriever


@pytest.fixture
def mock_income_stmt():
    cols = pd.to_datetime(["2023-12-31", "2022-12-31"])
    data = {"Net Income": [10_000, 8_000], "Total Revenue": [100_000, 90_000]}
    return pd.DataFrame(data, index=cols).T


@pytest.fixture
def mock_balance_sheet():
    cols = pd.to_datetime(["2023-12-31", "2022-12-31"])
    data = {
        "Stockholders Equity": [50_000, 45_000],
        "Current Assets": [30_000, 28_000],
        "Current Liabilities": [15_000, 13_000],
        "Total Debt": [20_000, 18_000],
    }
    return pd.DataFrame(data, index=cols).T


# ---------------------------------------------------------------------------
# Synthesizer tests
# ---------------------------------------------------------------------------

class TestSynthesizer:
    def test_bullish_signal_on_positive_scores(self, sample_tasks, bullish_conclusions):
        signal = synthesize(
            profile=MagicMock(),
            conclusions=bullish_conclusions,
            tasks=sample_tasks,
        )
        assert signal.direction == Direction.BUY
        assert signal.agent_name == "fundamental"
        assert 0.0 <= signal.confidence <= 1.0

    def test_bearish_signal_on_negative_scores(self, sample_tasks, bearish_conclusions):
        signal = synthesize(
            profile=MagicMock(),
            conclusions=bearish_conclusions,
            tasks=sample_tasks,
        )
        assert signal.direction == Direction.SELL
        assert signal.agent_name == "fundamental"

    def test_neutral_signal_on_mixed_scores(self, sample_tasks):
        mixed_conclusions = [
            SubConclusion(
                task_id="task_1",
                conclusion="Mixed outlook",
                supporting_evidence=[],
                sentiment_score=0.1,
                confidence=0.6,
            ),
            SubConclusion(
                task_id="task_2",
                conclusion="Neutral assessment",
                supporting_evidence=[],
                sentiment_score=-0.05,
                confidence=0.6,
            ),
        ]
        signal = synthesize(
            profile=MagicMock(),
            conclusions=mixed_conclusions,
            tasks=sample_tasks,
        )
        assert signal.direction == Direction.NEUTRAL

    def test_sentiment_above_threshold_maps_to_buy(self, sample_tasks):
        """score > 0.2 → BUY"""
        conclusions = [
            SubConclusion(
                task_id="task_1",
                conclusion="Positive",
                supporting_evidence=[],
                sentiment_score=0.5,
                confidence=0.8,
            )
        ]
        signal = synthesize(MagicMock(), conclusions, sample_tasks)
        assert signal.direction == Direction.BUY

    def test_sentiment_below_threshold_maps_to_sell(self, sample_tasks):
        """score < -0.2 → SELL"""
        conclusions = [
            SubConclusion(
                task_id="task_1",
                conclusion="Negative",
                supporting_evidence=[],
                sentiment_score=-0.5,
                confidence=0.8,
            )
        ]
        signal = synthesize(MagicMock(), conclusions, sample_tasks)
        assert signal.direction == Direction.SELL

    def test_strong_strength_for_high_score(self, sample_tasks):
        """abs(score) > 0.5 → STRONG"""
        conclusions = [
            SubConclusion(
                task_id="task_1",
                conclusion="Very bullish",
                supporting_evidence=[],
                sentiment_score=0.9,
                confidence=0.9,
            )
        ]
        signal = synthesize(MagicMock(), conclusions, sample_tasks)
        assert signal.strength == Strength.STRONG

    def test_empty_conclusions_returns_neutral(self, sample_tasks):
        signal = synthesize(MagicMock(), [], sample_tasks)
        assert signal.direction == Direction.NEUTRAL
        assert signal.confidence == 0.0

    def test_signal_is_immutable_agent_signal(self, sample_tasks, bullish_conclusions):
        signal = synthesize(MagicMock(), bullish_conclusions, sample_tasks)
        assert isinstance(signal, AgentSignal)
        assert signal.agent_name == "fundamental"

    def test_reasoning_not_empty(self, sample_tasks, bullish_conclusions):
        signal = synthesize(MagicMock(), bullish_conclusions, sample_tasks)
        assert len(signal.reasoning) > 0


# ---------------------------------------------------------------------------
# Planner tests
# ---------------------------------------------------------------------------

class TestPlanner:
    def test_default_tasks_returned_on_no_api_key(self, sample_profile):
        settings = MagicMock()
        settings.openai_api_key = None
        tasks = generate_tasks(sample_profile, settings)
        assert len(tasks) >= 3
        assert all(isinstance(t, AnalysisTask) for t in tasks)

    def test_weights_sum_to_approximately_one(self, sample_profile):
        settings = MagicMock()
        settings.openai_api_key = None
        tasks = generate_tasks(sample_profile, settings)
        total = sum(t.weight for t in tasks)
        assert total == pytest.approx(1.0, abs=0.01)

    def test_llm_failure_returns_default_tasks(self, sample_profile):
        """When LLM raises an exception, fall back to default tasks."""
        settings = MagicMock()
        settings.openai_api_key = "key"
        settings.openai_model = "gpt-4o"

        with patch("backend.agents.fundamental.planner.OpenAI") as mock_openai:
            mock_openai.side_effect = Exception("API down")
            tasks = generate_tasks(sample_profile, settings)

        assert len(tasks) >= 3
        assert all(isinstance(t, AnalysisTask) for t in tasks)

    def test_llm_json_parse_failure_returns_default_tasks(self, sample_profile):
        """When LLM returns invalid JSON, fall back to defaults."""
        settings = MagicMock()
        settings.openai_api_key = "key"
        settings.openai_model = "gpt-4o"

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "this is not json"

        with patch("backend.agents.fundamental.planner.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            tasks = generate_tasks(sample_profile, settings)

        assert len(tasks) >= 3

    def test_successful_llm_tasks_normalized(self, sample_profile):
        """When LLM returns valid tasks, weights are normalized."""
        settings = MagicMock()
        settings.openai_api_key = "key"
        settings.openai_model = "gpt-4o"

        llm_tasks = [
            {"task_id": "t1", "description": "Task 1", "rag_query": "q1", "weight": 2.0},
            {"task_id": "t2", "description": "Task 2", "rag_query": "q2", "weight": 3.0},
        ]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(llm_tasks)

        with patch("backend.agents.fundamental.planner.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            tasks = generate_tasks(sample_profile, settings)

        total = sum(t.weight for t in tasks)
        assert total == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# Executor tests
# ---------------------------------------------------------------------------

class TestExecutor:
    def test_handles_llm_failure_gracefully(self, sample_tasks, mock_retriever, mock_settings):
        """If LLM call fails, returns fallback SubConclusion with confidence=0.3."""
        with patch("backend.agents.fundamental.executor.OpenAI") as mock_openai:
            mock_openai.side_effect = Exception("API error")
            conclusions = execute_tasks(
                tasks=sample_tasks,
                ticker="AAPL",
                retriever=mock_retriever,
                financial_data={"metrics": {}},
                settings_obj=mock_settings,
            )

        assert len(conclusions) == len(sample_tasks)
        for c in conclusions:
            assert isinstance(c, SubConclusion)
            assert c.confidence == 0.3
            assert c.sentiment_score == 0.0

    def test_returns_one_conclusion_per_task(self, sample_tasks, mock_retriever, mock_settings):
        llm_output = {
            "task_id": "task_1",
            "conclusion": "Strong performance",
            "supporting_evidence": ["Revenue up"],
            "sentiment_score": 0.6,
            "confidence": 0.8,
        }

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(llm_output)

        with patch("backend.agents.fundamental.executor.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            conclusions = execute_tasks(
                tasks=sample_tasks,
                ticker="AAPL",
                retriever=mock_retriever,
                financial_data={"metrics": {}},
                settings_obj=mock_settings,
            )

        assert len(conclusions) == len(sample_tasks)

    def test_none_retriever_does_not_crash(self, sample_tasks, mock_settings):
        """execute_tasks with retriever=None should work (no RAG passages)."""
        with patch("backend.agents.fundamental.executor.OpenAI") as mock_openai:
            mock_openai.side_effect = Exception("No API")
            conclusions = execute_tasks(
                tasks=sample_tasks,
                ticker="AAPL",
                retriever=None,
                financial_data={"metrics": {}},
                settings_obj=mock_settings,
            )

        assert len(conclusions) == len(sample_tasks)
        for c in conclusions:
            assert isinstance(c, SubConclusion)

    def test_fallback_conclusion_values(self):
        c = _fallback_conclusion("task_x", "some error")
        assert c.task_id == "task_x"
        assert c.confidence == 0.3
        assert c.sentiment_score == 0.0
        assert isinstance(c.supporting_evidence, list)


# ---------------------------------------------------------------------------
# Full pipeline integration test
# ---------------------------------------------------------------------------

class TestFundamentalAgentPipeline:
    """End-to-end pipeline test with all externals mocked."""

    @pytest.fixture
    def mock_yf_ticker(self, mock_income_stmt, mock_balance_sheet):
        mock = MagicMock()
        mock.info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "longBusinessSummary": "Apple makes great products.",
            "marketCap": 3_000_000_000_000,
            "trailingPE": 28.5,
            "revenueGrowth": 0.08,
        }
        mock.income_stmt = mock_income_stmt
        mock.balance_sheet = mock_balance_sheet
        mock.cashflow = pd.DataFrame()
        return mock

    @pytest.fixture
    def llm_plan_response(self):
        tasks = [
            {"task_id": "t1", "description": "Revenue analysis", "rag_query": "revenue", "weight": 0.5},
            {"task_id": "t2", "description": "Profitability", "rag_query": "margins", "weight": 0.5},
        ]
        resp = MagicMock()
        resp.choices[0].message.content = json.dumps(tasks)
        return resp

    @pytest.fixture
    def llm_exec_response(self):
        data = {
            "task_id": "t1",
            "conclusion": "Strong growth prospects",
            "supporting_evidence": ["15% revenue growth"],
            "sentiment_score": 0.65,
            "confidence": 0.8,
        }
        resp = MagicMock()
        resp.choices[0].message.content = json.dumps(data)
        return resp

    def test_full_pipeline_returns_agent_signal(
        self,
        mock_yf_ticker,
        llm_plan_response,
        llm_exec_response,
        mock_retriever,
        mock_settings,
    ):
        with (
            patch("backend.agents.fundamental.tools.company_profile.yf.Ticker", return_value=mock_yf_ticker),
            patch("backend.agents.fundamental.tools.financial_data.yf.Ticker", return_value=mock_yf_ticker),
            patch("backend.agents.fundamental.planner.OpenAI") as mock_plan_openai,
            patch("backend.agents.fundamental.executor.OpenAI") as mock_exec_openai,
        ):
            mock_plan_openai.return_value.chat.completions.create.return_value = llm_plan_response
            mock_exec_openai.return_value.chat.completions.create.return_value = llm_exec_response

            import asyncio
            from backend.agents.fundamental.agent import FundamentalAgent

            agent = FundamentalAgent(
                retriever=mock_retriever,
                timeout=30.0,
                settings_override=mock_settings,
            )
            signal = asyncio.get_event_loop().run_until_complete(agent.run("AAPL"))

        assert signal is not None
        assert isinstance(signal, AgentSignal)
        assert signal.agent_name == "fundamental"
        assert signal.direction in (Direction.BUY, Direction.NEUTRAL, Direction.SELL)
        assert 0.0 <= signal.confidence <= 1.0

    def test_pipeline_with_no_retriever(
        self,
        mock_yf_ticker,
        llm_plan_response,
        llm_exec_response,
        mock_settings,
    ):
        """Pipeline should work when retriever=None."""
        with (
            patch("backend.agents.fundamental.tools.company_profile.yf.Ticker", return_value=mock_yf_ticker),
            patch("backend.agents.fundamental.tools.financial_data.yf.Ticker", return_value=mock_yf_ticker),
            patch("backend.agents.fundamental.planner.OpenAI") as mock_plan_openai,
            patch("backend.agents.fundamental.executor.OpenAI") as mock_exec_openai,
        ):
            mock_plan_openai.return_value.chat.completions.create.return_value = llm_plan_response
            mock_exec_openai.return_value.chat.completions.create.return_value = llm_exec_response

            import asyncio
            from backend.agents.fundamental.agent import FundamentalAgent

            agent = FundamentalAgent(
                retriever=None,
                timeout=30.0,
                settings_override=mock_settings,
            )
            signal = asyncio.get_event_loop().run_until_complete(agent.run("AAPL"))

        assert signal is not None
        assert isinstance(signal, AgentSignal)

    def test_pipeline_with_llm_failure_still_returns_signal(
        self,
        mock_yf_ticker,
        mock_settings,
    ):
        """Even when LLM fails entirely, agent returns a valid signal from defaults."""
        mock_settings.openai_api_key = None  # Force default task fallback
        with (
            patch("backend.agents.fundamental.tools.company_profile.yf.Ticker", return_value=mock_yf_ticker),
            patch("backend.agents.fundamental.tools.financial_data.yf.Ticker", return_value=mock_yf_ticker),
        ):
            import asyncio
            from backend.agents.fundamental.agent import FundamentalAgent

            agent = FundamentalAgent(
                retriever=None,
                timeout=30.0,
                settings_override=mock_settings,
            )
            signal = asyncio.get_event_loop().run_until_complete(agent.run("AAPL"))

        # With no LLM, defaults + fallback conclusions → neutral signal still valid
        assert signal is not None
        assert isinstance(signal, AgentSignal)

    def test_buy_direction_from_positive_scores(self, sample_tasks):
        """Synthesizer maps weighted score > 0.2 to BUY."""
        positive_conclusions = [
            SubConclusion(
                task_id="task_1",
                conclusion="Strong",
                supporting_evidence=[],
                sentiment_score=0.8,
                confidence=0.9,
            ),
            SubConclusion(
                task_id="task_2",
                conclusion="Good",
                supporting_evidence=[],
                sentiment_score=0.6,
                confidence=0.8,
            ),
        ]
        signal = synthesize(MagicMock(), positive_conclusions, sample_tasks)
        assert signal.direction == Direction.BUY

    def test_sell_direction_from_negative_scores(self, sample_tasks):
        """Synthesizer maps weighted score < -0.2 to SELL."""
        negative_conclusions = [
            SubConclusion(
                task_id="task_1",
                conclusion="Weak",
                supporting_evidence=[],
                sentiment_score=-0.8,
                confidence=0.9,
            ),
            SubConclusion(
                task_id="task_2",
                conclusion="Bad",
                supporting_evidence=[],
                sentiment_score=-0.6,
                confidence=0.8,
            ),
        ]
        signal = synthesize(MagicMock(), negative_conclusions, sample_tasks)
        assert signal.direction == Direction.SELL
