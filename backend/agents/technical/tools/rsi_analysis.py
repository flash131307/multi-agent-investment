"""
RSI-based signal computation with context-aware thresholds.
"""
import pandas as pd
import ta

from backend.models.technical import MarketRegime, RegimeType, Reliability, ToolOutput, ToolSignal

_MIN_ROWS = 60


def compute_rsi_signal(df: pd.DataFrame, regime: MarketRegime) -> ToolOutput:
    """
    Compute RSI (14-period) signal, adapting thresholds to the current market regime.

    Thresholds:
    - TRENDING:                overbought=75, oversold=25
    - RANGING / HIGH_VOL:      overbought=70, oversold=30

    Signal logic:
    - RSI < oversold  → BULLISH (HIGH if trending, MEDIUM otherwise)
    - RSI > overbought → BEARISH (HIGH if trending, MEDIUM otherwise)
    - RSI 45-55       → NEUTRAL (MEDIUM)
    - else            → NEUTRAL (LOW)

    Args:
        df:     OHLCV DataFrame.
        regime: Pre-computed MarketRegime (from compute_market_regime).

    Returns:
        ToolOutput with raw_values={"rsi": float}.

    Raises:
        ValueError: If DataFrame has fewer than 60 rows.
    """
    if len(df) < _MIN_ROWS:
        raise ValueError(
            f"Insufficient data: need at least {_MIN_ROWS} rows, got {len(df)}"
        )

    close = df["Close"]
    rsi_series = ta.momentum.RSIIndicator(close=close, window=14).rsi()

    # Use last non-NaN value
    last_rsi = rsi_series.dropna().iloc[-1] if not rsi_series.dropna().empty else None
    if last_rsi is None:
        raise ValueError("RSI calculation produced all NaN values — insufficient data.")

    rsi_val = float(last_rsi)

    # Context-aware thresholds
    is_trending = regime.regime_type == RegimeType.TRENDING
    overbought = 75 if is_trending else 70
    oversold = 25 if is_trending else 30

    if rsi_val < oversold:
        signal = ToolSignal.BULLISH
        reliability = Reliability.HIGH if is_trending else Reliability.MEDIUM
        interpretation = (
            f"RSI={rsi_val:.1f} below oversold threshold ({oversold}) in "
            f"{'trending' if is_trending else 'ranging/volatile'} market. "
            f"Potential bullish reversal."
        )
    elif rsi_val > overbought:
        signal = ToolSignal.BEARISH
        reliability = Reliability.HIGH if is_trending else Reliability.MEDIUM
        interpretation = (
            f"RSI={rsi_val:.1f} above overbought threshold ({overbought}) in "
            f"{'trending' if is_trending else 'ranging/volatile'} market. "
            f"Potential bearish reversal."
        )
    elif 45 <= rsi_val <= 55:
        signal = ToolSignal.NEUTRAL
        reliability = Reliability.MEDIUM
        interpretation = f"RSI={rsi_val:.1f} in neutral zone (45-55). No directional bias."
    else:
        signal = ToolSignal.NEUTRAL
        reliability = Reliability.LOW
        interpretation = (
            f"RSI={rsi_val:.1f} — neither overbought ({overbought}) nor oversold ({oversold}). "
            f"Indeterminate signal."
        )

    return ToolOutput(
        tool_name="rsi_analysis",
        signal=signal,
        reliability=reliability,
        interpretation=interpretation,
        raw_values={"rsi": rsi_val},
    )
