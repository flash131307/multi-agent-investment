"""
Reasoning generator for the Decision Hub.

Translates the mathematical DecisionResult into human-readable text
using an LLM. The reasoning NEVER modifies the decision — it only
explains it. If the LLM fails, a deterministic fallback is returned.
"""

from backend.models.decision import DecisionResult


def generate_reasoning(result: DecisionResult) -> str:
    """
    Generate a human-readable explanation of the DecisionResult.

    Attempts an LLM call; falls back to a deterministic summary on failure.
    This function does NOT modify the result — it returns a new string only.

    Args:
        result: The finalized DecisionResult from DecisionHub.fuse().

    Returns:
        Human-readable reasoning string.
    """
    try:
        return _llm_reasoning(result)
    except Exception:
        return _fallback_reasoning(result)


def _llm_reasoning(result: DecisionResult) -> str:
    """Attempt LLM-based reasoning generation."""
    from openai import OpenAI
    from backend.config.settings import settings

    client = OpenAI(api_key=settings.openai_api_key)

    signal_lines = "\n".join(
        f"  - {s.agent_name}: {s.direction.value}/{s.strength.value} "
        f"(confidence={s.confidence:.2f}) — {s.reasoning}"
        for s in result.signals
    )
    weight_lines = "\n".join(
        f"  - {w.agent_name}: {w.final_weight:.3f}"
        for w in result.weights
    )

    prompt = f"""You are explaining an investment signal fusion result to a portfolio manager.
The decision was computed mathematically — do NOT change it. Only explain it clearly.

Decision: {result.direction.value}
Confidence: {result.confidence:.2f}
Risk Mode: {result.consistency.risk_mode.value}
Consistency Score: {result.consistency.final_consistency:.3f}
Aggregated Score: {result.aggregated_score:.3f}

Agent Signals:
{signal_lines}

Final Weights:
{weight_lines}

Write 2–3 concise sentences explaining why this decision was reached and what drove the weighting.
Do not include numbers directly — describe the qualitative picture."""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _fallback_reasoning(result: DecisionResult) -> str:
    """Deterministic fallback when LLM is unavailable."""
    risk_desc = {
        "NORMAL": "high consistency",
        "CAUTIOUS": "moderate consistency",
        "RISK": "low consistency",
    }[result.consistency.risk_mode.value]

    dominant = max(result.weights, key=lambda w: w.final_weight)
    signal_map = {s.agent_name: s for s in result.signals}
    dominant_signal = signal_map.get(dominant.agent_name)
    dominant_desc = (
        f"{dominant.agent_name} signal ({dominant_signal.direction.value}/"
        f"{dominant_signal.strength.value})"
        if dominant_signal
        else dominant.agent_name
    )

    return (
        f"The {result.direction.value} recommendation was derived from {len(result.signals)} "
        f"agent signal(s) with {risk_desc} (score: {result.aggregated_score:+.3f}). "
        f"The most influential factor was the {dominant_desc} "
        f"with a weight of {dominant.final_weight:.1%}."
    )
