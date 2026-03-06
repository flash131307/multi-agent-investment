"""
Finnhub API client with caching and rate limiting.
"""
import logging
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 300  # 5 minutes
_RATE_LIMIT_CALLS = 60
_RATE_LIMIT_WINDOW = 60.0  # seconds


class FinnhubClient:
    """Client for the Finnhub financial data API."""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        # Cache: ticker -> (timestamp, data)
        self._news_cache: dict[str, tuple[float, list[dict]]] = {}
        # Rate limiting: deque of call timestamps within the sliding window
        self._call_times: deque[float] = deque()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enforce_rate_limit(self) -> None:
        """Block until we are allowed to make another API call."""
        now = time.monotonic()
        # Remove timestamps outside the window
        while self._call_times and self._call_times[0] < now - _RATE_LIMIT_WINDOW:
            self._call_times.popleft()

        if len(self._call_times) >= _RATE_LIMIT_CALLS:
            oldest = self._call_times[0]
            sleep_for = _RATE_LIMIT_WINDOW - (now - oldest)
            if sleep_for > 0:
                logger.debug("Rate limit reached; sleeping %.2fs", sleep_for)
                time.sleep(sleep_for)
            # Prune again after sleeping
            now = time.monotonic()
            while self._call_times and self._call_times[0] < now - _RATE_LIMIT_WINDOW:
                self._call_times.popleft()

        self._call_times.append(time.monotonic())

    def _get(self, endpoint: str, params: dict[str, Any]) -> Any:
        """Execute a GET request against the Finnhub API."""
        self._enforce_rate_limit()
        params["token"] = self._api_key
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_news(self, ticker: str, days_back: int = 7) -> list[dict]:
        """
        Fetch company news from Finnhub.

        Results are cached per ticker for 5 minutes.  If the API call fails,
        a warning is logged and an empty list is returned.
        """
        now_ts = time.monotonic()
        cached = self._news_cache.get(ticker)
        if cached is not None:
            cache_ts, cache_data = cached
            if now_ts - cache_ts < _CACHE_TTL_SECONDS:
                logger.debug("Cache hit for ticker %s", ticker)
                return cache_data

        try:
            to_date = datetime.now(tz=timezone.utc)
            from_date = to_date - timedelta(days=days_back)
            data = self._get(
                "company-news",
                {
                    "symbol": ticker,
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                },
            )
            articles: list[dict] = data if isinstance(data, list) else []
        except requests.HTTPError as exc:
            logger.warning(
                "Finnhub news request failed for %s (HTTP %s): %s",
                ticker,
                exc.response.status_code if exc.response is not None else "?",
                exc,
            )
            return []
        except Exception as exc:
            logger.warning("Finnhub news request failed for %s: %s", ticker, exc)
            return []

        self._news_cache[ticker] = (now_ts, articles)
        return articles

    def get_ticker_profile(self, ticker: str) -> dict:
        """Fetch company profile from Finnhub /stock/profile2."""
        try:
            data = self._get("stock/profile2", {"symbol": ticker})
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Finnhub profile request failed for %s: %s", ticker, exc)
            return {}
