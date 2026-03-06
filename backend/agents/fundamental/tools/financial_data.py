"""
Financial statements fetcher: pulls income statement, balance sheet, and
cash flow from yfinance and computes key cross-statement metrics.
"""
import logging
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)


def get_financial_statements(ticker: str) -> dict:
    """
    Fetch financial statements and compute key metrics for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").

    Returns:
        Dict containing:
          - "income_stmt": raw income statement DataFrame (as dict)
          - "balance_sheet": raw balance sheet DataFrame (as dict)
          - "cash_flow": raw cash flow DataFrame (as dict)
          - "metrics": dict of computed metrics (None when data is missing)
    """
    stock = yf.Ticker(ticker)

    income_stmt = _safe_fetch(stock, "income_stmt")
    balance_sheet = _safe_fetch(stock, "balance_sheet")
    cash_flow = _safe_fetch(stock, "cashflow")

    metrics = _compute_metrics(income_stmt, balance_sheet)

    return {
        "income_stmt": income_stmt,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_fetch(stock, attr: str):
    """Fetch a DataFrame attribute from a yfinance Ticker, returning empty DF on error."""
    try:
        import pandas as pd  # type: ignore
        df = getattr(stock, attr, None)
        if df is None or (hasattr(df, "empty") and df.empty):
            return pd.DataFrame()
        return df
    except Exception as exc:
        logger.warning("Failed to fetch '%s' for ticker: %s", attr, exc)
        try:
            import pandas as pd
            return pd.DataFrame()
        except ImportError:
            return {}


def _get_row(df, *possible_labels: str):
    """
    Retrieve the first row from a DataFrame matching any of the given labels.
    Returns a pandas Series or None.
    """
    if df is None or (hasattr(df, "empty") and df.empty):
        return None
    for label in possible_labels:
        if label in df.index:
            return df.loc[label]
    return None


def _latest_value(series) -> float | None:
    """Return the most recent (first column) value from a pandas Series, or None."""
    if series is None:
        return None
    try:
        values = series.dropna()
        if len(values) == 0:
            return None
        return float(values.iloc[0])
    except Exception:
        return None


def _compute_metrics(income_stmt, balance_sheet) -> dict[str, Any]:
    """Compute cross-statement financial metrics."""
    metrics: dict[str, Any] = {
        "roe": None,
        "current_ratio": None,
        "debt_to_equity": None,
        "revenue_growth_yoy": None,
    }

    # --- ROE = Net Income / Total Stockholder Equity ---
    net_income_row = _get_row(
        income_stmt,
        "Net Income",
        "NetIncome",
        "Net income",
        "Net Income Common Stockholders",
    )
    equity_row = _get_row(
        balance_sheet,
        "Stockholders Equity",
        "Total Stockholder Equity",
        "Total Equity Gross Minority Interest",
        "Common Stock Equity",
        "TotalStockholdersEquity",
    )

    net_income = _latest_value(net_income_row)
    equity = _latest_value(equity_row)

    if net_income is not None and equity is not None and equity != 0:
        metrics["roe"] = net_income / equity

    # --- Current Ratio = Current Assets / Current Liabilities ---
    current_assets_row = _get_row(
        balance_sheet,
        "Current Assets",
        "Total Current Assets",
        "TotalCurrentAssets",
    )
    current_liabilities_row = _get_row(
        balance_sheet,
        "Current Liabilities",
        "Total Current Liabilities",
        "TotalCurrentLiabilities",
    )

    current_assets = _latest_value(current_assets_row)
    current_liabilities = _latest_value(current_liabilities_row)

    if (
        current_assets is not None
        and current_liabilities is not None
        and current_liabilities != 0
    ):
        metrics["current_ratio"] = current_assets / current_liabilities

    # --- Debt-to-Equity = Total Debt / Total Equity ---
    debt_row = _get_row(
        balance_sheet,
        "Total Debt",
        "Long Term Debt",
        "LongTermDebt",
        "Short Long Term Debt",
    )

    total_debt = _latest_value(debt_row)

    if total_debt is not None and equity is not None and equity != 0:
        metrics["debt_to_equity"] = total_debt / equity

    # --- Revenue Growth YoY = (Revenue_t - Revenue_t-1) / Revenue_t-1 ---
    revenue_row = _get_row(
        income_stmt,
        "Total Revenue",
        "Revenue",
        "TotalRevenue",
        "Net Revenue",
    )

    if revenue_row is not None:
        try:
            non_null = revenue_row.dropna()
            if len(non_null) >= 2:
                rev_t = float(non_null.iloc[0])
                rev_t1 = float(non_null.iloc[1])
                if rev_t1 != 0:
                    metrics["revenue_growth_yoy"] = (rev_t - rev_t1) / rev_t1
        except Exception as exc:
            logger.warning("Could not compute revenue growth: %s", exc)

    return metrics
