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
        prompt = f"""Analyze this investment research query and determine the intent and required data sources.

## Intent Types & Flag Mapping

1. **price_query**: Current price or market data only
   - Examples: "What's AAPL price?", "Show me Microsoft stock price", "苹果股价多少？"
   - Flags: market_data=true, sentiment=false, context=false

2. **fundamental_analysis**: Financial metrics, valuation, ratios
   - Examples: "What's Tesla P/E ratio?", "Analyze Amazon fundamentals", "微软的财务指标如何？"
   - Flags: market_data=true, sentiment=false, context=true

3. **sentiment_analysis**: News, market sentiment, public opinion
   - Examples: "What's the sentiment on Tesla?", "Recent news about Apple", "特斯拉的市场情绪如何？"
   - Flags: market_data=true, sentiment=true, context=false

4. **general_research**: Comprehensive investment analysis
   - Examples: "Should I invest in Apple?", "Analyze Microsoft", "微软的投资前景如何？"
   - Flags: market_data=true, sentiment=true, context=true

5. **comparison**: Compare multiple stocks or sectors
   - Examples: "Compare Tesla vs Ford", "Apple vs Microsoft", "比较特斯拉和传统汽车制造商"
   - Flags: market_data=true, sentiment=false, context=true

## Important Rules

- **Only set flags to true if explicitly needed for the query**
- If query only asks for price → DON'T enable sentiment or context
- If query asks for sentiment → Enable market_data (for context) but DON'T enable context
- If no tickers found → context should be true (for semantic search)
- General/vague queries → use general_research with all flags true
- Specific queries → use narrow intent with minimal flags

## Negative Examples (What NOT to do)

❌ Query: "What's AAPL price?" → DON'T set sentiment=true (not asked)
❌ Query: "Show Tesla sentiment" → DON'T set context=true (not needed for sentiment)
❌ Query: "Compare stocks" → DON'T use general_research (use comparison)

## User Query Analysis

User query: "{query}"
Tickers found: {tickers if tickers else "None"}

Respond in JSON format:
{{
    "intent": "<price_query|fundamental_analysis|sentiment_analysis|general_research|comparison>",
    "fetch_market_data": <true|false>,
    "analyze_sentiment": <true|false>,
    "retrieve_context": <true|false>,
    "reasoning": "<brief explanation of intent and flag choices>"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert investment query analyzer. Your task is to:\n"
                            "1. Identify the PRIMARY intent (choose the most specific one)\n"
                            "2. Set flags to TRUE only if explicitly needed for that query\n"
                            "3. Follow the examples and rules precisely\n"
                            "4. Be conservative - when in doubt, set flags to FALSE\n"
                            "5. Always respond with valid JSON\n"
                            "6. Provide clear reasoning for your decisions"
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent intent detection
                max_tokens=250
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

            # Explicit boolean parsing with fallback to defaults
            # Handle both boolean and string responses from LLM
            def parse_bool(value, default=False):
                """Parse boolean value, handling strings and None."""
                if value is None:
                    return default
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes')
                return bool(value)

            fetch_market = parse_bool(result.get("fetch_market_data"), default=False)
            analyze_sent = parse_bool(result.get("analyze_sentiment"), default=False)
            retrieve = parse_bool(result.get("retrieve_context"), default=False)

            reasoning = result.get('reasoning', 'N/A')

            # Enhanced logging with flag details
            self.logger.info(
                f"🎯 Intent: {intent} | "
                f"Flags: market_data={fetch_market}, sentiment={analyze_sent}, context={retrieve}"
            )
            self.logger.info(f"💡 Reasoning: {reasoning}")

            # Log decision summary for analysis
            flags_enabled = []
            if fetch_market: flags_enabled.append("market_data")
            if analyze_sent: flags_enabled.append("sentiment")
            if retrieve: flags_enabled.append("context")

            if not flags_enabled:
                self.logger.warning(
                    f"⚠️  No agents enabled for query: '{query[:50]}...' | "
                    f"Intent: {intent} | Tickers: {tickers}"
                )
            else:
                self.logger.debug(f"📊 Enabled agents: {', '.join(flags_enabled)}")

            return intent, fetch_market, analyze_sent, retrieve

        except Exception as e:
            self.logger.error(f"❌ Intent analysis failed: {e}, using fallback strategy")

            # Fallback strategy: Conservative approach
            # If we have tickers, do comprehensive research
            # If no tickers, rely on RAG for semantic search
            has_tickers = bool(tickers)

            if has_tickers:
                self.logger.info(
                    f"🔄 Fallback with tickers: general_research "
                    f"(market=True, sentiment=True, context=True)"
                )
                return "general_research", True, True, True
            else:
                self.logger.info(
                    f"🔄 Fallback without tickers: general_research "
                    f"(market=False, sentiment=False, context=True)"
                )
                return "general_research", False, False, True


# Singleton instance
router_agent = RouterAgent()
