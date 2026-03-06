"""
Layer 2 — FinBERT classification of filtered articles.
"""
import logging
import math
from datetime import datetime, timezone

from backend.models.sentiment import ArticleSentiment, NewsArticle
from backend.services.finbert_service import FinBERTService
from .filter import get_source_weight

logger = logging.getLogger(__name__)

_MAX_TEXT_CHARS = 512


def classify_articles(
    articles: list[NewsArticle],
    finbert: FinBERTService,
) -> list[ArticleSentiment]:
    """
    Run FinBERT classification on a list of news articles.

    Computes time_decay and source_weight for each article so that the
    aggregation layer can produce a weighted average.

    Args:
        articles: Filtered list of NewsArticle objects.
        finbert: FinBERTService instance to use for classification.

    Returns:
        List of ArticleSentiment objects (frozen Pydantic models).
    """
    if not articles:
        return []

    now = datetime.now(tz=timezone.utc)

    # Build input texts
    texts: list[str] = []
    for article in articles:
        combined = f"{article.headline}. {article.summary}"
        texts.append(combined[:_MAX_TEXT_CHARS])

    # Batch classify
    predictions = finbert.classify(texts)

    classified: list[ArticleSentiment] = []
    for article, (label, confidence) in zip(articles, predictions):
        # Days since publication (floor at 0)
        days_ago = max((now - article.published_at).days, 0)
        time_decay = math.exp(-0.1 * days_ago)

        source_weight = get_source_weight(article.source)

        sentiment = ArticleSentiment(
            article=article,
            label=label,
            confidence=confidence,
            source_weight=source_weight,
            time_decay=time_decay,
        )
        classified.append(sentiment)

    logger.debug("Classified %d articles.", len(classified))
    return classified
