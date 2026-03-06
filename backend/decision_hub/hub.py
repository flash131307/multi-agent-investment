"""
Decision Hub orchestrator.

Fuses 1–3 agent signals into a DecisionResult using:
    1. Consistency scoring (direction gate + strength/confidence spread)
    2. Dynamic weight allocation (base × regime × confidence → normalize)
    3. Weighted aggregation (score → direction + confidence)

Handles graceful degradation:
    - 3 agents: normal operation
    - 2 agents: confidence ×0.8 warning
    - 1 agent: confidence ×0.5 strong warning
    - 0 agents: raises ValueError (caller should return 503)
"""

from backend.models.signals import AgentSignal
from backend.models.technical import MarketRegime
from backend.models.decision import DecisionResult

from .consistency import compute_consistency
from .weighting import compute_weights
from .aggregation import aggregate

_DEGRADATION_WARNINGS = {
    2: "Only 2 of 3 agents responded. Confidence dampened by ×0.8.",
    1: "Only 1 of 3 agents responded. Confidence dampened by ×0.5. Decision unreliable.",
}

_DEGRADATION_MULTIPLIERS = {3: 1.0, 2: 0.8, 1: 0.5}


class DecisionHub:
    """Pure mathematical signal fusion engine."""

    def fuse(
        self,
        signals: list[AgentSignal],
        regime: MarketRegime | None = None,
    ) -> DecisionResult:
        """
        Fuse agent signals into a final DecisionResult.

        Args:
            signals: 1–3 AgentSignal objects from active agents.
            regime: Market regime from TechnicalAgent (optional — used for weighting).

        Returns:
            DecisionResult with direction, confidence, weights, reasoning placeholder.

        Raises:
            ValueError: If signals is empty (caller should respond with 503).
        """
        if not signals:
            raise ValueError("Cannot fuse zero signals. Return a 503 to the caller.")

        warnings: list[str] = []
        n = len(signals)

        if n > 3:
            raise ValueError(f"Maximum 3 signals supported, got {n}.")

        if n < 3 and n in _DEGRADATION_WARNINGS:
            warnings.append(_DEGRADATION_WARNINGS[n])

        # --- Step 1: Consistency ---
        consistency = compute_consistency(signals)

        # --- Step 2: Weights ---
        weights = compute_weights(signals, regime)

        # --- Step 3: Aggregation ---
        direction, confidence, score = aggregate(signals, weights, consistency)

        # --- Step 4: Degradation dampening ---
        degradation = _DEGRADATION_MULTIPLIERS.get(n, 1.0)
        confidence = min(1.0, confidence * degradation)

        return DecisionResult(
            direction=direction,
            confidence=confidence,
            consistency=consistency,
            weights=weights,
            signals=signals,
            aggregated_score=score,
            reasoning="",   # Populated by reasoning.py post-decision
            warnings=warnings,
        )
