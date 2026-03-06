"""Core signal models shared across all agents."""

from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Direction(str, Enum):
    """Trading signal direction."""
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"


class Strength(str, Enum):
    """Signal conviction strength."""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"

    @property
    def numeric(self) -> float:
        """Return numeric value for math operations."""
        return {"STRONG": 1.0, "MODERATE": 0.7, "WEAK": 0.4}[self.value]


class AgentSignal(BaseModel, frozen=True):
    """
    Immutable output from any analysis agent.
    Consumed by Decision Hub for fusion.
    """
    agent_name: str = Field(..., description="Identifier of the producing agent")
    direction: Direction
    strength: Strength
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence [0.0, 1.0]")
    reasoning: str = Field(..., min_length=1, description="Human-readable rationale")

    @model_validator(mode="after")
    def validate_neutral_strength(self) -> "AgentSignal":
        """NEUTRAL direction should use WEAK strength by convention."""
        if self.direction == Direction.NEUTRAL and self.strength == Strength.STRONG:
            raise ValueError("NEUTRAL direction cannot have STRONG strength")
        return self
