"""
Report Generator Agent - Synthesizes all agent outputs into coherent report.
Generates structured investment research reports.
"""
from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.config.settings import settings


class ReportAgent(BaseAgent):
    """
    Generates final investment research report by:
    - Combining market data, sentiment, and context
    - Creating structured, coherent narrative
    - Providing actionable insights
    """

    def __init__(self):
        super().__init__("report")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def execute(self, state: AgentState) -> AgentState:
        """
        Generate final report from all agent outputs.

        Args:
            state: Current agent state with all data collected

        Returns:
            State with final report
        """
        # Extract data from state
        user_query = state.get("user_query", "")
        tickers = state.get("tickers", [])
        intent = state.get("intent", "general_research")
        market_data = state.get("market_data")
        sentiment = state.get("sentiment_analysis")
        analyst_consensus = state.get("analyst_consensus")
        peer_valuation = state.get("peer_valuation")
        context = state.get("retrieved_context")

        self.logger.info(f"Generating report for query: {user_query[:50]}...")

        # Generate report based on available data
        report = await self._generate_report(
            user_query=user_query,
            tickers=tickers,
            intent=intent,
            market_data=market_data,
            sentiment=sentiment,
            analyst_consensus=analyst_consensus,
            peer_valuation=peer_valuation,
            context=context
        )

        # Generate snapshot for beginner investors
        snapshot = await self._generate_snapshot(
            tickers=tickers,
            market_data=market_data,
            sentiment=sentiment,
            analyst_consensus=analyst_consensus,
            peer_valuation=peer_valuation
        )

        # Return both report and snapshot
        return {
            "report": report,
            "snapshot": snapshot
        }

    async def _generate_report(
        self,
        user_query: str,
        tickers: list,
        intent: str,
        market_data: list,
        sentiment: list,
        analyst_consensus: list,
        peer_valuation: list,
        context: list
    ) -> str:
        """
        Generate structured report using LLM.

        Args:
            user_query: Original user query
            tickers: List of tickers
            intent: Query intent
            market_data: Market data from MarketDataAgent
            sentiment: Sentiment analysis from SentimentAgent
            analyst_consensus: Analyst consensus from ForwardLookingAgent
            peer_valuation: Peer valuation comparison from MarketDataAgent
            context: Retrieved documents from RAG

        Returns:
            Formatted report string
        """
        # Build context sections
        market_section = self._format_market_data(market_data) if market_data else "Market data not available."
        sentiment_section = self._format_sentiment(sentiment) if sentiment else "Sentiment analysis not available."
        analyst_section = self._format_analyst_consensus(analyst_consensus) if analyst_consensus else "Analyst consensus not available."
        peer_section = self._format_peer_valuation(peer_valuation) if peer_valuation else "Peer valuation comparison not available."
        context_section = self._format_context(context) if context else "No additional context retrieved."

        # Create prompt
        prompt = f"""Generate a comprehensive investment research report to answer this query:

**User Query:** {user_query}

**Tickers:** {', '.join(tickers) if tickers else 'Not specified'}
**Intent:** {intent}

---

**Market Data:**
{market_section}

---

**Peer Valuation Comparison:**
{peer_section}

---

**Sentiment Analysis:**
{sentiment_section}

---

**Analyst Consensus & Forward-Looking:**
{analyst_section}

---

**Supporting Context:**
{context_section}

---

Please provide a structured report with:

1. **Executive Summary** (2-3 sentences)
2. **Market Analysis**
   - Current price and valuation metrics
   - 52-week trend analysis: Interpret the stock's position in its 52-week range and what it suggests about momentum
3. **Peer Valuation Comparison** (how the stock's valuation compares to sector averages)
4. **Sentiment & News** (recent news themes, sentiment overview)
5. **Analyst Consensus & Forward-Looking** (price targets, upside potential, recommendation)
6. **Key Insights** (3-5 bullet points, include insights from 52-week trends, peer comparison, and analyst expectations)
7. **Conclusion** (investment perspective considering all analysis)

Format the report in clear sections with markdown formatting.
Be objective and data-driven. If information is missing, acknowledge it.

**Important:**
- When analyzing 52-week trends: Stocks near 52-week highs (80%+ position) may indicate strong momentum or potential resistance. Stocks near 52-week lows (20%- position) may indicate weakness or potential support/value opportunity.
- When analyzing peer valuation: Premium valuations (positive %) may indicate market confidence or overvaluation. Discount valuations (negative %) may indicate undervaluation or market concerns."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert investment research analyst. Create clear, professional, and data-driven reports. IMPORTANT: Respond in the same language as the user's query. If the user asks in Chinese, respond in Chinese. If in English, respond in English."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            report = response.choices[0].message.content.strip()

            self.logger.info("✅ Report generated successfully")
            return report

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")

            # Fallback: Simple text report
            return self._generate_fallback_report(
                user_query, tickers, market_data, sentiment
            )

    def _format_market_data(self, market_data: list) -> str:
        """Format market data for report."""
        if not market_data:
            return "No market data available."

        sections = []
        for data in market_data:
            ticker = data.get("ticker", "N/A")
            price = data.get("current_price")
            change = data.get("change_percent")
            market_cap = data.get("market_cap")
            pe = data.get("pe_ratio")

            # 52-week trend data
            week_52_high = data.get("year_high")
            week_52_low = data.get("year_low")
            week_52_position = data.get("week_52_position")
            distance_from_high = data.get("distance_from_high")
            distance_from_low = data.get("distance_from_low")
            trend_signal = data.get("trend_signal")

            section = f"**{ticker}**\n"
            if price:
                section += f"- Current Price: ${price:.2f}"
                if change:
                    section += f" ({change:+.2f}%)"
                section += "\n"

            if market_cap:
                section += f"- Market Cap: ${market_cap:,.0f}\n"
            if pe:
                section += f"- P/E Ratio: {pe:.2f}\n"

            # Add 52-week trend analysis
            if week_52_high and week_52_low and week_52_position is not None:
                section += f"- 52-Week Range: ${week_52_low:.2f} - ${week_52_high:.2f}\n"
                section += f"- Current Position in Range: {week_52_position:.1f}%"

                if trend_signal == "near_high":
                    section += " (Near 52-week high)"
                elif trend_signal == "near_low":
                    section += " (Near 52-week low)"
                else:
                    section += " (Mid-range)"
                section += "\n"

                if distance_from_high is not None:
                    section += f"- Distance from 52W High: {distance_from_high:+.1f}%\n"
                if distance_from_low is not None:
                    section += f"- Distance from 52W Low: {distance_from_low:+.1f}%\n"

            sections.append(section)

        return "\n".join(sections)

    def _format_sentiment(self, sentiment: list) -> str:
        """Format sentiment analysis for report."""
        if not sentiment:
            return "No sentiment data available."

        sections = []
        for s in sentiment:
            ticker = s.get("ticker", "N/A")
            overall = s.get("overall_sentiment", "neutral")
            confidence = s.get("confidence", 0.0)
            themes = s.get("key_themes", [])
            summary = s.get("summary", "")

            section = f"**{ticker}**\n"
            section += f"- Overall Sentiment: {overall.upper()} (confidence: {confidence:.0%})\n"

            if themes:
                section += f"- Key Themes: {', '.join(themes)}\n"

            if summary:
                section += f"- Summary: {summary}\n"

            sections.append(section)

        return "\n".join(sections)

    def _format_analyst_consensus(self, analyst_consensus: list) -> str:
        """Format analyst consensus for report."""
        if not analyst_consensus:
            return "No analyst consensus data available."

        sections = []
        for consensus in analyst_consensus:
            ticker = consensus.get("ticker", "N/A")
            target_mean = consensus.get("target_price_mean")
            target_high = consensus.get("target_price_high")
            target_low = consensus.get("target_price_low")
            current_price = consensus.get("current_price")
            upside_potential = consensus.get("upside_potential")
            recommendation = consensus.get("recommendation")
            num_analysts = consensus.get("num_analysts")

            section = f"**{ticker}**\n"

            if current_price:
                section += f"- Current Price: ${current_price:.2f}\n"

            if target_mean:
                section += f"- Analyst Target Price (Mean): ${target_mean:.2f}\n"

            if target_high and target_low:
                section += f"- Target Range: ${target_low:.2f} - ${target_high:.2f}\n"

            if upside_potential is not None:
                direction = "upside" if upside_potential > 0 else "downside"
                section += f"- Potential {direction.capitalize()}: {upside_potential:+.1f}%\n"

            if recommendation:
                section += f"- Recommendation: {recommendation.upper()}\n"

            if num_analysts:
                section += f"- Number of Analysts: {num_analysts}\n"

            sections.append(section)

        return "\n".join(sections)

    def _format_peer_valuation(self, peer_valuation: list) -> str:
        """Format peer valuation comparison for report."""
        if not peer_valuation:
            return "No peer valuation data available."

        sections = []
        for peer in peer_valuation:
            ticker = peer.get("ticker", "N/A")
            sector = peer.get("sector", "N/A")
            industry = peer.get("industry", "N/A")

            # Company's ratios
            pe_ratio = peer.get("pe_ratio")
            price_to_book = peer.get("price_to_book")
            price_to_sales = peer.get("price_to_sales")

            # Sector averages
            sector_avg_pe = peer.get("sector_avg_pe")
            sector_avg_pb = peer.get("sector_avg_pb")
            sector_avg_ps = peer.get("sector_avg_ps")

            # Premium/discount
            pe_premium_discount = peer.get("pe_premium_discount")
            pb_premium_discount = peer.get("pb_premium_discount")
            ps_premium_discount = peer.get("ps_premium_discount")

            peer_count = peer.get("peer_count", 0)

            section = f"**{ticker}** ({sector})\n"
            section += f"- Industry: {industry}\n"

            if pe_ratio and sector_avg_pe:
                section += f"- P/E Ratio: {pe_ratio:.2f} vs Sector Avg: {sector_avg_pe:.2f}"
                if pe_premium_discount is not None:
                    direction = "premium" if pe_premium_discount > 0 else "discount"
                    section += f" ({pe_premium_discount:+.1f}% {direction})"
                section += "\n"

            if price_to_book and sector_avg_pb:
                section += f"- Price/Book: {price_to_book:.2f} vs Sector Avg: {sector_avg_pb:.2f}"
                if pb_premium_discount is not None:
                    direction = "premium" if pb_premium_discount > 0 else "discount"
                    section += f" ({pb_premium_discount:+.1f}% {direction})"
                section += "\n"

            if price_to_sales and sector_avg_ps:
                section += f"- Price/Sales: {price_to_sales:.2f} vs Sector Avg: {sector_avg_ps:.2f}"
                if ps_premium_discount is not None:
                    direction = "premium" if ps_premium_discount > 0 else "discount"
                    section += f" ({ps_premium_discount:+.1f}% {direction})"
                section += "\n"

            if peer_count > 0:
                section += f"- Based on {peer_count} peer comparisons\n"

            sections.append(section)

        return "\n".join(sections)

    def _format_context(self, context: list) -> str:
        """Format retrieved context for report."""
        if not context:
            return "No additional context found."

        # Show top 3 most relevant contexts
        top_contexts = context[:3]

        sections = []
        for i, ctx in enumerate(top_contexts, 1):
            text = ctx.get("text", "")[:200]  # Truncate
            source = ctx.get("metadata", {}).get("source", "Unknown")
            ticker = ctx.get("metadata", {}).get("ticker", "N/A")

            section = f"{i}. **{ticker} - {source}**\n   {text}..."
            sections.append(section)

        return "\n\n".join(sections)

    async def _generate_snapshot(
        self,
        tickers: list,
        market_data: list,
        sentiment: list,
        analyst_consensus: list,
        peer_valuation: list
    ) -> dict:
        """
        Generate simplified investor snapshot for beginners.

        Args:
            tickers: List of tickers
            market_data: Market data from MarketDataAgent
            sentiment: Sentiment analysis from SentimentAgent
            analyst_consensus: Analyst consensus from ForwardLookingAgent
            peer_valuation: Peer valuation comparison from MarketDataAgent

        Returns:
            InvestorSnapshot dict or None if not enough data
        """
        # Need at least one ticker and market data
        if not tickers or not market_data:
            self.logger.warning("Insufficient data to generate snapshot")
            return None

        # Use first ticker (primary analysis target)
        ticker = tickers[0]
        primary_market_data = next((m for m in market_data if m.get("ticker") == ticker), None)

        if not primary_market_data:
            return None

        # Extract core metrics
        current_price = primary_market_data.get("current_price")
        price_change_pct = primary_market_data.get("change_percent")
        market_cap = primary_market_data.get("market_cap")
        pe_ratio = primary_market_data.get("pe_ratio")

        # Format data for LLM
        pe_str = f"{pe_ratio:.2f}" if pe_ratio else "N/A"
        market_summary = f"""
