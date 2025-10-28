"""
Router Agent - Analyzes user query to determine intent and extract tickers.
Routes to appropriate specialist agents based on analysis.
"""
import re
import json
from typing import List
from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.config.settings import settings
from backend.services.ticker_resolver import ticker_resolver


class RouterAgent(BaseAgent):
    """
    Analyzes user queries to:
    1. Determine primary intent
    2. Extract stock tickers
    3. Set routing flags for specialist agents
    """

    def __init__(self):
        super().__init__("router")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

        # Ticker resolver for dynamic company name resolution
        self.ticker_resolver = ticker_resolver

        # Common stock ticker patterns (for direct ticker detection)
        self.ticker_pattern = re.compile(r'\b([A-Z]{1,5})\b')

        # Known ticker list for validation (basic set, resolver handles more)
        self.known_tickers = {
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA",
            "JPM", "V", "WMT", "JNJ", "PG", "MA", "UNH", "HD", "DIS"
        }

    async def execute(self, state: AgentState) -> AgentState:
        """
        Analyze query and determine routing.

        Args:
            state: Current agent state

        Returns:
            State with intent, tickers, and routing flags set
        """
        query = state["user_query"]

        # Extract tickers from query (now async with dynamic resolution)
        tickers = await self._extract_tickers(query)

        # Analyze intent using LLM
        intent, should_fetch_market, should_analyze_sentiment, should_retrieve = \
            await self._analyze_intent(query, tickers)

        # Return only the fields we're updating
        return {
            "intent": intent,
            "tickers": tickers,
            "should_fetch_market_data": should_fetch_market,
            "should_analyze_sentiment": should_analyze_sentiment,
            "should_retrieve_context": should_retrieve
        }

    async def _extract_tickers(self, query: str) -> List[str]:
        """
        Extract stock tickers from query using dynamic resolution.

        Supports:
        - Direct ticker symbols (AAPL, MSFT)
        - Company names (Apple, Microsoft)
        - Aliases and abbreviations (Facebook → META, J&J → JNJ)

        Args:
            query: User query

        Returns:
            List of ticker symbols
        """
        tickers = set()

        # Method 1: Find explicit ticker symbols (uppercase 1-5 chars)
        potential_tickers = self.ticker_pattern.findall(query.upper())
        for ticker in potential_tickers:
            if ticker in self.known_tickers:
                tickers.add(ticker)

        # Method 2: Use dynamic ticker resolver for company names
        # Extract capitalized words (potential company names)
        # Pattern: words starting with capital letter
        capitalized_words = re.findall(r'\b([A-Z][a-zA-Z&]+(?:\s+[A-Z][a-zA-Z]+)*)\b', query)

        # Filter out common non-company words
        stopwords = {'What', 'How', 'When', 'Where', 'Why', 'Who', 'Which',
                     'The', 'Is', 'Are', 'Can', 'Could', 'Should', 'Would',
                     'Give', 'Tell', 'Show', 'Analyze', 'Compare', 'Research'}

        for word in capitalized_words:
            # Skip stopwords and short words
            if word in stopwords or len(word) < 2:
                continue

            # Try to resolve as company name
            ticker = await self.ticker_resolver.resolve(word)
            if ticker:
                tickers.add(ticker)

        # Method 3: Try phrases separated by "and", "vs", ","
        # This catches "Microsoft and Google" or "AAPL vs TSLA"
        phrases = re.split(r'\s+(?:and|vs|versus|,)\s+', query, flags=re.IGNORECASE)
        for phrase in phrases:
            phrase = phrase.strip()
            # Remove leading question words
            phrase = re.sub(r'^(?:What|How|When|Where|Why|Who|Which)\s+(?:is|are|about)?\s*', '', phrase, flags=re.IGNORECASE)
            phrase = phrase.strip()

            if phrase and len(phrase) > 2:
                # Try to resolve the cleaned phrase
                ticker = await self.ticker_resolver.resolve(phrase)
                if ticker:
                    tickers.add(ticker)

        # Convert to sorted list
        tickers = sorted(list(tickers))

        self.logger.info(f"Extracted tickers: {tickers}")
        return tickers

    async def _analyze_intent(
        self,
        query: str,
        tickers: List[str]
    ) -> tuple[str, bool, bool, bool]:
        """
        Use LLM to analyze query intent.

        Args:
            query: User query
            tickers: Extracted tickers

        Returns:
            Tuple of (intent, fetch_market, analyze_sentiment, retrieve_context)
        """
        prompt = f"""Analyze this investment research query and determine:

1. Primary intent (choose ONE):
   - "price_query": User wants current price/market data
   - "fundamental_analysis": User wants financial metrics, ratios, fundamentals
   - "sentiment_analysis": User wants news and sentiment analysis
   - "general_research": User wants comprehensive research report
   - "comparison": User wants to compare multiple stocks

2. What data to fetch:
   - market_data: Should we fetch current price/fundamentals? (true/false)
   - sentiment: Should we analyze news/sentiment? (true/false)
   - context: Should we retrieve EDGAR/historical documents? (true/false)

User query: "{query}"
Tickers found: {tickers if tickers else "None"}

Respond in JSON format:
{{
    "intent": "<intent_type>",
    "fetch_market_data": <true/false>,
    "analyze_sentiment": <true/false>,
    "retrieve_context": <true/false>,
    "reasoning": "<brief explanation>"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing investment research queries. Always respond with valid JSON. Respond in the same language as the user's query (English or Chinese)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            # Parse JSON response
            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            result = json.loads(content)

            intent = result.get("intent", "general_research")
            fetch_market = result.get("fetch_market_data", True)
            analyze_sent = result.get("analyze_sentiment", True)
            retrieve = result.get("retrieve_context", True)

            self.logger.info(
                f"Intent analysis: {intent} | "
                f"market={fetch_market}, sentiment={analyze_sent}, context={retrieve}"
            )
            self.logger.debug(f"Reasoning: {result.get('reasoning', 'N/A')}")

            return intent, fetch_market, analyze_sent, retrieve

        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}, using defaults")

            # Fallback: Conservative defaults
            return "general_research", True, True, True


# Singleton instance
router_agent = RouterAgent()
