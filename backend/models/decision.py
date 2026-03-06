"""Decision Hub output models."""

from enum import Enum
from pydantic import BaseModel, Field
from .signals import Direction, AgentSignal


class RiskMode(str, Enum):
    """Risk mode derived from consistency score."""
    NORMAL = "NORMAL"      # consistency >= 0.7 — full weight
    CAUTIOUS = "CAUTIOUS"  # 0.4 <= consistency < 0.7 — 0.8x
    RISK = "RISK"          # consistency < 0.4 — 0.6x

    @property
    def multiplier(self) -> float:
        return {"NORMAL": 1.0, "CAUTIOUS": 0.8, "RISK": 0.6}[self.value]


class ConsistencyScore(BaseModel, frozen=True):
    """Intermediate consistency calculation breakdown."""
    direction_score: float = Field(..., ge=0.0, le=1.0)
    strength_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    raw_consistency: float = Field(..., ge=0.0, le=1.0)
    risk_mode: RiskMode
    final_consistency: float = Field(..., ge=0.0, le=1.0)


class WeightAllocation(BaseModel, frozen=True):
    """Per-agent normalized weight after regime and confidence adjustments."""
    agent_name: str
    base_weight: float = Field(..., gt=0.0)
    regime_modifier: float = Field(..., gt=0.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    final_weight: float = Field(..., ge=0.0, le=1.0)


class DecisionResult(BaseModel, frozen=True):
    """Final output from the Decision Hub."""
    direction: Direction
    confidence: float = Field(..., ge=0.0, le=1.0)
    consistency: ConsistencyScore
    weights: list[WeightAllocation]
    signals: list[AgentSignal]
    aggregated_score: float
    reasoning: str = ""
    warnings: list[str] = Field(default_factory=list)
