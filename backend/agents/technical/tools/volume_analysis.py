"""
Volume-based signal computation with price-volume confirmation.
"""
import pandas as pd

from backend.models.technical import Reliability, ToolOutput, ToolSignal

_MIN_ROWS = 60
_AVG_WINDOW = 20
_HIGH_VOL_RATIO = 1.5
_LOW_VOL_RATIO = 0.8


def compute_volume_signal(df: pd.DataFrame) -> ToolOutput:
    """
    Compare current volume to 20-day average and confirm price direction.

    Rules:
    - Price UP   + volume > 1.5× avg → BULLISH (HIGH)
    - Price DOWN + volume > 1.5× avg → BEARISH (HIGH)
    - Price UP   + volume < 0.8× avg → BULLISH (LOW, divergence warning)
    - Price DOWN + volume < 0.8× avg → BEARISH (LOW, divergence warning)
    - else                            → NEUTRAL (MEDIUM)

    Args:
        df: OHLCV DataFrame with at least 60 rows and Volume column.

    Returns:
        ToolOutput with raw_values={"volume_ratio": float, "price_change_pct": float}.

    Raises:
        ValueError: If DataFrame has fewer than 60 rows or Volume column is missing.
    """
    if "Volume" not in df.columns:
        raise ValueError("DataFrame missing required 'Volume' column.")

    if len(df) < _MIN_ROWS:
        raise ValueError(
            f"Insufficient data: need at least {_MIN_ROWS} rows, got {len(df)}"
        )

    close = df["Close"]
    volume = df["Volume"]

    # Average volume over last 20 periods
    avg_volume = volume.rolling(window=_AVG_WINDOW).mean()

    # Last valid values
    valid = close.notna() & volume.notna() & avg_volume.notna()
    if not valid.any():
        raise ValueError("Volume analysis produced all NaN values.")

    # Use last two valid rows for price change
    valid_indices = close[valid].index
    if len(valid_indices) < 2:
        raise ValueError("Need at least 2 valid rows to compute price change.")

    last_idx = valid_indices[-1]
    prev_idx = valid_indices[-2]

    current_price = float(close[last_idx])
    previous_price = float(close[prev_idx])
    current_volume = float(volume[last_idx])
    avg_vol_val = float(avg_volume[last_idx])

    price_change_pct = ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0.0
    volume_ratio = current_volume / avg_vol_val if avg_vol_val > 0 else 1.0

    price_up = price_change_pct > 0

    if volume_ratio > _HIGH_VOL_RATIO:
        if price_up:
            signal = ToolSignal.BULLISH
            reliability = Reliability.HIGH
            interpretation = (
                f"Price +{price_change_pct:.2f}% with volume {volume_ratio:.1f}× avg. "
                f"High-volume bullish confirmation."
            )
        else:
            signal = ToolSignal.BEARISH
            reliability = Reliability.HIGH
            interpretation = (
                f"Price {price_change_pct:.2f}% with volume {volume_ratio:.1f}× avg. "
                f"High-volume bearish confirmation."
            )
    elif volume_ratio < _LOW_VOL_RATIO:
        if price_up:
            signal = ToolSignal.BULLISH
            reliability = Reliability.LOW
            interpretation = (
                f"Price +{price_change_pct:.2f}% but volume only {volume_ratio:.1f}× avg. "
                f"Weak bullish move — low-volume divergence warning."
            )
        else:
            signal = ToolSignal.BEARISH
            reliability = Reliability.LOW
            interpretation = (
                f"Price {price_change_pct:.2f}% but volume only {volume_ratio:.1f}× avg. "
                f"Weak bearish move — low-volume divergence warning."
            )
    else:
        signal = ToolSignal.NEUTRAL
        reliability = Reliability.MEDIUM
        interpretation = (
            f"Volume ratio {volume_ratio:.1f}× avg (between {_LOW_VOL_RATIO}× and {_HIGH_VOL_RATIO}×). "
            f"No exceptional volume activity."
        )

    return ToolOutput(
        tool_name="volume_analysis",
        signal=signal,
        reliability=reliability,
        interpretation=interpretation,
        raw_values={
            "volume_ratio": volume_ratio,
            "price_change_pct": price_change_pct,
        },
    )
