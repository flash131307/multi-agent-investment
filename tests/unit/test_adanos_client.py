"""Unit tests for the Adanos public sentiment client."""

from unittest.mock import MagicMock

from backend.models.sentiment import SourceAlignment
from backend.services.adanos_client import AdanosClient


def _response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_public_sentiment_snapshot_aggregates_supported_sources():
    client = AdanosClient("sk_test", base_url="https://api.adanos.org")
    client._session.get = MagicMock(side_effect=[
        _response(
            {
                "stocks": [
                    {
                        "ticker": "TSLA",
                        "buzz_score": 81.2,
                        "bullish_pct": 46,
                        "trend": "rising",
                        "mentions": 647,
                    }
                ]
            }
        ),
        _response(
            {
                "stocks": [
                    {
                        "ticker": "TSLA",
                        "buzz_score": 86.4,
                        "bullish_pct": 58,
                        "trend": "falling",
                        "mentions": 2650,
                    }
                ]
            }
        ),
        _response(
            {
                "stocks": [
                    {
                        "ticker": "TSLA",
                        "buzz_score": 55.7,
                        "bullish_pct": 72,
                        "trend": "stable",
                        "trade_count": 3731,
                    }
                ]
            }
        ),
    ])

    snapshot = client.get_public_sentiment_snapshot("TSLA", days_back=7)

    assert snapshot is not None
    assert snapshot.ticker == "TSLA"
    assert snapshot.average_buzz == 74.4
    assert snapshot.average_bullish_pct == 58.7
    assert snapshot.coverage_factor == 1.0
    assert snapshot.source_alignment == SourceAlignment.MIXED
    assert [item.source for item in snapshot.sources] == ["reddit", "x", "polymarket"]
    assert snapshot.sources[0].mentions == 647
    assert snapshot.sources[2].trade_count == 3731


def test_public_sentiment_snapshot_skips_invalid_rows_and_returns_none_when_empty():
    client = AdanosClient("sk_test", base_url="https://api.adanos.org")
    client._session.get = MagicMock(side_effect=[
        _response({"stocks": [{"ticker": "TSLA", "buzz_score": None, "bullish_pct": 46}]}),
        _response({"stocks": []}),
        _response({"unexpected": "shape"}),
    ])

    snapshot = client.get_public_sentiment_snapshot("TSLA", days_back=7)

    assert snapshot is None
