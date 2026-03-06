"""E2E tests for POST /api/research/analyze via FastAPI TestClient."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.models.signals import AgentSignal, Direction, Strength
from backend.models.decision import (
    DecisionResult, ConsistencyScore, RiskMode, WeightAllocation
)


def make_signal(agent_name: str, direction: Direction = Direction.BUY) -> AgentSignal:
    return AgentSignal(
        agent_name=agent_name,
        direction=direction,
        strength=Strength.MODERATE,
        confidence=0.75,
        reasoning=f"{agent_name} analysis complete.",
    )


def make_decision_result(signals: list[AgentSignal]) -> DecisionResult:
    """Build a minimal valid DecisionResult for mocking."""
    consistency = ConsistencyScore(
        direction_score=0.7,
        strength_score=0.8,
        confidence_score=0.9,
        raw_consistency=0.6,
        risk_mode=RiskMode.CAUTIOUS,
        final_consistency=0.48,
    )
    weights = [
        WeightAllocation(
            agent_name=s.agent_name,
            base_weight=0.33,
            regime_modifier=1.0,
            confidence=s.confidence,
            final_weight=1.0 / len(signals),
        )
        for s in signals
    ]
    return DecisionResult(
        direction=Direction.BUY,
        confidence=0.65,
        consistency=consistency,
        weights=weights,
        signals=signals,
        aggregated_score=0.42,
        reasoning="Bullish consensus across all agents.",
        warnings=[],
    )


@pytest.fixture
def client():
    """FastAPI TestClient with mocked dependencies."""
    # ticker_resolver is imported at module level in research.py, patch it there
    with patch("backend.api.routes.research.ticker_resolver") as mock_resolver:
        mock_resolver.resolve = AsyncMock(return_value="AAPL")

        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            c._mock_resolver = mock_resolver
            yield c


@pytest.fixture
def three_signals() -> list[AgentSignal]:
    return [
        make_signal("technical", Direction.BUY),
        make_signal("sentiment", Direction.BUY),
        make_signal("fundamental", Direction.BUY),
    ]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    def test_successful_analysis_returns_200(self, client, three_signals):
        result = make_decision_result(three_signals)

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, {}))):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        assert resp.status_code == 200

    def test_response_contains_decision(self, client, three_signals):
        result = make_decision_result(three_signals)

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, {}))):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        body = resp.json()
        assert "decision" in body
        assert body["decision"]["direction"] == "BUY"
        assert 0.0 <= body["decision"]["confidence"] <= 1.0

    def test_response_contains_ticker(self, client, three_signals):
        result = make_decision_result(three_signals)

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, {}))):
            resp = client.post("/api/research/analyze", json={"ticker": "aapl"})

        body = resp.json()
        assert body["ticker"] == "AAPL"

    def test_response_contains_agent_signals(self, client, three_signals):
        result = make_decision_result(three_signals)

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, {}))):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        body = resp.json()
        assert "agents" in body
        assert len(body["agents"]) == 3

    def test_response_contains_reasoning(self, client, three_signals):
        result = make_decision_result(three_signals)

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, {}))):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        body = resp.json()
        assert body["decision"]["reasoning"] != ""

    def test_ticker_uppercased_before_resolution(self, client, three_signals):
        result = make_decision_result(three_signals)

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, {}))):
            resp = client.post("/api/research/analyze", json={"ticker": "aapl"})

        # resolver should be called with uppercased ticker
        client._mock_resolver.resolve.assert_called_with("AAPL")


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestAnalyzeErrors:
    def test_unknown_ticker_returns_400(self, client):
        client._mock_resolver.resolve = AsyncMock(return_value=None)

        resp = client.post("/api/research/analyze", json={"ticker": "XYZXYZ"})
        assert resp.status_code == 400
        assert "XYZXYZ" in resp.json()["detail"]

    def test_all_agents_fail_returns_503(self, client):
        with patch(
            "backend.api.routes.research.analyze",
            new=AsyncMock(side_effect=RuntimeError("All agents failed")),
        ):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        assert resp.status_code == 503

    def test_unexpected_error_returns_500(self, client):
        with patch(
            "backend.api.routes.research.analyze",
            new=AsyncMock(side_effect=Exception("Unexpected internal error")),
        ):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        assert resp.status_code == 500

    def test_missing_ticker_field_returns_422(self, client):
        resp = client.post("/api/research/analyze", json={})
        assert resp.status_code == 422

    def test_empty_ticker_returns_422(self, client):
        resp = client.post("/api/research/analyze", json={"ticker": ""})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Agent error passthrough
# ---------------------------------------------------------------------------

class TestAgentErrorsInResponse:
    def test_partial_failure_returns_200_with_warnings(self, client):
        """2 agents succeed, 1 fails → 200 with warnings."""
        signals = [
            make_signal("technical", Direction.BUY),
            make_signal("sentiment", Direction.BUY),
        ]
        result = make_decision_result(signals)
        result = result.model_copy(update={"warnings": ["Only 2 of 3 agents responded."]})
        errors = {"fundamental": "Timed out."}

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, errors))):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["warnings"]) >= 1

    def test_failed_agent_appears_in_agents_list(self, client):
        """Failed agent should appear in the agents list with error field."""
        signals = [make_signal("technical", Direction.BUY)]
        result = make_decision_result(signals)
        errors = {
            "sentiment": "Timed out.",
            "fundamental": "Import error.",
        }

        with patch("backend.api.routes.research.analyze", new=AsyncMock(return_value=(result, errors))):
            resp = client.post("/api/research/analyze", json={"ticker": "AAPL"})

        body = resp.json()
        agent_names = [a["agent_name"] for a in body["agents"]]
        assert "sentiment" in agent_names
        assert "fundamental" in agent_names

        error_agents = [a for a in body["agents"] if a.get("error")]
        assert len(error_agents) == 2


# ---------------------------------------------------------------------------
# Other endpoints
# ---------------------------------------------------------------------------

class TestOtherEndpoints:
    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert "version" in body

    def test_health_returns_healthy(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_research_health_returns_healthy(self, client):
        resp = client.get("/api/research/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
