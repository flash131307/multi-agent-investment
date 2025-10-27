"""
Dynamic Ticker Resolver Service.

Intelligently resolves company names to stock ticker symbols using:
1. Local cache (fastest)
2. yfinance direct query (medium)
3. LLM semantic understanding (smartest)
"""
import json
import os
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
from openai import AsyncOpenAI

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class TickerResolver:
    """
    Dynamically resolves company names to ticker symbols.

    Features:
    - Three-layer resolution (cache → yfinance → LLM)
    - TTL-based cache expiration
    - S&P 500 initialization
    - Handles aliases and abbreviations
    """

    def __init__(
        self,
        cache_path: Optional[str] = None,
        ttl_days: int = 90,
        enable_llm: bool = True,
        llm_confidence_threshold: float = 0.7
    ):
        """
        Initialize ticker resolver.

        Args:
            cache_path: Path to cache file
            ttl_days: Cache entry TTL in days
            enable_llm: Whether to use LLM for resolution
            llm_confidence_threshold: Minimum LLM confidence
        """
        self.cache_path = cache_path or "backend/data/ticker_cache.json"
        self.ttl_days = ttl_days
        self.enable_llm = enable_llm
        self.llm_confidence_threshold = llm_confidence_threshold

        # In-memory cache for fast lookup
        self.cache: Dict[str, Any] = {}

        # OpenAI client for LLM resolution
        self.llm_client = AsyncOpenAI(api_key=settings.openai_api_key) if enable_llm else None

        # Load cache from disk
        self._load_cache()

        logger.info(f"✅ TickerResolver initialized with {len(self.cache.get('companies', {}))} cached companies")

    def _load_cache(self):
        """Load cache from disk into memory."""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded ticker cache from {self.cache_path}")
            else:
                # Initialize empty cache
                self.cache = {
                    "metadata": {
                        "last_updated": datetime.utcnow().isoformat(),
                        "version": "1.0",
                        "total_entries": 0
                    },
                    "companies": {}
                }
                logger.info("Initialized empty ticker cache")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self.cache = {"metadata": {}, "companies": {}}

    def _save_cache(self):
        """Save in-memory cache to disk."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

            # Update metadata
            self.cache["metadata"]["last_updated"] = datetime.utcnow().isoformat()
            self.cache["metadata"]["total_entries"] = len(self.cache.get("companies", {}))

            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)

            logger.debug(f"Saved ticker cache to {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _normalize_name(self, name: str) -> str:
        """
        Normalize company name for cache lookup.

        Args:
            name: Company name

        Returns:
            Normalized lowercase name
        """
        # Remove common suffixes
        name = re.sub(r'\s+(Inc\.?|Corp\.?|Corporation|Ltd\.?|LLC|Company|Co\.?)$', '', name, flags=re.IGNORECASE)
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())  # Normalize whitespace
        return name.lower().strip()

    def _is_cache_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Check if cache entry is expired.

        Args:
            entry: Cache entry dict

        Returns:
            True if expired, False otherwise
        """
        try:
            cached_at = datetime.fromisoformat(entry['cached_at'])
            ttl_days = entry.get('ttl_days', self.ttl_days)
            expiry = cached_at + timedelta(days=ttl_days)
            return datetime.utcnow() > expiry
        except Exception as e:
            logger.warning(f"Error checking cache expiry: {e}")
            return True  # Treat as expired if error

    async def resolve(self, company_name: str) -> Optional[str]:
        """
        Resolve company name to ticker symbol.

        Uses three-layer approach:
        1. Local cache (fastest)
        2. yfinance direct query
        3. LLM semantic understanding

        Args:
            company_name: Company name or alias

        Returns:
            Ticker symbol (e.g., "AAPL") or None
        """
        if not company_name:
            return None

        # Check if already a valid ticker (uppercase, 1-5 chars)
        if re.match(r'^[A-Z]{1,5}$', company_name.strip()):
            # Validate it's a real ticker
            if self._validate_ticker_sync(company_name):
                return company_name.upper()

        # Normalize for cache lookup
        normalized = self._normalize_name(company_name)

        # Layer 1: Cache lookup
        ticker = self._query_cache(normalized)
        if ticker:
            logger.info(f"✅ Cache hit: '{company_name}' → {ticker}")
            return ticker

        # Layer 2: yfinance direct query
        ticker = await self._query_yfinance(company_name)
        if ticker:
            logger.info(f"✅ yfinance hit: '{company_name}' → {ticker}")
            self._update_cache(normalized, ticker, company_name, source="yfinance")
            return ticker

        # Layer 3: LLM semantic understanding
        if self.enable_llm:
            ticker = await self._query_llm(company_name)
            if ticker:
                logger.info(f"✅ LLM resolved: '{company_name}' → {ticker}")
                self._update_cache(normalized, ticker, company_name, source="llm")
                return ticker

        logger.warning(f"❌ Could not resolve: '{company_name}'")
        return None

    def _query_cache(self, normalized_name: str) -> Optional[str]:
        """
        Query cache for ticker.

        Args:
            normalized_name: Normalized company name

        Returns:
            Ticker or None
        """
        companies = self.cache.get("companies", {})

        # Direct lookup
        if normalized_name in companies:
            entry = companies[normalized_name]

            # Check expiration
            if self._is_cache_expired(entry):
                logger.debug(f"Cache entry expired for '{normalized_name}'")
                return None

            return entry.get("ticker")

        # Check aliases
        for name, entry in companies.items():
            aliases = entry.get("aliases", [])
            if normalized_name in [self._normalize_name(a) for a in aliases]:
                if not self._is_cache_expired(entry):
                    return entry.get("ticker")

        return None

    async def _query_yfinance(self, company_name: str) -> Optional[str]:
        """
        Query yfinance for ticker.

        Args:
            company_name: Company name

        Returns:
            Ticker or None
        """
        try:
            # Try as ticker first
            ticker_obj = yf.Ticker(company_name)
            info = ticker_obj.info

            # Check if valid
            if info and info.get("symbol"):
                ticker = info["symbol"]
                # Validate it matches the name
                official_name = info.get("longName") or info.get("shortName", "")
                if company_name.lower() in official_name.lower():
                    return ticker

            # TODO: yfinance doesn't have good company name search
            # This layer mainly validates ticker symbols
            return None

        except Exception as e:
            logger.debug(f"yfinance query failed for '{company_name}': {e}")
            return None

    async def _query_llm(self, company_name: str) -> Optional[str]:
        """
        Query LLM for ticker using semantic understanding.

        Args:
            company_name: Company name or alias

        Returns:
            Ticker or None
        """
        if not self.llm_client:
            return None

        prompt = f"""You are a financial ticker resolver. Identify the stock ticker symbol for this company.

Company input: "{company_name}"

Rules:
- Return the primary US stock ticker (e.g., "AAPL" for Apple)
- Handle common aliases (e.g., "Facebook" → "META", "Google" → "GOOGL")
- Handle abbreviations (e.g., "J&J" → "JNJ")
- Only return publicly traded US companies
- If ambiguous or not a known company, return null

Respond ONLY in JSON format:
{{"ticker": "AAPL", "confidence": 0.95, "official_name": "Apple Inc."}}
or
{{"ticker": null, "confidence": 0.0, "official_name": null}}"""

        try:
            response = await self.llm_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            result = json.loads(content)

            # Handle case where result might be a list or not have expected structure
            if isinstance(result, list):
                result = result[0] if result else {}

            ticker = result.get("ticker")
            confidence = result.get("confidence", 0.0)

            if ticker and confidence >= self.llm_confidence_threshold:
                # Validate ticker with yfinance
                if self._validate_ticker_sync(ticker):
                    return ticker.upper()

            return None

        except Exception as e:
            logger.error(f"LLM query failed for '{company_name}': {e}")
            return None

    def _validate_ticker_sync(self, ticker: str) -> bool:
        """
        Validate ticker symbol synchronously.

        Args:
            ticker: Ticker symbol

        Returns:
            True if valid, False otherwise
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            # Check if has basic required fields
            return bool(info and (info.get("symbol") or info.get("shortName")))
        except:
            return False

    def _update_cache(
        self,
        normalized_name: str,
        ticker: str,
        original_name: str,
        source: str = "unknown"
    ):
        """
        Update cache with new ticker mapping.

        Args:
            normalized_name: Normalized company name (cache key)
            ticker: Ticker symbol
            original_name: Original company name
            source: Data source (sp500, yfinance, llm)
        """
        companies = self.cache.setdefault("companies", {})

        companies[normalized_name] = {
            "ticker": ticker.upper(),
            "official_name": original_name,
            "cached_at": datetime.utcnow().isoformat(),
            "ttl_days": self.ttl_days,
            "source": source
        }

        # Save to disk
        self._save_cache()

    def add_sp500_companies(self, sp500_data: Dict[str, str]):
        """
        Bulk add S&P 500 companies to cache.

        Args:
            sp500_data: Dict of {normalized_name: ticker}
        """
        companies = self.cache.setdefault("companies", {})

        for name, ticker in sp500_data.items():
            normalized = self._normalize_name(name)
            companies[normalized] = {
                "ticker": ticker.upper(),
                "official_name": name,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl_days": self.ttl_days,
                "source": "sp500"
            }

        logger.info(f"Added {len(sp500_data)} S&P 500 companies to cache")
        self._save_cache()


# Singleton instance
ticker_resolver = TickerResolver(
    ttl_days=90,
    enable_llm=True,
    llm_confidence_threshold=0.7
)
