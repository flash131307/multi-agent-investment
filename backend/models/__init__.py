"""Pydantic models for the Multi-Agent Investment Research System."""

from .signals import Direction, Strength, AgentSignal
from .technical import RegimeType, MarketRegime, Reliability, ToolSignal, ToolOutput, ReActStep
from .sentiment import SentimentLabel, NewsArticle, ArticleSentiment, AggregationResult
from .fundamental import CompanyProfile, AnalysisTask, SubConclusion
from .decision import RiskMode, ConsistencyScore, WeightAllocation, DecisionResult
from .api import AnalysisRequest, AgentSignalResponse, DecisionResponse, AnalysisResponse, ErrorResponse

__all__ = [
    "Direction", "Strength", "AgentSignal",
    "RegimeType", "MarketRegime", "Reliability", "ToolSignal", "ToolOutput", "ReActStep",
    "SentimentLabel", "NewsArticle", "ArticleSentiment", "AggregationResult",
    "CompanyProfile", "AnalysisTask", "SubConclusion",
    "RiskMode", "ConsistencyScore", "WeightAllocation", "DecisionResult",
    "AnalysisRequest", "AgentSignalResponse", "DecisionResponse", "AnalysisResponse", "ErrorResponse",
]
