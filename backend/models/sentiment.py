"""News and public sentiment models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SentimentLabel(str, Enum):
    """FinBERT classification output."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SourceAlignment(str, Enum):
    """How aligned public sentiment sources are for a ticker."""

    SINGLE_SOURCE = "single_source"
    ALIGNED = "aligned"
    MIXED = "mixed"
    DIVERGENT = "divergent"


class PublicSentimentSource(BaseModel, frozen=True):
    """Structured social/public sentiment for a single upstream source."""

    source: str
    buzz_score: float = Field(..., ge=0.0, le=100.0)
    bullish_pct: float = Field(..., ge=0.0, le=100.0)
    trend: str | None = None
    mentions: int | None = Field(default=None, ge=0)
    trade_count: int | None = Field(default=None, ge=0)


class PublicSentimentSnapshot(BaseModel, frozen=True):
    """Aggregated public sentiment snapshot across social/public sources."""

    ticker: str
    days_back: int = Field(..., ge=1, le=90)
    sources: list[PublicSentimentSource] = Field(default_factory=list)
    average_buzz: float = Field(..., ge=0.0, le=100.0)
    average_bullish_pct: float = Field(..., ge=0.0, le=100.0)
    coverage_factor: float = Field(..., ge=0.0, le=1.0)
    alignment_factor: float = Field(..., ge=0.0, le=1.0)
    source_alignment: SourceAlignment


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
    public_sentiment_used: bool = False
    public_sentiment_mode: str | None = None
    public_average_buzz: float | None = Field(default=None, ge=0.0, le=100.0)
    public_average_bullish_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    public_source_alignment: SourceAlignment | None = None