Ticker: {ticker}
Current Price: ${current_price:.2f}
Price Change: {price_change_pct:+.2f}%
Market Cap: ${market_cap / 1e9:.2f}B
P/E Ratio: {pe_str}
"""

        # Add sentiment if available
        primary_sentiment = next((s for s in sentiment if s.get("ticker") == ticker), None) if sentiment else None
        sentiment_summary = ""
        if primary_sentiment:
            sentiment_summary = f"\nSentiment: {primary_sentiment.get('overall_sentiment', 'neutral').upper()} ({primary_sentiment.get('confidence', 0):.0%} confidence)"

        # Add analyst consensus if available
        primary_consensus = next((a for a in analyst_consensus if a.get("ticker") == ticker), None) if analyst_consensus else None
        analyst_summary = ""
        if primary_consensus:
            target = primary_consensus.get("target_price_mean")
            upside = primary_consensus.get("upside_potential")
            rec = primary_consensus.get("recommendation", "hold")
            if target:
                analyst_summary = f"\nAnalyst Target: ${target:.2f} ({upside:+.1f}% potential)\nRecommendation: {rec.upper()}"

        # Create prompt for snapshot generation
        prompt = f"""Based on this investment data for {ticker}, generate a beginner-friendly snapshot in JSON format:

{market_summary}{sentiment_summary}{analyst_summary}

