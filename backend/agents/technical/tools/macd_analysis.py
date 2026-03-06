"""
MACD-based signal computation with crossover detection.
"""
import pandas as pd
import ta

from backend.models.technical import Reliability, ToolOutput, ToolSignal

_MIN_ROWS = 60
_CROSSOVER_WINDOW = 3  # bars to look back for crossover


def compute_macd_signal(df: pd.DataFrame) -> ToolOutput:
    """
    Compute MACD (12, 26, 9) signal with crossover detection.

    Crossover detection (last 3 bars):
    - Golden cross (MACD crosses above signal) → BULLISH (HIGH reliability)
    - Death cross  (MACD crosses below signal) → BEARISH (HIGH reliability)

    Position logic (when no recent crossover):
    - MACD > 0 and MACD > signal → BULLISH (MEDIUM)
    - MACD < 0 and MACD < signal → BEARISH (MEDIUM)
    - else                        → NEUTRAL (LOW)

    Args:
        df: OHLCV DataFrame with at least 60 rows.

    Returns:
        ToolOutput with raw_values={"macd": float, "signal": float, "histogram": float}.

    Raises:
        ValueError: If DataFrame has fewer than 60 rows.
    """
    if len(df) < _MIN_ROWS:
        raise ValueError(
            f"Insufficient data: need at least {_MIN_ROWS} rows, got {len(df)}"
        )

    close = df["Close"]
    macd_indicator = ta.trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)

    macd_line = macd_indicator.macd()
    signal_line = macd_indicator.macd_signal()
    histogram = macd_indicator.macd_diff()

    # Drop NaN
    valid = macd_line.notna() & signal_line.notna() & histogram.notna()
    macd_clean = macd_line[valid]
    signal_clean = signal_line[valid]
    hist_clean = histogram[valid]

    if len(macd_clean) < 2:
        raise ValueError("MACD calculation produced insufficient non-NaN values.")

    macd_val = float(macd_clean.iloc[-1])
    signal_val = float(signal_clean.iloc[-1])
    hist_val = float(hist_clean.iloc[-1])

    # Crossover detection in last _CROSSOVER_WINDOW bars
    window = min(_CROSSOVER_WINDOW, len(macd_clean))
    recent_macd = macd_clean.iloc[-window:].values
    recent_signal = signal_clean.iloc[-window:].values

    golden_cross = False
    death_cross = False
    for i in range(1, len(recent_macd)):
        prev_diff = recent_macd[i - 1] - recent_signal[i - 1]
        curr_diff = recent_macd[i] - recent_signal[i]
        if prev_diff < 0 and curr_diff >= 0:
            golden_cross = True
        elif prev_diff > 0 and curr_diff <= 0:
            death_cross = True

    if golden_cross:
        signal = ToolSignal.BULLISH
        reliability = Reliability.HIGH
        interpretation = (
            f"MACD golden cross detected (MACD crossed above signal in last {_CROSSOVER_WINDOW} bars). "
            f"MACD={macd_val:.4f}, Signal={signal_val:.4f}. Strong bullish momentum."
        )
    elif death_cross:
        signal = ToolSignal.BEARISH
        reliability = Reliability.HIGH
        interpretation = (
            f"MACD death cross detected (MACD crossed below signal in last {_CROSSOVER_WINDOW} bars). "
            f"MACD={macd_val:.4f}, Signal={signal_val:.4f}. Strong bearish momentum."
        )
    elif macd_val > 0 and macd_val > signal_val:
        signal = ToolSignal.BULLISH
        reliability = Reliability.MEDIUM
        interpretation = (
            f"MACD={macd_val:.4f} positive and above signal ({signal_val:.4f}). "
            f"Moderate bullish momentum, no recent crossover."
        )
    elif macd_val < 0 and macd_val < signal_val:
        signal = ToolSignal.BEARISH
        reliability = Reliability.MEDIUM
        interpretation = (
            f"MACD={macd_val:.4f} negative and below signal ({signal_val:.4f}). "
            f"Moderate bearish momentum, no recent crossover."
        )
    else:
        signal = ToolSignal.NEUTRAL
        reliability = Reliability.LOW
        interpretation = (
            f"MACD={macd_val:.4f}, Signal={signal_val:.4f}. "
            f"No clear directional signal."
        )

    return ToolOutput(
        tool_name="macd_analysis",
        signal=signal,
        reliability=reliability,
        interpretation=interpretation,
        raw_values={"macd": macd_val, "signal": signal_val, "histogram": hist_val},
    )
