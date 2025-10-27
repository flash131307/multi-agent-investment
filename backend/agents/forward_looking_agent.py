"""
Forward-Looking Agent - Fetches analyst consensus and price targets.
Provides forward-looking guidance for investment decisions.
"""
from typing import List

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState, AnalystConsensus
from backend.services.yahoo_finance import yahoo_finance


class ForwardLookingAgent(BaseAgent):
    """
    Fetches analyst consensus data:
    - Price targets (mean, high, low)
    - Analyst recommendations
    - Upside/downside potential
    """

    def __init__(self):
        super().__init__("forward_looking")
        self.yahoo = yahoo_finance

    async def execute(self, state: AgentState) -> AgentState:
        """
        Fetch analyst consensus for all tickers in state.

        Args:
            state: Current agent state

        Returns:
            State with analyst_consensus populated
        """
        tickers = state.get("tickers", [])

        if not tickers:
            self.logger.warning("No tickers to fetch analyst data for")
            return state

        # Fetch analyst data for each ticker
        analyst_data_list = []

        for ticker in tickers:
            self.logger.info(f"Fetching analyst consensus for {ticker}")

            try:
                data = self._fetch_analyst_data(ticker)
                if data:
                    analyst_data_list.append(data)
            except Exception as e:
                self.logger.error(f"Failed to fetch analyst data for {ticker}: {e}")
                # Continue with other tickers

        # Return only the fields we're updating (for parallel execution)
        return {
            "analyst_consensus": analyst_data_list
        }

    def _fetch_analyst_data(self, ticker: str) -> AnalystConsensus:
        """
        Fetch analyst consensus for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AnalystConsensus dict or None
        """
        # Get analyst recommendations from Yahoo Finance
        analyst_data = self.yahoo.get_analyst_recommendations(ticker)

        if not analyst_data:
            self.logger.warning(f"No analyst data available for {ticker}")
            return None

        # Extract key fields
        target_mean = analyst_data.get("target_price_mean")
        target_high = analyst_data.get("target_price_high")
        target_low = analyst_data.get("target_price_low")
        current_price = analyst_data.get("current_price")
        upside_potential = analyst_data.get("upside_potential")
        recommendation = analyst_data.get("recommendation")
        num_analysts = analyst_data.get("num_analysts")

        # Create AnalystConsensus object
        consensus = AnalystConsensus(
            ticker=ticker,
            target_price_mean=target_mean,
            target_price_high=target_high,
            target_price_low=target_low,
            current_price=current_price,
            upside_potential=upside_potential,
            recommendation=recommendation,
            num_analysts=num_analysts
        )

        # Log summary
        if upside_potential is not None and target_mean:
            self.logger.info(
                f"✅ {ticker}: Target ${target_mean:.2f} "
                f"({upside_potential:+.1f}% upside) | "
                f"Recommendation: {recommendation or 'N/A'} "
                f"({num_analysts or 0} analysts)"
            )
        else:
            self.logger.info(f"✅ {ticker}: Limited analyst data available")

        return consensus


# Singleton instance
forward_looking_agent = ForwardLookingAgent()
