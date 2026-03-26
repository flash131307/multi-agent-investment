"""Small HTTP client for structured public sentiment snapshots."""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass

import requests

from backend.models.sentiment import (
    PublicSentimentSnapshot,
    PublicSentimentSource,
    SourceAlignment,
)

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 4.0
_DEFAULT_DAYS = 7


@dataclass(frozen=True)
class _SourceSpec:
    name: str
    path: str
    activity_field: str


_SOURCE_SPECS = (
    _SourceSpec("reddit", "/reddit/stocks/v1/compare", "mentions"),
    _SourceSpec("x", "/x/stocks/v1/compare", "mentions"),
    _SourceSpec("polymarket", "/polymarket/stocks/v1/compare", "trade_count"),
)


class AdanosClient:
    """Fetch compact social/public stock sentiment from the Adanos API."""

    def __init__(self, api_key: str, *, base_url: str, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": api_key, "Accept": "application/json"})

    def get_public_sentiment_snapshot(
        self,
        ticker: str,
        *,
        days_back: int = _DEFAULT_DAYS,
    ) -> PublicSentimentSnapshot | None:
        """Fetch and aggregate public sentiment for one ticker across supported sources."""
        sources: list[PublicSentimentSource] = []

        for spec in _SOURCE_SPECS:
            source_row = self._fetch_compare_row(spec, ticker=ticker, days_back=days_back)
            if source_row is None:
                continue
            sources.append(source_row)

        if not sources:
            return None

        average_buzz = round(sum(item.buzz_score for item in sources) / len(sources), 1)
        average_bullish_pct = round(sum(item.bullish_pct for item in sources) / len(sources), 1)
        coverage_factor = round(len(sources) / len(_SOURCE_SPECS), 2)
        source_alignment, alignment_factor = _classify_alignment(
            [item.bullish_pct for item in sources]
        )

        return PublicSentimentSnapshot(
            ticker=ticker.upper(),
            days_back=days_back,
            sources=sources,
            average_buzz=average_buzz,
            average_bullish_pct=average_bullish_pct,
            coverage_factor=coverage_factor,
            alignment_factor=alignment_factor,
            source_alignment=source_alignment,
        )

    def _fetch_compare_row(
        self,
        spec: _SourceSpec,
        *,
        ticker: str,
        days_back: int,
    ) -> PublicSentimentSource | None:
        try:
            response = self._session.get(
                f"{self._base_url}{spec.path}",
                params={"tickers": ticker.upper(), "days": days_back},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.info("Adanos %s compare request failed for %s: %s", spec.name, ticker, exc)
            return None
        except ValueError as exc:
            logger.info("Adanos %s compare returned invalid JSON for %s: %s", spec.name, ticker, exc)
            return None

        row = _extract_row(payload, ticker)
        if row is None:
            return None

        buzz_score = _as_float(row.get("buzz_score"))
        bullish_pct = _as_float(row.get("bullish_pct"))
        if buzz_score is None or bullish_pct is None:
            return None

        return PublicSentimentSource(
            source=spec.name,
            buzz_score=round(buzz_score, 1),
            bullish_pct=round(bullish_pct, 1),
            trend=row.get("trend"),
            mentions=_as_int(row.get("mentions")) if spec.activity_field == "mentions" else None,
            trade_count=_as_int(row.get("trade_count")) if spec.activity_field == "trade_count" else None,
        )


def _extract_row(payload: object, ticker: str) -> dict | None:
    """Return the matching stock row from a compare payload."""
    if not isinstance(payload, dict):
        return None
    stocks = payload.get("stocks")
    if not isinstance(stocks, list):
        return None
    normalized = ticker.upper()
    for item in stocks:
        if isinstance(item, dict) and str(item.get("ticker") or "").upper() == normalized:
            return item
    return None


def _as_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _as_int(value: object) -> int | None:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _classify_alignment(values: list[float]) -> tuple[SourceAlignment, float]:
    """Map source dispersion to a discrete label and numeric trust factor."""
    if not values:
        return SourceAlignment.SINGLE_SOURCE, 0.0
    if len(values) == 1:
        return SourceAlignment.SINGLE_SOURCE, 0.4

    spread = max(values) - min(values)
    if spread <= 12:
        return SourceAlignment.ALIGNED, 1.0
    if spread <= 25:
        return SourceAlignment.MIXED, 0.75

    # Divergent sources still carry information, but should not dominate the score.
    if len(values) >= 3:
        try:
            std_dev = statistics.pstdev(values)
        except statistics.StatisticsError:
            std_dev = spread / 2
        if std_dev <= 15:
            return SourceAlignment.MIXED, 0.7
    return SourceAlignment.DIVERGENT, 0.45
