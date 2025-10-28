"""
Visualization Agent - Prepares structured data for frontend charts.
Fetches historical price data and formats it for visualization components.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState, VisualizationData, PricePoint
from backend.services.yahoo_finance import yahoo_finance


class VisualizationAgent(BaseAgent):
    """
    Prepares data for interactive visualizations:
    - Historical price charts (1 year daily data)
    - 52-week range indicators
    - Peer comparison charts
    """

    def __init__(self):
        super().__init__("visualization")
        self.yahoo = yahoo_finance

    async def execute(self, state: AgentState) -> AgentState:
        """
        Fetch and structure visualization data for all tickers.

        Args:
            state: Current agent state

        Returns:
            State with visualization_data populated
        """
        tickers = state.get("tickers", [])

        if not tickers:
            self.logger.warning("No tickers to generate visualization data for")
            return state

        # Generate visualization data for each ticker
        viz_data_list = []

        for ticker in tickers:
            self.logger.info(f"Generating visualization data for {ticker}")

            try:
                viz_data = await self._generate_viz_data(ticker, state)
                if viz_data:
                    viz_data_list.append(viz_data)

            except Exception as e:
                self.logger.error(f"Failed to generate viz data for {ticker}: {e}")
                # Continue with other tickers

        # Return only the field we're updating (for parallel execution)
        return {
            "visualization_data": viz_data_list
        }

    async def _generate_viz_data(
        self,
        ticker: str,
        state: AgentState
    ) -> Optional[VisualizationData]:
        """
        Generate comprehensive visualization data for a single ticker.

        Args:
            ticker: Stock ticker symbol
            state: Current state (for accessing market_data and peer_valuation)

        Returns:
            VisualizationData dict or None if error
        """
        # 1. Fetch historical price data (1 year, daily interval)
        historical_data = self.yahoo.get_historical_data(
            ticker=ticker,
            period="1y",
            interval="1d"
        )

        if not historical_data:
            self.logger.warning(f"No historical data available for {ticker}")
            return None

        # 2. Convert historical data to price points
        price_history = self._format_price_history(historical_data)

        # 3. Extract market data for current price and 52-week stats
        market_data = self._find_market_data(ticker, state)

        current_price = None
        week_52_high = None
        week_52_low = None
        current_position_pct = None

        if market_data:
            current_price = market_data.get("current_price")
            week_52_high = market_data.get("year_high")
            week_52_low = market_data.get("year_low")
            current_position_pct = market_data.get("week_52_position")

        # 4. Extract peer comparison data
        peer_comparison = self._format_peer_comparison(ticker, state)

        # 5. Calculate summary statistics from historical data
        summary = historical_data.get("summary", {})

        viz_data = VisualizationData(
            ticker=ticker,
            price_history=price_history,
            week_52_high=week_52_high,
            week_52_low=week_52_low,
            current_price=current_price,
            current_position_pct=current_position_pct,
            peer_comparison=peer_comparison,
            period_high=summary.get("highest"),
            period_low=summary.get("lowest"),
            average_volume=summary.get("average_volume")
        )

        self.logger.info(
            f"✅ Generated viz data for {ticker}: "
            f"{len(price_history)} price points, {len(peer_comparison)} peers"
        )

        return viz_data

    def _format_price_history(self, historical_data: Dict) -> List[PricePoint]:
        """
        Convert Yahoo Finance historical data to price points.

        Args:
            historical_data: Raw data from yahoo_finance.get_historical_data()

        Returns:
            List of PricePoint dicts
        """
        raw_data = historical_data.get("data", {})
        price_points = []

        for date_key, values in raw_data.items():
            try:
                # date_key is a pandas Timestamp or datetime string
                if isinstance(date_key, str):
                    date_str = date_key
                else:
                    # Convert to ISO format string
                    date_str = date_key.isoformat() if hasattr(date_key, 'isoformat') else str(date_key)

                price_point = PricePoint(
                    date=date_str,
                    open=float(values.get("Open", 0)),
                    high=float(values.get("High", 0)),
                    low=float(values.get("Low", 0)),
                    close=float(values.get("Close", 0)),
                    volume=int(values.get("Volume", 0))
                )
                price_points.append(price_point)

            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid price point: {e}")
                continue

        # Sort by date (oldest first)
        price_points.sort(key=lambda x: x["date"])

        return price_points

    def _find_market_data(self, ticker: str, state: AgentState) -> Optional[Dict]:
        """
        Find market data for a specific ticker from state.

        Args:
            ticker: Stock ticker
            state: Current state

        Returns:
            MarketData dict or None
        """
        market_data_list = state.get("market_data", [])

        for data in market_data_list:
            if data.get("ticker") == ticker:
                return data

        return None

    def _format_peer_comparison(
        self,
        ticker: str,
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        Format peer valuation data for comparison charts.

        Args:
            ticker: Stock ticker
            state: Current state

        Returns:
            List of peer comparison dicts
        """
        peer_data_list = state.get("peer_valuation", [])
        market_data_list = state.get("market_data", [])

        # Find peer valuation for this ticker
        peer_valuation = None
        for peer in peer_data_list:
            if peer.get("ticker") == ticker:
                peer_valuation = peer
                break

        if not peer_valuation:
            return []

        # Create comparison data: [main ticker, sector average, selected peers]
        comparison = []

        # 1. Main ticker data
        ticker_data = {
            "ticker": ticker,
            "name": ticker,  # Could be enhanced with company name
            "pe_ratio": peer_valuation.get("pe_ratio"),
            "pb_ratio": peer_valuation.get("price_to_book"),
            "ps_ratio": peer_valuation.get("price_to_sales"),
            "is_main": True
        }
        comparison.append(ticker_data)

        # 2. Sector average (as a comparison point)
        sector_name = peer_valuation.get("sector", "Sector")
        sector_avg = {
            "ticker": f"{sector_name[:10]} Avg",
            "name": f"{sector_name} Average",
            "pe_ratio": peer_valuation.get("sector_avg_pe"),
            "pb_ratio": peer_valuation.get("sector_avg_pb"),
            "ps_ratio": peer_valuation.get("sector_avg_ps"),
            "is_main": False
        }
        comparison.append(sector_avg)

        # 3. TODO: Add actual peer tickers (for now just show sector avg)
        # In future enhancement, fetch peer tickers from same sector

        return comparison


# Singleton instance
visualization_agent = VisualizationAgent()
