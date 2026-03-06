"""Decision Hub package — pure mathematical signal fusion engine."""

from .consistency import compute_consistency
from .weighting import compute_weights
from .aggregation import aggregate
from .hub import DecisionHub

__all__ = ["compute_consistency", "compute_weights", "aggregate", "DecisionHub"]
