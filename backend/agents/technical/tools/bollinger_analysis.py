"""
Bollinger Bands signal computation.
"""
import pandas as pd
import ta

from backend.models.technical import Reliability, ToolOutput, ToolSignal

_MIN_ROWS = 60


def compute_bollinger_signal(df: pd.DataFrame) -> ToolOutput:
    """
    Compute Bollinger Bands (20-period, 2 std) signal.

    Price position logic:
    - Below lower band → BULLISH (potential reversal)
    - Above upper band → BEARISH (potential reversal)
    - Within 10% of band width from middle → NEUTRAL
    - else             → NEUTRAL

    Reliability is always MEDIUM (Bollinger is supplementary).

    Args:
        df: OHLCV DataFrame with at least 60 rows.

    Returns:
        ToolOutput with raw_values={"upper": float, "lower": float, "middle": float, "price": float}.

    Raises:
        ValueError: If DataFrame has fewer than 60 rows.
    """
    if len(df) < _MIN_ROWS:
        raise ValueError(
            f"Insufficient data: need at least {_MIN_ROWS} rows, got {len(df)}"
        )

    close = df["Close"]
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)

    upper = bb.bollinger_hband()
    lower = bb.bollinger_lband()
    middle = bb.bollinger_mavg()

    valid = upper.notna() & lower.notna() & middle.notna()
    if not valid.any():
        raise ValueError("Bollinger Bands produced all NaN values — insufficient data.")

    last_idx = valid[::-1].idxmax()
    upper_val = float(upper[last_idx])
    lower_val = float(lower[last_idx])
    middle_val = float(middle[last_idx])
    price_val = float(close[last_idx])

    band_width = upper_val - lower_val
    near_middle_threshold = 0.10 * band_width if band_width > 0 else 0.0

    if price_val < lower_val:
        signal = ToolSignal.BULLISH
        interpretation = (
            f"Price ({price_val:.2f}) is below lower Bollinger Band ({lower_val:.2f}). "
            f"Potential mean-reversion bullish setup."
        )
    elif price_val > upper_val:
        signal = ToolSignal.BEARISH
        interpretation = (
            f"Price ({price_val:.2f}) is above upper Bollinger Band ({upper_val:.2f}). "
            f"Potential mean-reversion bearish setup."
        )
    elif abs(price_val - middle_val) <= near_middle_threshold:
        signal = ToolSignal.NEUTRAL
        interpretation = (
            f"Price ({price_val:.2f}) near middle band ({middle_val:.2f}). "
            f"No clear directional signal from Bollinger Bands."
        )
    else:
        signal = ToolSignal.NEUTRAL
        interpretation = (
            f"Price ({price_val:.2f}) within bands (lower={lower_val:.2f}, upper={upper_val:.2f}). "
            f"No extreme reading."
        )

    return ToolOutput(
        tool_name="bollinger_analysis",
        signal=signal,
        reliability=Reliability.MEDIUM,
        interpretation=interpretation,
        raw_values={
            "upper": upper_val,
            "lower": lower_val,
            "middle": middle_val,
            "price": price_val,
        },
    )
