"""
Initialize ticker cache with S&P 500 companies.

Downloads S&P 500 list from Wikipedia and populates the ticker cache.
"""
import asyncio
import sys
import logging
from typing import Dict

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas")
    sys.exit(1)

from backend.services.ticker_resolver import ticker_resolver

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def download_sp500() -> Dict[str, str]:
    """
    Download S&P 500 companies from Wikipedia.

    Returns:
        Dict mapping company names to tickers
    """
    logger.info("Downloading S&P 500 list from Wikipedia...")

    try:
        # Wikipedia URL for S&P 500
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

        # Read the first table (current S&P 500 companies)
        tables = pd.read_html(url)
        sp500_df = tables[0]

        # Extract company name and ticker
        # Columns: Symbol, Security, SEC filings, GICS Sector, ...
        companies = {}

        for _, row in sp500_df.iterrows():
            ticker = row.get('Symbol', row.get('Ticker'))
            company_name = row.get('Security', row.get('Company'))

            if ticker and company_name:
                # Clean up company name
                company_name = str(company_name).strip()
                ticker = str(ticker).strip()

                companies[company_name] = ticker

        logger.info(f"✅ Downloaded {len(companies)} S&P 500 companies")
        return companies

    except Exception as e:
        logger.error(f"❌ Failed to download S&P 500: {e}")
        logger.info("Falling back to hardcoded list...")
        return get_fallback_sp500()


def get_fallback_sp500() -> Dict[str, str]:
    """
    Fallback S&P 500 list if Wikipedia download fails.

    Returns:
        Dict of major companies
    """
    return {
        # Technology
        "Apple Inc.": "AAPL",
        "Microsoft Corporation": "MSFT",
        "Alphabet Inc. Class A": "GOOGL",
        "Amazon.com Inc.": "AMZN",
        "NVIDIA Corporation": "NVDA",
        "Meta Platforms Inc.": "META",
        "Tesla Inc.": "TSLA",

        # Finance
        "JPMorgan Chase & Co.": "JPM",
        "Visa Inc.": "V",
        "Mastercard Incorporated": "MA",
        "Bank of America Corporation": "BAC",

        # Healthcare
        "Johnson & Johnson": "JNJ",
        "UnitedHealth Group Incorporated": "UNH",
        "Pfizer Inc.": "PFE",

        # Consumer
        "Walmart Inc.": "WMT",
        "Procter & Gamble Company": "PG",
        "Coca-Cola Company": "KO",
        "PepsiCo Inc.": "PEP",
        "Nike Inc.": "NKE",

        # Other
        "Berkshire Hathaway Inc.": "BRK.B",
        "Exxon Mobil Corporation": "XOM",
        "Chevron Corporation": "CVX",
        "Home Depot Inc.": "HD",
        "Walt Disney Company": "DIS",
    }


async def main():
    """Main initialization function."""
    print("="*70)
    print("TICKER CACHE INITIALIZATION")
    print("="*70)
    print()

    # Download S&P 500
    sp500_companies = download_sp500()

    print(f"\nTotal companies to add: {len(sp500_companies)}")
    print("\nSample companies:")
    for i, (name, ticker) in enumerate(list(sp500_companies.items())[:10], 1):
        print(f"  {i}. {name} → {ticker}")
    print(f"  ... and {len(sp500_companies) - 10} more")

    # Confirm before proceeding
    print(f"\n{'-'*70}")
    response = input("Proceed with initialization? (y/n): ").strip().lower()

    if response != 'y':
        print("❌ Initialization cancelled")
        return

    # Add to cache
    print(f"\n{'-'*70}")
    print("Adding companies to cache...")
    ticker_resolver.add_sp500_companies(sp500_companies)

    print(f"\n✅ Cache initialized successfully!")
    print(f"   - Total entries: {len(sp500_companies)}")
    print(f"   - Cache file: {ticker_resolver.cache_path}")

    # Test a few companies
    print(f"\n{'-'*70}")
    print("Testing ticker resolution...")

    test_names = [
        "Apple",
        "Microsoft",
        "Google",
        "Facebook",
        "Amazon",
        "Tesla"
    ]

    for name in test_names:
        ticker = await ticker_resolver.resolve(name)
        status = "✅" if ticker else "❌"
        print(f"  {status} '{name}' → {ticker or 'NOT FOUND'}")

    print(f"\n{'-'*70}")
    print("Initialization complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
