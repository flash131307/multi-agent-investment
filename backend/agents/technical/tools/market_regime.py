"""
Market regime detection using ADX, ATR, and moving averages.
"""
import pandas as pd
import ta

from backend.models.technical import MarketRegime, RegimeType

_MIN_ROWS = 60


def compute_market_regime(df: pd.DataFrame) -> MarketRegime:
    """
    Classify the current market regime as TRENDING, RANGING, or HIGH_VOLATILITY.

    Rules (in priority order):
    1. ATR > 2 × rolling_mean(ATR, 20)  → HIGH_VOLATILITY
    2. ADX > 25 AND MA20 > MA50          → TRENDING (bullish), trend_strength = ADX/100
    3. ADX > 25 AND MA20 < MA50          → TRENDING (bearish), trend_strength = ADX/100
    4. otherwise                          → RANGING

    Args:
        df: OHLCV DataFrame with columns Open, High, Low, Close, Volume.

    Returns:
        MarketRegime (frozen Pydantic model).

    Raises:
        ValueError: If DataFrame has fewer than 60 rows or required columns are missing.
    """
    required = {"High", "Low", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    if len(df) < _MIN_ROWS:
        raise ValueError(
            f"Insufficient data: need at least {_MIN_ROWS} rows, got {len(df)}"
        )

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # ADX 14-period
    adx_indicator = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14)
    adx_series = adx_indicator.adx()

    # ATR 14-period
    atr_indicator = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14)
    atr_series = atr_indicator.average_true_range()

    # Simple moving averages
    ma20 = close.rolling(window=20).mean()
    ma50 = close.rolling(window=50).mean()

    # Drop NaN rows for safe computation
    valid_mask = adx_series.notna() & atr_series.notna() & ma20.notna() & ma50.notna()
    if not valid_mask.any():
        raise ValueError("All computed indicator values are NaN — insufficient data.")

    last_valid_idx = valid_mask[::-1].idxmax()

    adx_val = float(adx_series[last_valid_idx])
    atr_val = float(atr_series[last_valid_idx])
    close_val = float(close[last_valid_idx])
    ma20_val = float(ma20[last_valid_idx])
    ma50_val = float(ma50[last_valid_idx])

    # ATR rolling mean (20-period) for volatility spike detection
    atr_rolling_mean = atr_series.rolling(window=20).mean()
    atr_mean_val = float(atr_rolling_mean[last_valid_idx]) if atr_rolling_mean[last_valid_idx] is not None else atr_val

    # Normalized volatility
    volatility = atr_val / close_val if close_val > 0 else 0.0

    # Regime classification
    if pd.notna(atr_mean_val) and atr_mean_val > 0 and atr_val > 2 * atr_mean_val:
        regime_type = RegimeType.HIGH_VOLATILITY
        trend_strength = min(volatility, 1.0)
        interpretation = (
            f"High volatility regime: ATR ({atr_val:.2f}) exceeds 2× the 20-period "
            f"ATR mean ({atr_mean_val:.2f}). Extreme price swings detected."
        )
    elif adx_val > 25 and ma20_val > ma50_val:
        regime_type = RegimeType.TRENDING
        trend_strength = min(adx_val / 100.0, 1.0)
        interpretation = (
            f"Bullish trending regime: ADX={adx_val:.1f} (>25) with MA20 ({ma20_val:.2f}) "
            f"above MA50 ({ma50_val:.2f}). Strong upward directional movement."
        )
    elif adx_val > 25 and ma20_val < ma50_val:
        regime_type = RegimeType.TRENDING
        trend_strength = min(adx_val / 100.0, 1.0)
        interpretation = (
            f"Bearish trending regime: ADX={adx_val:.1f} (>25) with MA20 ({ma20_val:.2f}) "
            f"below MA50 ({ma50_val:.2f}). Strong downward directional movement."
        )
    else:
        regime_type = RegimeType.RANGING
        trend_strength = min(adx_val / 100.0, 1.0)
        interpretation = (
            f"Ranging market: ADX={adx_val:.1f} (<=25). No clear directional trend. "
            f"Price oscillating between support and resistance levels."
        )

    return MarketRegime(
        regime_type=regime_type,
        trend_strength=trend_strength,
        volatility=volatility,
        interpretation=interpretation,
    )
