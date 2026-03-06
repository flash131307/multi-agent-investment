"""
Simple pattern recognition using last 20 bars of price data.
"""
import pandas as pd
import numpy as np

from backend.models.technical import Reliability, ToolOutput, ToolSignal

_MIN_ROWS = 60
_PATTERN_WINDOW = 20
_DOUBLE_TOLERANCE = 0.03  # 3% tolerance for double top/bottom


def _find_local_extrema(series: pd.Series, order: int = 3):
    """
    Return (local_min_indices, local_max_indices) using a rolling window approach.
    """
    values = series.values
    n = len(values)
    local_mins = []
    local_maxes = []
    for i in range(order, n - order):
        window = values[i - order: i + order + 1]
        if values[i] == min(window):
            local_mins.append(i)
        if values[i] == max(window):
            local_maxes.append(i)
    return local_mins, local_maxes


def _detect_double_bottom(close_window: pd.Series) -> bool:
    """
    Double bottom: two local mins within 3% of each other, price now > midpoint.
    """
    local_mins, _ = _find_local_extrema(close_window, order=2)
    if len(local_mins) < 2:
        return False
    # Use the last two local mins
    idx1, idx2 = local_mins[-2], local_mins[-1]
    v1, v2 = float(close_window.iloc[idx1]), float(close_window.iloc[idx2])
    avg = (v1 + v2) / 2
    if avg <= 0:
        return False
    within_tolerance = abs(v1 - v2) / avg <= _DOUBLE_TOLERANCE
    current_price = float(close_window.iloc[-1])
    midpoint = (v1 + v2) / 2
    return within_tolerance and current_price > midpoint


def _detect_double_top(close_window: pd.Series) -> bool:
    """
    Double top: two local maxes within 3% of each other, price now < midpoint.
    """
    _, local_maxes = _find_local_extrema(close_window, order=2)
    if len(local_maxes) < 2:
        return False
    idx1, idx2 = local_maxes[-2], local_maxes[-1]
    v1, v2 = float(close_window.iloc[idx1]), float(close_window.iloc[idx2])
    avg = (v1 + v2) / 2
    if avg <= 0:
        return False
    within_tolerance = abs(v1 - v2) / avg <= _DOUBLE_TOLERANCE
    current_price = float(close_window.iloc[-1])
    midpoint = (v1 + v2) / 2
    return within_tolerance and current_price < midpoint


def _detect_higher_lows(close_window: pd.Series, n_consecutive: int = 3) -> bool:
    """
    Detect n consecutive higher lows using local minima.
    """
    local_mins, _ = _find_local_extrema(close_window, order=2)
    if len(local_mins) < n_consecutive:
        return False
    recent = local_mins[-n_consecutive:]
    values = [float(close_window.iloc[i]) for i in recent]
    return all(values[i] > values[i - 1] for i in range(1, len(values)))


def _detect_lower_highs(close_window: pd.Series, n_consecutive: int = 3) -> bool:
    """
    Detect n consecutive lower highs using local maxima.
    """
    _, local_maxes = _find_local_extrema(close_window, order=2)
    if len(local_maxes) < n_consecutive:
        return False
    recent = local_maxes[-n_consecutive:]
    values = [float(close_window.iloc[i]) for i in recent]
    return all(values[i] < values[i - 1] for i in range(1, len(values)))


def compute_pattern_signal(df: pd.DataFrame) -> ToolOutput:
    """
    Detect simple price patterns in the last 20 bars.

    Patterns (in priority order):
    1. Double bottom   → BULLISH
    2. Double top      → BEARISH
    3. Higher lows (3) → BULLISH
    4. Lower highs (3) → BEARISH
    5. No pattern      → NEUTRAL

    Reliability is always LOW (pattern recognition is heuristic).

    Args:
        df: OHLCV DataFrame with at least 60 rows.

    Returns:
        ToolOutput with raw_values={"pattern": str}.

    Raises:
        ValueError: If DataFrame has fewer than 60 rows.
    """
    if len(df) < _MIN_ROWS:
        raise ValueError(
            f"Insufficient data: need at least {_MIN_ROWS} rows, got {len(df)}"
        )

    close = df["Close"].dropna()
    if len(close) < _PATTERN_WINDOW:
        raise ValueError("Insufficient non-NaN Close values for pattern recognition.")

    window = close.iloc[-_PATTERN_WINDOW:]

    if _detect_double_bottom(window):
        pattern_name = "double_bottom"
        signal = ToolSignal.BULLISH
        interpretation = (
            "Double bottom pattern detected in last 20 bars: two similar lows followed "
            "by price recovery above the midpoint. Potential bullish reversal."
        )
    elif _detect_double_top(window):
        pattern_name = "double_top"
        signal = ToolSignal.BEARISH
        interpretation = (
            "Double top pattern detected in last 20 bars: two similar highs followed "
            "by price falling below the midpoint. Potential bearish reversal."
        )
    elif _detect_higher_lows(window):
        pattern_name = "higher_lows"
        signal = ToolSignal.BULLISH
        interpretation = (
            "Higher lows pattern: 3 consecutive higher local lows detected in last 20 bars. "
            "Suggests accumulation and bullish bias."
        )
    elif _detect_lower_highs(window):
        pattern_name = "lower_highs"
        signal = ToolSignal.BEARISH
        interpretation = (
            "Lower highs pattern: 3 consecutive lower local highs detected in last 20 bars. "
            "Suggests distribution and bearish bias."
        )
    else:
        pattern_name = "none"
        signal = ToolSignal.NEUTRAL
        interpretation = (
            "No recognizable chart pattern detected in the last 20 bars. "
            "Neutral pattern signal."
        )

    return ToolOutput(
        tool_name="pattern_recognition",
        signal=signal,
        reliability=Reliability.LOW,
        interpretation=interpretation,
        raw_values={"pattern": pattern_name},
    )
