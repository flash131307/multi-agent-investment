"""
Layer 0 — News fetching from Finnhub API.
Converts raw API dicts into typed NewsArticle models.
"""
import logging
from datetime import datetime, timezone

from backend.models.sentiment import NewsArticle
from backend.services.finnhub_client import FinnhubClient

logger = logging.getLogger(__name__)


def fetch_news(ticker: str, days_back: int = 7) -> list[NewsArticle]:
    """
    Fetch news articles for a ticker using Finnhub.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        days_back: Number of days of history to retrieve.

    Returns:
        List of NewsArticle models. Empty list on failure or no results.
    """
    # Lazy import to avoid module-level Settings() instantiation in tests
    from backend.config.settings import settings  # noqa: PLC0415

    if not settings.finnhub_api_key:
        logger.warning("FINNHUB_API_KEY not set; returning empty news list.")
        return []

    client = FinnhubClient(api_key=settings.finnhub_api_key)
    raw_articles = client.get_news(ticker, days_back=days_back)

    articles: list[NewsArticle] = []
    for raw in raw_articles:
        headline: str = (raw.get("headline") or "").strip()
        summary: str = (raw.get("summary") or "").strip()

        # Filter out articles with empty headline or summary
        if not headline or not summary:
            continue

        # Parse timestamp — Finnhub provides Unix epoch seconds
        ts = raw.get("datetime") or raw.get("publishedAt") or 0
        try:
            published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            logger.debug("Could not parse timestamp %r for article; skipping.", ts)
            continue

        source: str = (raw.get("source") or "").strip().lower()
        url: str = raw.get("url") or ""

        article = NewsArticle(
            headline=headline,
            summary=summary,
            source=source,
            published_at=published_at,
            url=url,
        )
        articles.append(article)

    logger.debug("Fetched %d valid articles for %s", len(articles), ticker)
    return articles
