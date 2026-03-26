"""Optional public/social sentiment fetcher for the SentimentAgent."""

from __future__ import annotations

import logging

from backend.models.sentiment import PublicSentimentSnapshot
from backend.services.adanos_client import AdanosClient

logger = logging.getLogger(__name__)


def fetch_public_sentiment(ticker: str, days_back: int = 7) -> PublicSentimentSnapshot | None:
    """Fetch structured public sentiment when Adanos credentials are configured."""
    from backend.config.settings import settings  # noqa: PLC0415

    if not settings.adanos_api_key:
        return None

    client = AdanosClient(
        settings.adanos_api_key,
        base_url=settings.adanos_base_url,
        timeout=float(settings.adanos_timeout_seconds),
    )
    snapshot = client.get_public_sentiment_snapshot(ticker, days_back=days_back)
    if snapshot is None:
        logger.info("No public sentiment snapshot available for %s.", ticker)
    return snapshot
