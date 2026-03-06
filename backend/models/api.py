"""API request/response models."""

from pydantic import BaseModel, Field
from .signals import Direction, Strength, AgentSignal
from .decision import DecisionResult, RiskMode


class AnalysisRequest(BaseModel):
    """POST /api/research/analyze request body."""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")


class AgentSignalResponse(BaseModel):
    """Per-agent signal in the API response (nullable if agent failed)."""
    agent_name: str
    direction: Direction | None = None
    strength: Strength | None = None
    confidence: float | None = None
    reasoning: str | None = None
    error: str | None = None

    @classmethod
    def from_signal(cls, signal: AgentSignal) -> "AgentSignalResponse":
        return cls(
            agent_name=signal.agent_name,
            direction=signal.direction,
            strength=signal.strength,
            confidence=signal.confidence,
            reasoning=signal.reasoning,
        )

    @classmethod
    def from_error(cls, agent_name: str, error: str) -> "AgentSignalResponse":
        return cls(agent_name=agent_name, error=error)


class DecisionResponse(BaseModel):
    """Decision Hub output in the API response."""
    direction: Direction
    confidence: float
    risk_mode: RiskMode
    consistency_score: float
    aggregated_score: float
    reasoning: str


class AnalysisResponse(BaseModel):
    """Full response from POST /api/research/analyze."""
    ticker: str
    decision: DecisionResponse
    agents: list[AgentSignalResponse]
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def from_decision_result(
        cls,
        ticker: str,
        result: DecisionResult,
        agent_errors: dict[str, str] | None = None,
    ) -> "AnalysisResponse":
        agent_errors = agent_errors or {}

        # Build per-agent responses (signal or error)
        signal_map = {s.agent_name: s for s in result.signals}
        all_agent_names = list(signal_map.keys()) + list(agent_errors.keys())

        agents = []
        for name in all_agent_names:
            if name in signal_map:
                agents.append(AgentSignalResponse.from_signal(signal_map[name]))
            else:
                agents.append(AgentSignalResponse.from_error(name, agent_errors[name]))

        return cls(
            ticker=ticker,
            decision=DecisionResponse(
                direction=result.direction,
                confidence=result.confidence,
                risk_mode=result.consistency.risk_mode,
                consistency_score=result.consistency.final_consistency,
                aggregated_score=result.aggregated_score,
                reasoning=result.reasoning,
            ),
            agents=agents,
            warnings=result.warnings,
        )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str | None = None
