"""
Sentiment Agent - Analyzes financial news and sentiment.
Uses RAG pipeline for news retrieval and LLM for sentiment analysis.
"""
import json
from typing import List
from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState, SentimentAnalysis
from backend.config.settings import settings
from backend.rag.pipeline import rag_pipeline
from backend.rag.news_aggregator import news_aggregator


class SentimentAgent(BaseAgent):
    """
    Analyzes sentiment for requested tickers:
    - Retrieves recent news from RAG
    - Uses LLM to extract sentiment
    - Identifies key themes
    - Provides summary
    """

    def __init__(self):
        super().__init__("sentiment")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.rag = rag_pipeline
        self.news = news_aggregator

    async def execute(self, state: AgentState) -> AgentState:
        """
        Analyze sentiment for all tickers in state.

        Args:
            state: Current agent state

        Returns:
            State with sentiment_analysis populated
        """
        tickers = state.get("tickers", [])

        if not tickers:
            self.logger.warning("No tickers to analyze sentiment for")
            return state

        # Analyze sentiment for each ticker
        sentiment_results = []

        for ticker in tickers:
            self.logger.info(f"Analyzing sentiment for {ticker}")

            try:
                analysis = await self._analyze_ticker_sentiment(ticker)
                if analysis:
                    sentiment_results.append(analysis)
            except Exception as e:
                self.logger.error(f"Sentiment analysis failed for {ticker}: {e}")
                # Continue with other tickers

        # Return only the fields we're updating (for parallel execution)
        # Always return a list (empty or with data) for Annotated[List, operator.add]
        return {
            "sentiment_analysis": sentiment_results
        }

    async def _analyze_ticker_sentiment(self, ticker: str) -> SentimentAnalysis:
        """
        Analyze sentiment for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            SentimentAnalysis dict
        """
        # 1. Retrieve recent news from vector store
        news_docs = await self._retrieve_news(ticker)

        if not news_docs:
            self.logger.warning(f"No news found for {ticker}")
            return None

        # 2. Format news for LLM
        news_text = self._format_news_for_llm(news_docs)

        # 3. Analyze sentiment using LLM
        sentiment_data = await self._llm_sentiment_analysis(ticker, news_text, len(news_docs))

        return sentiment_data

    async def _retrieve_news(self, ticker: str) -> List[dict]:
        """
        Retrieve recent news for ticker from RAG.

        Args:
            ticker: Stock ticker

        Returns:
            List of news documents
        """
        try:
            # Try vector store first
            query = f"Recent news and updates about {ticker}"
            results = await self.rag.retrieve_context(
                query=query,
                ticker=ticker,
                source="news",
                top_k=10
            )

            if results:
                return results

            # Fallback to news aggregator
            news_summary = self.news.get_news_summary(ticker, limit=10)
            if news_summary and news_summary.get("news"):
                return [
                    {
                        "text": f"Title: {item.get('title', 'N/A')}\n"
                                f"Publisher: {item.get('publisher', 'Unknown')}\n"
                                f"Published: {item.get('publish_time', 'Unknown')}",
                        "metadata": {"ticker": ticker, "source": "news"}
                    }
                    for item in news_summary["news"]
                ]

            return []

        except Exception as e:
            self.logger.error(f"News retrieval failed: {e}")
            return []

    def _format_news_for_llm(self, news_docs: List[dict]) -> str:
        """
        Format news documents for LLM input.

        Args:
            news_docs: List of news documents

        Returns:
            Formatted string
        """
        formatted = []

        for i, doc in enumerate(news_docs[:10], 1):  # Limit to 10
            text = doc.get("text", "")
            formatted.append(f"{i}. {text[:300]}...")  # Truncate long texts

        return "\n\n".join(formatted)

    async def _llm_sentiment_analysis(
        self,
        ticker: str,
        news_text: str,
        news_count: int
    ) -> SentimentAnalysis:
        """
        Use LLM to analyze sentiment from news.

        Args:
            ticker: Stock ticker
            news_text: Formatted news text
            news_count: Number of news items

        Returns:
            SentimentAnalysis dict
        """
        prompt = f"""Analyze the sentiment of these recent news articles about {ticker}:

{news_text}

Provide:
1. Overall sentiment (positive/neutral/negative)
2. Confidence level (0.0 to 1.0)
3. Key themes (3-5 main topics)
4. Brief summary (2-3 sentences)

Respond in JSON format:
{{
    "sentiment": "<positive/neutral/negative>",
    "confidence": <0.0-1.0>,
    "themes": ["theme1", "theme2", ...],
    "summary": "<brief summary>"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst. Analyze news sentiment objectively and respond with valid JSON. Respond in the same language as the user's query (English or Chinese)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            result = json.loads(content)

            # Create SentimentAnalysis object
            analysis = SentimentAnalysis(
                ticker=ticker,
                overall_sentiment=result.get("sentiment", "neutral"),
                confidence=float(result.get("confidence", 0.5)),
                key_themes=result.get("themes", []),
                news_count=news_count,
                summary=result.get("summary", "No summary available")
            )

            self.logger.info(
                f"✅ {ticker} sentiment: {analysis['overall_sentiment']} "
                f"(confidence: {analysis['confidence']:.2f})"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"LLM sentiment analysis failed: {e}")

            # Return neutral sentiment as fallback
            return SentimentAnalysis(
                ticker=ticker,
                overall_sentiment="neutral",
                confidence=0.0,
                key_themes=[],
                news_count=news_count,
                summary=f"Sentiment analysis unavailable. Based on {news_count} news items."
            )


# Singleton instance
sentiment_agent = SentimentAgent()
