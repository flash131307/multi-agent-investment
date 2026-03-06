"""Technical analysis agent models."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RegimeType(str, Enum):
    """Market regime classification."""
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


class Reliability(str, Enum):
    """Tool output reliability level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ToolSignal(str, Enum):
    """Semantic signal from a technical tool."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class MarketRegime(BaseModel, frozen=True):
    """Output from the market_regime tool — mandatory first ReAct step."""
    regime_type: RegimeType
    trend_strength: float = Field(..., ge=0.0, le=1.0)
    volatility: float = Field(..., ge=0.0, description="ATR-based volatility measure")
    interpretation: str = Field(..., min_length=1)


class ToolOutput(BaseModel, frozen=True):
    """Semantic output from any technical indicator tool."""
    tool_name: str
    signal: ToolSignal
    reliability: Reliability
    interpretation: str = Field(..., min_length=1)
    raw_values: dict[str, Any] = Field(default_factory=dict)


class ReActStep(BaseModel, frozen=True):
    """Single step in the ReAct reasoning loop."""
    step_number: int = Field(..., ge=1)
    thought: str
    action: str
    observation: ToolOutput | MarketRegime