Generate ONLY a valid JSON object with this exact structure:
{{
  "ticker": "{ticker}",
  "current_price": {current_price},
  "price_change_pct": {price_change_pct},
  "market_cap": {market_cap},
  "pe_ratio": {pe_ratio if pe_ratio else 'null'},
  "investment_rating": "one of: strong_buy, buy, hold, sell, strong_sell",
  "rating_explanation": "1-2 sentence explanation in simple terms",
  "key_highlights": ["highlight 1", "highlight 2", "highlight 3"],
  "risk_warnings": ["risk 1", "risk 2"]
}}

Guidelines:
- investment_rating: Based on price momentum, valuation, sentiment, and analyst views
- rating_explanation: WHY this rating in simple language
- key_highlights: 3-5 positive facts (growth, strengths, opportunities)
- risk_warnings: 2-3 main risks (valuation concerns, market risks, business challenges)
- Use simple language for beginners, avoid jargon
- Be objective and balanced

Return ONLY the JSON object, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial advisor helping beginner investors. Generate clear, simple snapshots in JSON format. Be concise and avoid technical jargon."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            import json
            snapshot_data = json.loads(response.choices[0].message.content.strip())

            self.logger.info(f"✅ Snapshot generated successfully for {ticker}")
            return snapshot_data

        except Exception as e:
            self.logger.error(f"Failed to generate snapshot: {str(e)}")
            return None

    def _generate_fallback_report(
        self,
        query: str,
        tickers: list,
        market_data: list,
        sentiment: list
    ) -> str:
        """Generate simple fallback report if LLM fails."""
        report = f"# Investment Research Report\n\n"
        report += f"**Query:** {query}\n\n"

        if tickers:
            report += f"**Tickers:** {', '.join(tickers)}\n\n"

        if market_data:
            report += "## Market Data\n\n"
            report += self._format_market_data(market_data)
            report += "\n\n"

        if sentiment:
            report += "## Sentiment Analysis\n\n"
            report += self._format_sentiment(sentiment)
            report += "\n\n"

        report += "---\n*Note: Full report generation temporarily unavailable. This is a summary view.*"

        return report


# Singleton instance
report_agent = ReportAgent()
