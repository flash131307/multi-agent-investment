"""
Unit tests for backend/agents/fundamental/tools/financial_data.py.
All yfinance calls are mocked.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.agents.fundamental.tools.financial_data import (
    get_financial_statements,
    _compute_metrics,
    _get_row,
    _latest_value,
)


# ---------------------------------------------------------------------------
# Helpers to build realistic-ish DataFrames
# ---------------------------------------------------------------------------

def _make_income_stmt(net_income=(5_000, 4_000), revenue=(100_000, 90_000)):
    """Return a mock income_stmt DataFrame with two fiscal years."""
    import pandas as pd
    cols = pd.to_datetime(["2023-12-31", "2022-12-31"])
    data = {
        "Net Income": list(net_income),
        "Total Revenue": list(revenue),
    }
    return pd.DataFrame(data, index=cols).T


def _make_balance_sheet(
    equity=(25_000, 22_000),
    current_assets=(30_000, 28_000),
    current_liabilities=(15_000, 14_000),
    total_debt=(10_000, 9_000),
):
    import pandas as pd
    cols = pd.to_datetime(["2023-12-31", "2022-12-31"])
    data = {
        "Stockholders Equity": list(equity),
        "Current Assets": list(current_assets),
        "Current Liabilities": list(current_liabilities),
        "Total Debt": list(total_debt),
    }
    return pd.DataFrame(data, index=cols).T


# ---------------------------------------------------------------------------
# Tests for _get_row
# ---------------------------------------------------------------------------

class TestGetRow:
    def test_returns_row_when_label_matches(self):
        df = _make_income_stmt()
        row = _get_row(df, "Net Income")
        assert row is not None
        assert float(row.iloc[0]) == 5_000

    def test_returns_none_for_missing_label(self):
        df = _make_income_stmt()
        row = _get_row(df, "NonExistentRow")
        assert row is None

    def test_returns_none_for_empty_df(self):
        row = _get_row(pd.DataFrame(), "Net Income")
        assert row is None

    def test_returns_none_for_none_input(self):
        row = _get_row(None, "Net Income")
        assert row is None

    def test_tries_multiple_labels_in_order(self):
        df = _make_income_stmt()
        # "Total Revenue" should be found even though "Revenue" is tried first
        row = _get_row(df, "Revenue", "Total Revenue")
        assert row is not None
        assert float(row.iloc[0]) == 100_000


# ---------------------------------------------------------------------------
# Tests for _latest_value
# ---------------------------------------------------------------------------

class TestLatestValue:
    def test_returns_first_non_null(self):
        import pandas as pd
        s = pd.Series([5_000, 4_000])
        assert _latest_value(s) == 5_000

    def test_returns_none_for_all_null(self):
        import pandas as pd
        s = pd.Series([float("nan"), float("nan")])
        assert _latest_value(s) is None

    def test_returns_none_for_none_input(self):
        assert _latest_value(None) is None

    def test_returns_none_for_empty_series(self):
        import pandas as pd
        assert _latest_value(pd.Series([], dtype=float)) is None


# ---------------------------------------------------------------------------
# Tests for _compute_metrics
# ---------------------------------------------------------------------------

class TestComputeMetrics:
    def test_roe_computation(self):
        income = _make_income_stmt(net_income=(5_000, 4_000))
        balance = _make_balance_sheet(equity=(25_000, 22_000))
        metrics = _compute_metrics(income, balance)
        # ROE = 5000 / 25000 = 0.2
        assert metrics["roe"] == pytest.approx(0.2)

    def test_current_ratio_computation(self):
        income = _make_income_stmt()
        balance = _make_balance_sheet(
            current_assets=(30_000, 28_000),
            current_liabilities=(15_000, 14_000),
        )
        metrics = _compute_metrics(income, balance)
        # Current Ratio = 30000 / 15000 = 2.0
        assert metrics["current_ratio"] == pytest.approx(2.0)

    def test_debt_to_equity_computation(self):
        income = _make_income_stmt()
        balance = _make_balance_sheet(
            equity=(25_000, 22_000),
            total_debt=(10_000, 9_000),
        )
        metrics = _compute_metrics(income, balance)
        # D/E = 10000 / 25000 = 0.4
        assert metrics["debt_to_equity"] == pytest.approx(0.4)

    def test_revenue_growth_yoy(self):
        income = _make_income_stmt(revenue=(110_000, 100_000))
        balance = _make_balance_sheet()
        metrics = _compute_metrics(income, balance)
        # Growth = (110000 - 100000) / 100000 = 0.1
        assert metrics["revenue_growth_yoy"] == pytest.approx(0.1)

    def test_missing_equity_gives_none_roe(self):
        import pandas as pd
        income = _make_income_stmt(net_income=(5_000, 4_000))
        # Balance sheet without equity row
        balance = pd.DataFrame()
        metrics = _compute_metrics(income, balance)
        assert metrics["roe"] is None

    def test_missing_current_liabilities_gives_none_ratio(self):
        import pandas as pd
        income = _make_income_stmt()
        cols = pd.to_datetime(["2023-12-31", "2022-12-31"])
        # Only current assets, no liabilities
        balance = pd.DataFrame(
            {"Current Assets": [30_000, 28_000]}, index=cols
        ).T
        metrics = _compute_metrics(income, balance)
        assert metrics["current_ratio"] is None

    def test_empty_dataframes_return_none_metrics(self):
        import pandas as pd
        metrics = _compute_metrics(pd.DataFrame(), pd.DataFrame())
        assert metrics["roe"] is None
        assert metrics["current_ratio"] is None
        assert metrics["debt_to_equity"] is None
        assert metrics["revenue_growth_yoy"] is None

    def test_zero_equity_gives_none_roe(self):
        income = _make_income_stmt(net_income=(5_000, 4_000))
        balance = _make_balance_sheet(equity=(0, 0))
        metrics = _compute_metrics(income, balance)
        assert metrics["roe"] is None

    def test_only_one_revenue_period_gives_none_growth(self):
        import pandas as pd
        cols = pd.to_datetime(["2023-12-31"])
        income = pd.DataFrame(
            {"Total Revenue": [100_000]}, index=cols
        ).T
        balance = pd.DataFrame()
        metrics = _compute_metrics(income, balance)
        assert metrics["revenue_growth_yoy"] is None


# ---------------------------------------------------------------------------
# Tests for get_financial_statements (mocks yfinance)
# ---------------------------------------------------------------------------

class TestGetFinancialStatements:
    def _make_mock_ticker(
        self,
        income=None,
        balance=None,
        cashflow=None,
    ):
        mock_ticker = MagicMock()
        mock_ticker.income_stmt = income if income is not None else _make_income_stmt()
        mock_ticker.balance_sheet = balance if balance is not None else _make_balance_sheet()
        mock_ticker.cashflow = cashflow if cashflow is not None else pd.DataFrame()
        return mock_ticker

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_returns_dict_with_expected_keys(self, mock_yf_ticker):
        mock_yf_ticker.return_value = self._make_mock_ticker()
        result = get_financial_statements("AAPL")
        assert "income_stmt" in result
        assert "balance_sheet" in result
        assert "cash_flow" in result
        assert "metrics" in result

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_computes_roe_correctly(self, mock_yf_ticker):
        income = _make_income_stmt(net_income=(5_000, 4_000))
        balance = _make_balance_sheet(equity=(25_000, 22_000))
        mock_yf_ticker.return_value = self._make_mock_ticker(
            income=income, balance=balance
        )
        result = get_financial_statements("AAPL")
        assert result["metrics"]["roe"] == pytest.approx(0.2)

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_computes_current_ratio_correctly(self, mock_yf_ticker):
        balance = _make_balance_sheet(
            current_assets=(30_000, 28_000),
            current_liabilities=(10_000, 9_000),
        )
        mock_yf_ticker.return_value = self._make_mock_ticker(balance=balance)
        result = get_financial_statements("AAPL")
        assert result["metrics"]["current_ratio"] == pytest.approx(3.0)

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_computes_debt_to_equity_correctly(self, mock_yf_ticker):
        balance = _make_balance_sheet(
            equity=(20_000, 18_000),
            total_debt=(8_000, 7_000),
        )
        mock_yf_ticker.return_value = self._make_mock_ticker(balance=balance)
        result = get_financial_statements("AAPL")
        assert result["metrics"]["debt_to_equity"] == pytest.approx(0.4)

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_computes_revenue_growth_correctly(self, mock_yf_ticker):
        income = _make_income_stmt(revenue=(110_000, 100_000))
        mock_yf_ticker.return_value = self._make_mock_ticker(income=income)
        result = get_financial_statements("AAPL")
        assert result["metrics"]["revenue_growth_yoy"] == pytest.approx(0.1)

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_missing_data_does_not_crash(self, mock_yf_ticker):
        mock_yf_ticker.return_value = self._make_mock_ticker(
            income=pd.DataFrame(),
            balance=pd.DataFrame(),
            cashflow=pd.DataFrame(),
        )
        result = get_financial_statements("AAPL")
        assert result["metrics"]["roe"] is None
        assert result["metrics"]["current_ratio"] is None
        assert result["metrics"]["debt_to_equity"] is None
        assert result["metrics"]["revenue_growth_yoy"] is None

    @patch("backend.agents.fundamental.tools.financial_data.yf.Ticker")
    def test_empty_dataframes_handled_gracefully(self, mock_yf_ticker):
        mock_yf_ticker.return_value = self._make_mock_ticker(
            income=pd.DataFrame(),
            balance=pd.DataFrame(),
        )
        result = get_financial_statements("MSFT")
        assert isinstance(result, dict)
        assert isinstance(result["metrics"], dict)
