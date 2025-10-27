"""
Financial news aggregation service.
Aggregates news from multiple sources (Yahoo Finance, etc.) with sentiment analysis ready.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from backend.services.yahoo_finance import yahoo_finance

logger = logging.getLogger(__name__)


class NewsAggregator:
    """Aggregates financial news from multiple sources."""

    def __init__(self):
        """Initialize news aggregator."""
        self.yahoo = yahoo_finance

    def get_ticker_news(
        self,
        ticker: str,
        limit: int = 20,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get recent news for a specific ticker.

        Args:
            ticker: Stock ticker
            limit: Maximum number of news items
            days_back: Number of days to look back

        Returns:
            List of news items with metadata
        """
        try:
            # Get news from Yahoo Finance
            yahoo_news = self.yahoo.get_news(ticker, limit=limit)

            # Filter by date
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            filtered_news = []

            for news_item in yahoo_news:
                publish_time = news_item.get("publish_time", "")
                try:
                    news_date = datetime.fromisoformat(publish_time)
                    if news_date >= cutoff_date:
                        filtered_news.append(news_item)
                except:
                    # Include news with invalid dates
                    filtered_news.append(news_item)

            logger.info(f"✅ Aggregated {len(filtered_news)} news items for {ticker}")
            return filtered_news

        except Exception as e:
            logger.error(f"❌ Failed to aggregate news for {ticker}: {e}")
            return []

    def get_market_news(
        self,
        tickers: List[str],
        limit_per_ticker: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get news for multiple tickers (market overview).

        Args:
            tickers: List of stock tickers
            limit_per_ticker: Max news items per ticker

        Returns:
            Dict mapping tickers to their news items
        """
        market_news = {}

        for ticker in tickers:
            news = self.get_ticker_news(ticker, limit=limit_per_ticker, days_back=3)
            if news:
                market_news[ticker] = news

        total_items = sum(len(items) for items in market_news.values())
        logger.info(f"✅ Aggregated {total_items} market news items for {len(tickers)} tickers")

        return market_news

    def format_news_for_llm(
        self,
        news_items: List[Dict[str, Any]]
    ) -> str:
        """
        Format news items for LLM consumption.

        Args:
            news_items: List of news items

        Returns:
            Formatted string for LLM context
        """
        if not news_items:
            return "No recent news available."

        text = "Recent Financial News:\n\n"

        for i, news in enumerate(news_items[:10], 1):  # Limit to 10 for context
            text += f"{i}. {news.get('title', 'Untitled')}\n"
            text += f"   Publisher: {news.get('publisher', 'Unknown')}\n"
            text += f"   Published: {news.get('publish_time', 'Unknown')}\n"

            if news.get('link'):
                text += f"   Link: {news['link']}\n"

            text += "\n"

        return text

    def get_news_summary(
        self,
        ticker: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get news summary with metadata for a ticker.

        Args:
            ticker: Stock ticker
            limit: Number of news items

        Returns:
            Dict with news and metadata
        """
        news_items = self.get_ticker_news(ticker, limit=limit)

        if not news_items:
            return {
                "ticker": ticker,
                "count": 0,
                "news": [],
                "formatted_text": "No recent news available."
            }

        return {
            "ticker": ticker.upper(),
            "count": len(news_items),
            "news": news_items,
            "formatted_text": self.format_news_for_llm(news_items),
            "latest_date": news_items[0].get("publish_time") if news_items else None,
            "oldest_date": news_items[-1].get("publish_time") if news_items else None
        }

    def filter_by_keywords(
        self,
        news_items: List[Dict[str, Any]],
        keywords: List[str],
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter news items by keywords in title.

        Args:
            news_items: List of news items
            keywords: Keywords to search for
            case_sensitive: Whether to match case

        Returns:
            Filtered news items
        """
        filtered = []

        for news in news_items:
            title = news.get("title", "")

            if not case_sensitive:
                title = title.lower()
                keywords = [k.lower() for k in keywords]

            # Check if any keyword is in the title
            if any(keyword in title for keyword in keywords):
                filtered.append(news)

        logger.info(f"✅ Filtered {len(filtered)} news items from {len(news_items)} using keywords: {keywords}")
        return filtered

    def deduplicate_news(
        self,
        news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate news items based on title similarity.

        Args:
            news_items: List of news items

        Returns:
            Deduplicated news items
        """
        seen_titles = set()
        deduplicated = []

        for news in news_items:
            title = news.get("title", "").lower().strip()

            # Simple deduplication by exact title match
            if title not in seen_titles:
                seen_titles.add(title)
                deduplicated.append(news)

        logger.info(f"✅ Deduplicated {len(news_items)} to {len(deduplicated)} news items")
        return deduplicated

    def get_trending_topics(
        self,
        news_items: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, int]]:
        """
        Extract trending topics from news titles.

        Args:
            news_items: List of news items
            top_n: Number of top topics to return

        Returns:
            List of dicts with topic and count
        """
        # Common financial keywords to look for
        keywords = [
            "earnings", "revenue", "profit", "loss", "acquisition",
            "merger", "stock", "shares", "dividend", "growth",
            "decline", "surge", "rally", "crash", "forecast",
            "guidance", "beat", "miss", "upgrade", "downgrade"
        ]

        keyword_counts = {kw: 0 for kw in keywords}

        for news in news_items:
            title = news.get("title", "").lower()
            for keyword in keywords:
                if keyword in title:
                    keyword_counts[keyword] += 1

        # Sort by count and get top N
        sorted_topics = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        trending = [
            {"topic": topic, "count": count}
            for topic, count in sorted_topics[:top_n]
            if count > 0
        ]

        logger.info(f"✅ Identified {len(trending)} trending topics from {len(news_items)} news items")
        return trending


# Singleton instance
news_aggregator = NewsAggregator()
