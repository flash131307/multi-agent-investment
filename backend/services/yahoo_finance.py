"""
Yahoo Finance API integration for stock data.
Uses yfinance library for free access to market data.
"""
import yfinance as yf
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import asyncio
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Service for fetching stock data from Yahoo Finance with async support and caching."""

    def __init__(self):
        """Initialize service with simple memory cache."""
        # Simple memory cache: {cache_key: (data, timestamp)}
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 minutes TTL

    def _get_cache_key(self, method: str, ticker: str, **kwargs) -> str:
        """Generate cache key for method + ticker + params."""
        params_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{method}:{ticker}:{params_str}" if params_str else f"{method}:{ticker}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if not expired."""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"📦 Cache hit: {cache_key}")
                return data
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                logger.debug(f"🗑️  Cache expired: {cache_key}")
        return None

    def _set_cache(self, cache_key: str, data: Optional[Dict]):
        """Store data in cache with timestamp."""
        if data is not None:
            self._cache[cache_key] = (data, time.time())
            logger.debug(f"💾 Cache set: {cache_key}")

    # ========== SYNC METHODS (Original) ==========

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        Get comprehensive stock information.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with stock info or None if error
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract key information
            stock_data = {
                "ticker": ticker.upper(),
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "previous_close": info.get("previousClose", info.get("regularMarketPreviousClose")),
                "regular_market_change_percent": info.get("regularMarketChangePercent"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume"),
                "avg_volume": info.get("averageVolume"),
                "description": info.get("longBusinessSummary", ""),
                "employees": info.get("fullTimeEmployees"),
                "website": info.get("website"),
                "updated_at": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Fetched stock info for {ticker}")
            return stock_data

        except Exception as e:
            logger.error(f"❌ Failed to fetch stock info for {ticker}: {e}")
            return None

    def get_historical_data(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Optional[Dict]:
        """
        Get historical price data.

        Args:
            ticker: Stock ticker
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            Dict with historical data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"No historical data found for {ticker}")
                return None

            # Convert DataFrame to dict
            hist_data = {
                "ticker": ticker.upper(),
                "period": period,
                "interval": interval,
                "data": hist.to_dict('index'),  # Index by date
                "summary": {
                    "latest_close": float(hist['Close'].iloc[-1]),
                    "latest_date": hist.index[-1].isoformat(),
                    "highest": float(hist['High'].max()),
                    "lowest": float(hist['Low'].min()),
                    "average_volume": int(hist['Volume'].mean())
                }
            }

            logger.info(f"✅ Fetched {len(hist)} historical data points for {ticker}")
            return hist_data

        except Exception as e:
            logger.error(f"❌ Failed to fetch historical data for {ticker}: {e}")
            return None

    def get_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get fundamental financial data.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with fundamental data
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            fundamentals = {
                "ticker": ticker.upper(),
                "valuation": {
                    "market_cap": info.get("marketCap"),
                    "enterprise_value": info.get("enterpriseValue"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "price_to_book": info.get("priceToBook"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months")
                },
                "profitability": {
                    "profit_margin": info.get("profitMargins"),
                    "operating_margin": info.get("operatingMargins"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "return_on_equity": info.get("returnOnEquity")
                },
                "financial_health": {
                    "total_cash": info.get("totalCash"),
                    "total_debt": info.get("totalDebt"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "current_ratio": info.get("currentRatio"),
                    "quick_ratio": info.get("quickRatio")
                },
                "growth": {
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "revenue": info.get("totalRevenue"),
                    "gross_profit": info.get("grossProfits")
                }
            }

            logger.info(f"✅ Fetched fundamentals for {ticker}")
            return fundamentals

        except Exception as e:
            logger.error(f"❌ Failed to fetch fundamentals for {ticker}: {e}")
            return None

    def get_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """
        Get recent news for a stock.

        Args:
            ticker: Stock ticker
            limit: Maximum number of news items

        Returns:
            List of news dicts
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news[:limit]

            news_items = []
            for item in news:
                # New yfinance API structure: data is nested in 'content'
                content = item.get("content", {})

                # Get publish time (now in ISO format, not timestamp)
                publish_time = content.get("pubDate") or content.get("displayTime")
                if not publish_time:
                    publish_time = datetime.utcnow().isoformat()

                # Get thumbnail URL
                thumbnail_url = None
                thumbnail_data = content.get("thumbnail", {})
                if thumbnail_data and thumbnail_data.get("resolutions"):
                    # Get the original or first available resolution
                    thumbnail_url = thumbnail_data["resolutions"][0].get("url")

                # Get provider info
                provider = content.get("provider", {})
                publisher = provider.get("displayName")

                # Get canonical URL
                canonical = content.get("canonicalUrl", {})
                link = canonical.get("url") or content.get("clickThroughUrl", {}).get("url")

                news_items.append({
                    "ticker": ticker.upper(),
                    "title": content.get("title"),
                    "publisher": publisher,
                    "link": link,
                    "publish_time": publish_time,
                    "type": content.get("contentType"),
                    "summary": content.get("summary"),
                    "thumbnail": thumbnail_url
                })

            logger.info(f"✅ Fetched {len(news_items)} news items for {ticker}")
            return news_items

        except Exception as e:
            logger.error(f"❌ Failed to fetch news for {ticker}: {e}")
            return []

    def get_analyst_recommendations(self, ticker: str) -> Optional[Dict]:
        """
        Get analyst recommendations and price targets.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with analyst consensus data or None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get analyst price targets
            target_mean = info.get("targetMeanPrice")
            target_high = info.get("targetHighPrice")
            target_low = info.get("targetLowPrice")
            current_price = info.get("currentPrice", info.get("regularMarketPrice"))

            # Get recommendation
            recommendation_key = info.get("recommendationKey")  # "buy", "hold", "sell", etc.
            num_analysts = info.get("numberOfAnalystOpinions")

            # Calculate upside potential
            upside_potential = None
            if target_mean and current_price and current_price > 0:
                upside_potential = ((target_mean - current_price) / current_price) * 100

            analyst_data = {
                "ticker": ticker.upper(),
                "target_price_mean": target_mean,
                "target_price_high": target_high,
                "target_price_low": target_low,
                "current_price": current_price,
                "upside_potential": round(upside_potential, 2) if upside_potential else None,
                "recommendation": recommendation_key,
                "num_analysts": num_analysts
            }

            logger.info(f"✅ Fetched analyst recommendations for {ticker}")
            return analyst_data

        except Exception as e:
            logger.error(f"❌ Failed to fetch analyst recommendations for {ticker}: {e}")
            return None

    def get_peer_valuation_comparison(self, ticker: str) -> Optional[Dict]:
        """
        Get peer valuation comparison with sector averages.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with peer valuation comparison or None
        """
        # Predefined peer groups for major sectors
        SECTOR_PEERS = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "ORCL", "CRM", "ADBE"],
            "Consumer Cyclical": ["AMZN", "TSLA", "NKE", "HD", "MCD", "SBUX", "TGT", "LOW", "F", "GM"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "LLY", "DHR", "CVS", "AMGN"],
            "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB"],
            "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "CMCSA", "T", "VZ", "TMUS", "CHTR"],
            "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "CL", "MDLZ", "KHC"],
            "Industrials": ["BA", "HON", "UNP", "UPS", "CAT", "RTX", "LMT", "DE", "GE", "MMM"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY", "HAL"],
            "Basic Materials": ["LIN", "APD", "ECL", "SHW", "DD", "NEM", "FCX", "NUE", "DOW", "ALB"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL", "DLR", "AVB"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "ED", "PEG"]
        }

        try:
            # Get company info
            stock = yf.Ticker(ticker)
            info = stock.info

            sector = info.get("sector")
            industry = info.get("industry")

            # Get company's valuation ratios
            pe_ratio = info.get("trailingPE")
            price_to_book = info.get("priceToBook")
            price_to_sales = info.get("priceToSalesTrailing12Months")

            if not sector:
                logger.warning(f"No sector information for {ticker}")
                return None

            # Get peer list for the sector
            peer_list = SECTOR_PEERS.get(sector, [])

            # Remove the ticker itself from peer list
            peer_list = [p for p in peer_list if p.upper() != ticker.upper()]

            if not peer_list:
                logger.warning(f"No predefined peers for sector: {sector}")
                # Use a smaller set of general market peers
                peer_list = ["SPY"]  # S&P 500 ETF as fallback

            # Fetch peer data (limit to 5 peers to avoid rate limiting)
            peer_pe_ratios = []
            peer_pb_ratios = []
            peer_ps_ratios = []

            for peer_ticker in peer_list[:5]:
                try:
                    peer_stock = yf.Ticker(peer_ticker)
                    peer_info = peer_stock.info

                    peer_pe = peer_info.get("trailingPE")
                    peer_pb = peer_info.get("priceToBook")
                    peer_ps = peer_info.get("priceToSalesTrailing12Months")

                    if peer_pe:
                        peer_pe_ratios.append(peer_pe)
                    if peer_pb:
                        peer_pb_ratios.append(peer_pb)
                    if peer_ps:
                        peer_ps_ratios.append(peer_ps)

                except Exception as e:
                    logger.debug(f"Failed to fetch peer data for {peer_ticker}: {e}")
                    continue

            # Calculate sector averages
            sector_avg_pe = sum(peer_pe_ratios) / len(peer_pe_ratios) if peer_pe_ratios else None
            sector_avg_pb = sum(peer_pb_ratios) / len(peer_pb_ratios) if peer_pb_ratios else None
            sector_avg_ps = sum(peer_ps_ratios) / len(peer_ps_ratios) if peer_ps_ratios else None

            # Calculate premium/discount
            pe_premium_discount = None
            if pe_ratio and sector_avg_pe and sector_avg_pe > 0:
                pe_premium_discount = ((pe_ratio - sector_avg_pe) / sector_avg_pe) * 100

            pb_premium_discount = None
            if price_to_book and sector_avg_pb and sector_avg_pb > 0:
                pb_premium_discount = ((price_to_book - sector_avg_pb) / sector_avg_pb) * 100

            ps_premium_discount = None
            if price_to_sales and sector_avg_ps and sector_avg_ps > 0:
                ps_premium_discount = ((price_to_sales - sector_avg_ps) / sector_avg_ps) * 100

            peer_valuation = {
                "ticker": ticker.upper(),
                "sector": sector,
                "industry": industry,
                # Company's valuation ratios
                "pe_ratio": pe_ratio,
                "price_to_book": price_to_book,
                "price_to_sales": price_to_sales,
                # Sector averages
                "sector_avg_pe": round(sector_avg_pe, 2) if sector_avg_pe else None,
                "sector_avg_pb": round(sector_avg_pb, 2) if sector_avg_pb else None,
                "sector_avg_ps": round(sector_avg_ps, 2) if sector_avg_ps else None,
                # Premium/discount
                "pe_premium_discount": round(pe_premium_discount, 1) if pe_premium_discount else None,
                "pb_premium_discount": round(pb_premium_discount, 1) if pb_premium_discount else None,
                "ps_premium_discount": round(ps_premium_discount, 1) if ps_premium_discount else None,
                # Metadata
                "peer_count": len(peer_pe_ratios)
            }

            logger.info(f"✅ Fetched peer valuation for {ticker} ({sector})")
            return peer_valuation

        except Exception as e:
            logger.error(f"❌ Failed to fetch peer valuation for {ticker}: {e}")
            return None

    def get_complete_analysis(self, ticker: str) -> Dict:
        """
        Get complete analysis data for a stock (info + fundamentals + news).

        Args:
            ticker: Stock ticker

        Returns:
            Dict with comprehensive stock data
        """
        logger.info(f"Fetching complete analysis for {ticker}")

        return {
            "ticker": ticker.upper(),
            "timestamp": datetime.utcnow().isoformat(),
            "stock_info": self.get_stock_info(ticker),
            "fundamentals": self.get_fundamentals(ticker),
            "historical_1mo": self.get_historical_data(ticker, period="1mo"),
            "news": self.get_news(ticker, limit=5)
        }

    def format_for_llm(self, analysis_data: Dict) -> str:
        """
        Format stock analysis data for LLM consumption.

        Args:
            analysis_data: Output from get_complete_analysis()

        Returns:
            Formatted string for LLM context
        """
        try:
            ticker = analysis_data.get("ticker", "UNKNOWN")
            stock_info = analysis_data.get("stock_info", {})
            fundamentals = analysis_data.get("fundamentals", {})
            historical = analysis_data.get("historical_1mo", {})

            text = f"Stock Analysis for {ticker}\n\n"

            # Basic Info
            if stock_info:
                text += f"Company: {stock_info.get('name')}\n"
                text += f"Sector: {stock_info.get('sector')} | Industry: {stock_info.get('industry')}\n"
                text += f"Current Price: ${stock_info.get('current_price', 'N/A')}\n"
                text += f"Market Cap: ${stock_info.get('market_cap', 'N/A'):,}\n"
                text += f"P/E Ratio: {stock_info.get('pe_ratio', 'N/A')}\n\n"

            # Fundamentals
            if fundamentals and fundamentals.get("valuation"):
                text += "Valuation Metrics:\n"
                val = fundamentals["valuation"]
                text += f"  - Forward P/E: {val.get('forward_pe', 'N/A')}\n"
                text += f"  - PEG Ratio: {val.get('peg_ratio', 'N/A')}\n"
                text += f"  - Price/Book: {val.get('price_to_book', 'N/A')}\n\n"

            # Recent Performance
            if historical and historical.get("summary"):
                summary = historical["summary"]
                text += f"Recent Performance (1 month):\n"
                text += f"  - Latest Close: ${summary.get('latest_close', 'N/A')}\n"
                text += f"  - 1M High: ${summary.get('highest', 'N/A')}\n"
                text += f"  - 1M Low: ${summary.get('lowest', 'N/A')}\n\n"

            # Description
            if stock_info and stock_info.get("description"):
                text += f"Business Description:\n{stock_info['description'][:500]}...\n"

            return text

        except Exception as e:
            logger.error(f"❌ Failed to format analysis data: {e}")
            return f"Error formatting analysis for {analysis_data.get('ticker', 'UNKNOWN')}"

    # ========== ASYNC METHODS (Performance Optimized) ==========

    async def get_stock_info_async(self, ticker: str) -> Optional[Dict]:
        """
        Async version of get_stock_info with caching.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with stock info or None if error
        """
        cache_key = self._get_cache_key("stock_info", ticker)

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Fetch data in thread pool (yfinance is synchronous)
        data = await asyncio.to_thread(self.get_stock_info, ticker)

        # Cache result
        self._set_cache(cache_key, data)

        return data

    async def get_analyst_recommendations_async(self, ticker: str) -> Optional[Dict]:
        """
        Async version of get_analyst_recommendations with caching.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with analyst consensus data or None
        """
        cache_key = self._get_cache_key("analyst_recommendations", ticker)

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Fetch data in thread pool
        data = await asyncio.to_thread(self.get_analyst_recommendations, ticker)

        # Cache result
        self._set_cache(cache_key, data)

        return data

    async def get_historical_data_async(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Optional[Dict]:
        """
        Async version of get_historical_data with caching.

        Args:
            ticker: Stock ticker
            period: Data period
            interval: Data interval

        Returns:
            Dict with historical data
        """
        cache_key = self._get_cache_key("historical_data", ticker, period=period, interval=interval)

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Fetch data in thread pool
        data = await asyncio.to_thread(self.get_historical_data, ticker, period, interval)

        # Cache result
        self._set_cache(cache_key, data)

        return data

    async def get_news_async(self, ticker: str, limit: int = 10) -> List[Dict]:
        """
        Async version of get_news with caching.

        Args:
            ticker: Stock ticker
            limit: Maximum number of news items

        Returns:
            List of news dicts
        """
        cache_key = self._get_cache_key("news", ticker, limit=limit)

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Fetch data in thread pool
        data = await asyncio.to_thread(self.get_news, ticker, limit)

        # Cache result (store as dict for consistency)
        if data:
            cache_data = {"items": data}
            self._set_cache(cache_key, cache_data)
            return data

        return []

    async def _fetch_peer_info_async(self, ticker: str) -> Optional[Dict]:
        """
        Fetch peer valuation info with error handling.

        Args:
            ticker: Peer ticker symbol

        Returns:
            Dict with pe, pb, ps ratios or None
        """
        try:
            peer_stock = yf.Ticker(ticker)
            peer_info = await asyncio.to_thread(lambda: peer_stock.info)

            return {
                "ticker": ticker,
                "pe": peer_info.get("trailingPE"),
                "pb": peer_info.get("priceToBook"),
                "ps": peer_info.get("priceToSalesTrailing12Months")
            }
        except Exception as e:
            logger.debug(f"Failed to fetch peer data for {ticker}: {e}")
            return None

    async def get_peer_valuation_comparison_async(self, ticker: str) -> Optional[Dict]:
        """
        Async version of get_peer_valuation_comparison with CONCURRENT peer fetching.

        This is the main performance optimization - fetches peers in parallel
        instead of sequentially.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with peer valuation comparison or None
        """
        cache_key = self._get_cache_key("peer_valuation", ticker)

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Predefined peer groups for major sectors
        SECTOR_PEERS = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "ORCL", "CRM", "ADBE"],
            "Consumer Cyclical": ["AMZN", "TSLA", "NKE", "HD", "MCD", "SBUX", "TGT", "LOW", "F", "GM"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "LLY", "DHR", "CVS", "AMGN"],
            "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB"],
            "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "CMCSA", "T", "VZ", "TMUS", "CHTR"],
            "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "CL", "MDLZ", "KHC"],
            "Industrials": ["BA", "HON", "UNP", "UPS", "CAT", "RTX", "LMT", "DE", "GE", "MMM"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY", "HAL"],
            "Basic Materials": ["LIN", "APD", "ECL", "SHW", "DD", "NEM", "FCX", "NUE", "DOW", "ALB"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL", "DLR", "AVB"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "ED", "PEG"]
        }

        try:
            # Get company info
            stock = yf.Ticker(ticker)
            info = await asyncio.to_thread(lambda: stock.info)

            sector = info.get("sector")
            industry = info.get("industry")

            # Get company's valuation ratios
            pe_ratio = info.get("trailingPE")
            price_to_book = info.get("priceToBook")
            price_to_sales = info.get("priceToSalesTrailing12Months")

            if not sector:
                logger.warning(f"No sector information for {ticker}")
                return None

            # Get peer list for the sector
            peer_list = SECTOR_PEERS.get(sector, [])

            # Remove the ticker itself from peer list
            peer_list = [p for p in peer_list if p.upper() != ticker.upper()]

            if not peer_list:
                logger.warning(f"No predefined peers for sector: {sector}")
                peer_list = ["SPY"]  # S&P 500 ETF as fallback

            # ⚡ CONCURRENT PEER FETCHING - This is the key optimization!
            # Fetch all peers in parallel (limit to 5)
            peer_tasks = [self._fetch_peer_info_async(peer) for peer in peer_list[:5]]
            peer_results = await asyncio.gather(*peer_tasks, return_exceptions=True)

            # Process results and filter out errors
            peer_pe_ratios = []
            peer_pb_ratios = []
            peer_ps_ratios = []

            for result in peer_results:
                if isinstance(result, dict) and result:
                    if result.get("pe"):
                        peer_pe_ratios.append(result["pe"])
                    if result.get("pb"):
                        peer_pb_ratios.append(result["pb"])
                    if result.get("ps"):
                        peer_ps_ratios.append(result["ps"])

            # Calculate sector averages
            sector_avg_pe = sum(peer_pe_ratios) / len(peer_pe_ratios) if peer_pe_ratios else None
            sector_avg_pb = sum(peer_pb_ratios) / len(peer_pb_ratios) if peer_pb_ratios else None
            sector_avg_ps = sum(peer_ps_ratios) / len(peer_ps_ratios) if peer_ps_ratios else None

            # Calculate premium/discount
            pe_premium_discount = None
            if pe_ratio and sector_avg_pe and sector_avg_pe > 0:
                pe_premium_discount = ((pe_ratio - sector_avg_pe) / sector_avg_pe) * 100

            pb_premium_discount = None
            if price_to_book and sector_avg_pb and sector_avg_pb > 0:
                pb_premium_discount = ((price_to_book - sector_avg_pb) / sector_avg_pb) * 100

            ps_premium_discount = None
            if price_to_sales and sector_avg_ps and sector_avg_ps > 0:
                ps_premium_discount = ((price_to_sales - sector_avg_ps) / sector_avg_ps) * 100

            peer_valuation = {
                "ticker": ticker.upper(),
                "sector": sector,
                "industry": industry,
                # Company's valuation ratios
                "pe_ratio": pe_ratio,
                "price_to_book": price_to_book,
                "price_to_sales": price_to_sales,
                # Sector averages
                "sector_avg_pe": round(sector_avg_pe, 2) if sector_avg_pe else None,
                "sector_avg_pb": round(sector_avg_pb, 2) if sector_avg_pb else None,
                "sector_avg_ps": round(sector_avg_ps, 2) if sector_avg_ps else None,
                # Premium/discount
                "pe_premium_discount": round(pe_premium_discount, 1) if pe_premium_discount else None,
                "pb_premium_discount": round(pb_premium_discount, 1) if pb_premium_discount else None,
                "ps_premium_discount": round(ps_premium_discount, 1) if ps_premium_discount else None,
                # Metadata
                "peer_count": len(peer_pe_ratios)
            }

            logger.info(f"✅ Fetched peer valuation for {ticker} ({sector}) [ASYNC+CONCURRENT]")

            # Cache result
            self._set_cache(cache_key, peer_valuation)

            return peer_valuation

        except Exception as e:
            logger.error(f"❌ Failed to fetch peer valuation for {ticker}: {e}")
            return None


# Singleton instance
yahoo_finance = YahooFinanceService()
