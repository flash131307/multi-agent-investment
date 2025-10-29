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
            State with final report and metadata
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
        executed_agents = state.get("executed_agents", [])

        self.logger.info(f"Generating report for query: {user_query[:50]}...")
        self.logger.info(f"Intent: {intent}, Executed agents: {executed_agents}")

        # Determine which template to use based on intent
        template = self._select_template(intent)

        # Build metadata about data availability
        data_sources = {
            "market_data": bool(market_data),
            "sentiment": bool(sentiment),
            "analyst_consensus": bool(analyst_consensus),
            "peer_valuation": bool(peer_valuation),
            "context": bool(context)
        }

        # Generate report based on available data and template
        report = await self._generate_report(
            user_query=user_query,
            tickers=tickers,
            intent=intent,
            template=template,
            market_data=market_data,
            sentiment=sentiment,
            analyst_consensus=analyst_consensus,
            peer_valuation=peer_valuation,
            context=context,
            data_sources=data_sources
        )

        # Generate snapshot for beginner investors
        snapshot = await self._generate_snapshot(
            tickers=tickers,
            market_data=market_data,
            sentiment=sentiment,
            analyst_consensus=analyst_consensus,
            peer_valuation=peer_valuation
        )

        # Build report metadata
        report_metadata = {
            "executed_agents": executed_agents,
            "data_sources": data_sources,
            "intent": intent,
            "tickers": tickers,
            "report_template": template
        }

        # Return report, snapshot, and metadata
        return {
            "report": report,
            "snapshot": snapshot,
            "report_metadata": report_metadata
        }

    def _select_template(self, intent: str) -> str:
        """
        Select report template based on query intent.

        Args:
            intent: Query intent from router

        Returns:
            Template name
        """
        template_map = {
            "price_query": "brief_market",
            "sentiment_analysis": "sentiment_focused",
            "comparison": "peer_comparison",
            "fundamental_analysis": "comprehensive",
            "general_research": "comprehensive"
        }

        template = template_map.get(intent, "comprehensive")
        self.logger.info(f"Selected template: {template} for intent: {intent}")
        return template

    async def _generate_report(
        self,
        user_query: str,
        tickers: list,
        intent: str,
        template: str,
        market_data: list,
        sentiment: list,
        analyst_consensus: list,
        peer_valuation: list,
        context: list,
        data_sources: dict
    ) -> str:
        """
        Generate structured report using LLM with dynamic template.

        Args:
            user_query: Original user query
            tickers: List of tickers
            intent: Query intent
            template: Report template to use
            market_data: Market data from MarketDataAgent
            sentiment: Sentiment analysis from SentimentAgent
            analyst_consensus: Analyst consensus from ForwardLookingAgent
            peer_valuation: Peer valuation comparison from MarketDataAgent
            context: Retrieved documents from RAG
            data_sources: Dict of data availability

        Returns:
            Formatted report string
        """
        # Build dynamic sections based on template and data availability
        sections = self._build_sections(
            template=template,
            data_sources=data_sources,
            market_data=market_data,
            sentiment=sentiment,
            analyst_consensus=analyst_consensus,
            peer_valuation=peer_valuation,
            context=context
        )

        # Create dynamic prompt based on template
        prompt = self._create_prompt(
            user_query=user_query,
            tickers=tickers,
            intent=intent,
            template=template,
            sections=sections
        )

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

    def _build_sections(
        self,
        template: str,
        data_sources: dict,
        market_data: list,
        sentiment: list,
        analyst_consensus: list,
        peer_valuation: list,
        context: list
    ) -> dict:
        """
        Build report sections based on template and data availability.

        Args:
            template: Report template name
            data_sources: Dict indicating which data is available
            market_data: Market data
            sentiment: Sentiment data
            analyst_consensus: Analyst consensus data
            peer_valuation: Peer valuation data
            context: Retrieved context

        Returns:
            Dict of section names and formatted content
        """
        sections = {}

        # Define which sections each template includes
        template_sections = {
            "brief_market": ["market", "52_week_trend"],
            "sentiment_focused": ["sentiment", "market"],
            "peer_comparison": ["market", "peer_valuation", "key_insights"],
            "comprehensive": ["market", "52_week_trend", "peer_valuation", "sentiment", "analyst", "context", "key_insights"]
        }

        # Get sections for this template
        template_layout = template_sections.get(template, template_sections["comprehensive"])

        # Build only the sections that are in the template AND have data
        if "market" in template_layout and data_sources.get("market_data"):
            sections["Market Analysis"] = self._format_market_data(market_data)

        if "52_week_trend" in template_layout and data_sources.get("market_data"):
            # 52-week trend is part of market data, but we highlight it separately for some templates
            sections["52-Week Trend Analysis"] = self._format_52_week_trend(market_data)

        if "peer_valuation" in template_layout and data_sources.get("peer_valuation"):
            sections["Peer Valuation Comparison"] = self._format_peer_valuation(peer_valuation)

        if "sentiment" in template_layout and data_sources.get("sentiment"):
            sections["Sentiment & News"] = self._format_sentiment(sentiment)

        if "analyst" in template_layout and data_sources.get("analyst_consensus"):
            sections["Analyst Consensus & Forward-Looking"] = self._format_analyst_consensus(analyst_consensus)

        if "context" in template_layout and data_sources.get("context"):
            sections["Supporting Context"] = self._format_context(context)

        # Key insights is always included if we have any data
        if "key_insights" in template_layout:
            sections["Key Insights"] = "(To be generated by LLM based on available data)"

        return sections

    def _create_prompt(
        self,
        user_query: str,
        tickers: list,
        intent: str,
        template: str,
        sections: dict
    ) -> str:
        """
        Create dynamic prompt based on template and available sections.

        Args:
            user_query: User's query
            tickers: List of tickers
            intent: Query intent
            template: Template name
            sections: Dict of section names and content

        Returns:
            Formatted prompt string
        """
        # Build data sections
        data_section = ""
        for section_name, content in sections.items():
            if section_name != "Key Insights":  # Skip placeholder
                data_section += f"\n---\n\n**{section_name}:**\n{content}\n"

        # Build required sections list
        section_names = list(sections.keys())

        # Template-specific instructions
        template_instructions = {
            "brief_market": """
Provide a BRIEF market summary (3-4 sentences) covering:
- Current price and change
- 52-week position and what it indicates
- Quick valuation assessment""",

            "sentiment_focused": """
Provide a sentiment-focused analysis with:
1. **Executive Summary** (2-3 sentences, sentiment-driven)
2. **Sentiment Analysis** (detailed news themes and sentiment breakdown)
3. **Market Context** (brief price overview to support sentiment)
4. **Conclusion** (investment perspective based primarily on sentiment)""",

            "peer_comparison": """
Provide a peer comparison analysis with:
1. **Executive Summary** (2-3 sentences)
2. **Market Overview** (current price and basics)
3. **Peer Valuation Comparison** (detailed comparison with sector)
4. **Key Insights** (3-5 bullet points on valuation positioning)
5. **Conclusion** (investment perspective based on relative valuation)""",

            "comprehensive": """
Provide a comprehensive investment research report with:
1. **Executive Summary** (2-3 sentences)
2. Then cover each available section in detail
3. **Key Insights** (3-5 bullet points synthesizing all data)
4. **Conclusion** (balanced investment perspective)"""
        }

        instruction = template_instructions.get(template, template_instructions["comprehensive"])

        # Build prompt
        prompt = f"""Generate an investment research report to answer this query:

**User Query:** {user_query}

**Tickers:** {', '.join(tickers) if tickers else 'Not specified'}
**Intent:** {intent}
{data_section}

---

{instruction}

**IMPORTANT INSTRUCTIONS:**
- Generate ONLY sections based on the available data above
- Available sections: {', '.join(section_names)}
- DO NOT hallucinate or make up information for unavailable data
- Use clear markdown formatting
- Be objective and data-driven
- RESPOND IN THE SAME LANGUAGE AS THE USER'S QUERY (Chinese query = Chinese response, English query = English response)

**Analysis Guidelines:**
- 52-week trends: Stocks near highs (80%+) = strong momentum or resistance. Near lows (20%-) = weakness or potential value
- Peer valuation: Premium (positive %) = market confidence or overvaluation. Discount (negative %) = undervaluation or concerns
"""

        return prompt

    def _format_52_week_trend(self, market_data: list) -> str:
        """Format 52-week trend analysis specifically."""
        if not market_data:
            return "No market data available."

        sections = []
        for data in market_data:
            ticker = data.get("ticker", "N/A")
            week_52_high = data.get("year_high")
            week_52_low = data.get("year_low")
            week_52_position = data.get("week_52_position")
            distance_from_high = data.get("distance_from_high")
            distance_from_low = data.get("distance_from_low")
            trend_signal = data.get("trend_signal")
            current_price = data.get("current_price")

            if not (week_52_high and week_52_low and week_52_position is not None):
                continue

            section = f"**{ticker}**\n"
            section += f"- Current Price: ${current_price:.2f}\n" if current_price else ""
            section += f"- 52-Week Range: ${week_52_low:.2f} - ${week_52_high:.2f}\n"
            section += f"- Position in Range: {week_52_position:.1f}%"

            if trend_signal == "near_high":
                section += " (Trading near 52-week high - strong momentum or potential resistance)"
            elif trend_signal == "near_low":
                section += " (Trading near 52-week low - potential value or concern)"
            else:
                section += " (Mid-range - balanced positioning)"
            section += "\n"

            if distance_from_high is not None:
                section += f"- Distance from 52W High: {distance_from_high:+.1f}%\n"
            if distance_from_low is not None:
                section += f"- Distance from 52W Low: {distance_from_low:+.1f}%\n"

            sections.append(section)

        return "\n".join(sections) if sections else "52-week trend data not available."


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
