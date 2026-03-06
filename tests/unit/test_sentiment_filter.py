"""
Unit tests for backend/agents/sentiment/filter.py
"""
import pytest
from datetime import datetime, timedelta, timezone

from backend.models.sentiment import NewsArticle
from backend.agents.sentiment.filter import filter_articles, get_source_weight


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_article(
    headline: str,
    summary: str = "Some summary text.",
    source: str = "unknown",
    days_ago: int = 0,
    url: str = "",
) -> NewsArticle:
    published_at = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return NewsArticle(
        headline=headline,
        summary=summary,
        source=source,
        published_at=published_at,
        url=url,
    )


# ---------------------------------------------------------------------------
# Source weight tests
# ---------------------------------------------------------------------------

class TestGetSourceWeight:
    def test_reuters_weight(self):
        assert get_source_weight("reuters") == 1.2

    def test_reuters_case_insensitive(self):
        assert get_source_weight("Reuters") == 1.2
        assert get_source_weight("REUTERS") == 1.2

    def test_bloomberg_weight(self):
        assert get_source_weight("bloomberg") == 1.0
        assert get_source_weight("Bloomberg") == 1.0

    def test_unknown_source_weight(self):
        assert get_source_weight("cnbc") == 0.7
        assert get_source_weight("") == 0.7
        assert get_source_weight("random-source") == 0.7


# ---------------------------------------------------------------------------
# Empty input tests
# ---------------------------------------------------------------------------

class TestFilterArticlesEmpty:
    def test_empty_list_returns_empty(self):
        result = filter_articles([], ticker="AAPL")
        assert result == []


# ---------------------------------------------------------------------------
# Relevance filter tests
# ---------------------------------------------------------------------------

class TestRelevanceFilter:
    def test_keeps_articles_mentioning_ticker_in_headline(self):
        articles = [
            _make_article("AAPL surges after earnings beat"),
            _make_article("Weather update for today"),
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 1
        assert "AAPL" in result[0].headline

    def test_keeps_articles_mentioning_ticker_in_summary(self):
        articles = [
            _make_article("Tech giant posts strong results", summary="AAPL reported EPS of $2."),
            _make_article("Sports news today", summary="Game recap from last night."),
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 1

    def test_ticker_match_is_case_insensitive(self):
        articles = [
            _make_article("aapl beats expectations"),
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 1

    def test_company_name_match(self):
        articles = [
            _make_article("Apple announces new iPhone model"),
            _make_article("General market update: stocks rise"),
        ]
        result = filter_articles(articles, ticker="AAPL", company_name="Apple")
        assert len(result) == 1
        assert "Apple" in result[0].headline

    def test_fallback_when_no_relevant_articles(self):
        """If 0 articles are relevant, return all as fallback."""
        articles = [
            _make_article("Unrelated news about sports"),
            _make_article("Weather forecast for the weekend"),
        ]
        result = filter_articles(articles, ticker="AAPL")
        # All articles returned as fallback
        assert len(result) == len(articles)

    def test_fallback_preserves_all_articles(self):
        articles = [_make_article(f"News item {i}") for i in range(5)]
        result = filter_articles(articles, ticker="ZZZZ")
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_removes_near_duplicate_headlines(self):
        """Two headlines sharing >80% tokens → only one kept."""
        base = "Apple beats quarterly earnings expectations significantly"
        # This headline has many overlapping tokens (>80% Jaccard)
        near_dup = "Apple beats quarterly earnings expectations significantly today"
        articles = [
            _make_article(base, summary="AAPL results"),
            _make_article(near_dup, summary="AAPL results again"),
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 1

    def test_keeps_distinct_headlines(self):
        articles = [
            _make_article("AAPL reports record revenue for Q3", summary="Revenue was high."),
            _make_article("AAPL faces regulatory scrutiny in Europe", summary="EU investigation ongoing."),
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 2

    def test_dedup_keeps_first_seen(self):
        """The first article in order is kept, the near-duplicate is discarded."""
        first = _make_article("AAPL stock rises on strong earnings report", days_ago=1)
        duplicate = _make_article("AAPL stock rises on strong earnings report today", days_ago=0)
        articles = [first, duplicate]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Limit tests
# ---------------------------------------------------------------------------

class TestLimit:
    def test_caps_at_25_articles(self):
        articles = [
            _make_article(f"AAPL news update number {i}", days_ago=i)
            for i in range(30)
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 25

    def test_returns_most_recent_when_capped(self):
        articles = [
            _make_article(f"AAPL news item day {i}", days_ago=i)
            for i in range(30)
        ]
        result = filter_articles(articles, ticker="AAPL")
        # Most recent should appear first
        dates = [a.published_at for a in result]
        assert dates == sorted(dates, reverse=True)

    def test_fewer_than_25_articles_all_returned(self):
        articles = [
            _make_article(f"AAPL update {i}", days_ago=i)
            for i in range(10)
        ]
        result = filter_articles(articles, ticker="AAPL")
        assert len(result) == 10
