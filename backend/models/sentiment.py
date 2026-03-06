"""News sentiment agent models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SentimentLabel(str, Enum):
    """FinBERT classification output."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class NewsArticle(BaseModel, frozen=True):
    """Raw news article from Finnhub."""
    headline: str
    summary: str
    source: str
    published_at: datetime
    url: str = ""


class ArticleSentiment(BaseModel, frozen=True):
    """FinBERT classification result for a single article."""
    article: NewsArticle
    label: SentimentLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_weight: float = Field(..., gt=0.0)
    time_decay: float = Field(..., ge=0.0, le=1.0)

    @property
    def effective_weight(self) -> float:
        """Combined weight used in aggregation."""
        return self.confidence * self.time_decay * self.source_weight


class AggregationResult(BaseModel, frozen=True):
    """Layer 3 weighted aggregation output."""
    weighted_sentiment: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    article_count: int = Field(..., ge=0)
    consistency_factor: float = Field(..., ge=0.0, le=1.0)
    coverage_factor: float = Field(..., ge=0.0, le=1.0)
