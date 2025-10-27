"""
Market Data Agent - Fetches current market data and fundamentals.
Uses Yahoo Finance for real-time stock information.
"""
from typing import List

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState, MarketData, PeerValuation
from backend.services.yahoo_finance import yahoo_finance


class MarketDataAgent(BaseAgent):
    """
    Fetches market data for requested tickers:
    - Current price and change %
    - Volume and market cap
    - Key ratios (P/E, etc.)
    - Day/year high/low
    """

    def __init__(self):
        super().__init__("market_data")
        self.yahoo = yahoo_finance

    async def execute(self, state: AgentState) -> AgentState:
        """
        Fetch market data and peer valuation for all tickers in state.

        Args:
            state: Current agent state

        Returns:
            State with market_data and peer_valuation populated
        """
        tickers = state.get("tickers", [])

        if not tickers:
            self.logger.warning("No tickers to fetch market data for")
            return state

        # Fetch data for each ticker
        market_data_list = []
        peer_valuation_list = []

        for ticker in tickers:
            self.logger.info(f"Fetching market data for {ticker}")

            try:
                # Fetch market data
                data = self._fetch_ticker_data(ticker)
                if data:
                    market_data_list.append(data)

                # Fetch peer valuation comparison
                peer_data = self._fetch_peer_valuation(ticker)
                if peer_data:
                    peer_valuation_list.append(peer_data)

            except Exception as e:
                self.logger.error(f"Failed to fetch data for {ticker}: {e}")
                # Continue with other tickers

        # Return only the fields we're updating (for parallel execution)
        # Always return a list (empty or with data) for Annotated[List, operator.add]
        return {
            "market_data": market_data_list,
            "peer_valuation": peer_valuation_list
        }

    def _fetch_ticker_data(self, ticker: str) -> MarketData:
        """
        Fetch comprehensive market data for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            MarketData dict
        """
        # Get stock info from Yahoo Finance
        stock_info = self.yahoo.get_stock_info(ticker)

        if not stock_info:
            self.logger.warning(f"No data available for {ticker}")
            return None

        # Extract key fields
        current_price = stock_info.get("current_price")

        # Calculate change %
        day_high = stock_info.get("52_week_high")
        day_low = stock_info.get("52_week_low")

        change_percent = None
        if current_price and day_low and day_low > 0:
            # Simple approximation (ideally would use previous close)
            change_percent = ((current_price - day_low) / day_low) * 100

        # Calculate 52-week trend metrics
        week_52_high = stock_info.get("52_week_high")
        week_52_low = stock_info.get("52_week_low")

        week_52_position = None
        distance_from_high = None
        distance_from_low = None
        trend_signal = None

        if current_price and week_52_high and week_52_low and week_52_high > week_52_low:
            # Position in 52-week range (0% = at low, 100% = at high)
            week_52_position = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100

            # Distance from high (negative % indicates below high)
            distance_from_high = ((current_price - week_52_high) / week_52_high) * 100

            # Distance from low (positive % indicates above low)
            distance_from_low = ((current_price - week_52_low) / week_52_low) * 100

            # Trend signal based on position
            if week_52_position >= 80:
                trend_signal = "near_high"
            elif week_52_position <= 20:
                trend_signal = "near_low"
            else:
                trend_signal = "mid_range"

        # Create MarketData object
        market_data = MarketData(
            ticker=ticker,
            current_price=current_price,
            change_percent=round(change_percent, 2) if change_percent else None,
            volume=stock_info.get("volume"),
            market_cap=stock_info.get("market_cap"),
            pe_ratio=stock_info.get("pe_ratio"),
            day_high=stock_info.get("52_week_high"),  # Using year high as proxy
            day_low=stock_info.get("52_week_low"),    # Using year low as proxy
            year_high=week_52_high,
            year_low=week_52_low,
            # 52-week trend analysis
            week_52_position=round(week_52_position, 1) if week_52_position else None,
            distance_from_high=round(distance_from_high, 1) if distance_from_high else None,
            distance_from_low=round(distance_from_low, 1) if distance_from_low else None,
            trend_signal=trend_signal
        )

        self.logger.info(
            f"✅ {ticker}: ${current_price} "
            f"(MC: ${market_data['market_cap']:,})" if market_data['market_cap'] else ""
        )

        return market_data

    def _fetch_peer_valuation(self, ticker: str) -> PeerValuation:
        """
        Fetch peer valuation comparison for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            PeerValuation dict
        """
        # Get peer valuation from Yahoo Finance
        peer_data = self.yahoo.get_peer_valuation_comparison(ticker)

        if not peer_data:
            self.logger.warning(f"No peer valuation data available for {ticker}")
            return None

        # Convert to PeerValuation TypedDict
        peer_valuation = PeerValuation(
            ticker=peer_data.get("ticker"),
            sector=peer_data.get("sector"),
            industry=peer_data.get("industry"),
            pe_ratio=peer_data.get("pe_ratio"),
            price_to_book=peer_data.get("price_to_book"),
            price_to_sales=peer_data.get("price_to_sales"),
            sector_avg_pe=peer_data.get("sector_avg_pe"),
            sector_avg_pb=peer_data.get("sector_avg_pb"),
            sector_avg_ps=peer_data.get("sector_avg_ps"),
            pe_premium_discount=peer_data.get("pe_premium_discount"),
            pb_premium_discount=peer_data.get("pb_premium_discount"),
            ps_premium_discount=peer_data.get("ps_premium_discount"),
            peer_count=peer_data.get("peer_count", 0)
        )

        self.logger.info(
            f"✅ {ticker}: Peer comparison vs {peer_valuation['sector']} "
            f"(P/E: {peer_valuation['pe_premium_discount']:+.1f}% sector avg)"
            if peer_valuation['pe_premium_discount'] else ""
        )

        return peer_valuation


# Singleton instance
market_data_agent = MarketDataAgent()
