"""
Orchestrator runner — parallel agent execution + Decision Hub fusion.

Flow:
    POST /api/research/analyze {ticker}
      → ticker_resolver.resolve(ticker)
      → asyncio.gather(TechnicalAgent, SentimentAgent, FundamentalAgent)
      → collect valid signals (None / Exception → error entry)
      → DecisionHub.fuse(signals)
      → reasoning.generate(result)
      → DecisionResult (with reasoning filled in)

Degradation:
    3 agents → normal
    2 agents → hub adds ×0.8 warning
    1 agent  → hub adds ×0.5 warning
    0 agents → raises RuntimeError (caller returns 503)
"""

import asyncio
import logging
from typing import Optional

from backend.models.signals import AgentSignal
from backend.models.decision import DecisionResult
from backend.decision_hub.hub import DecisionHub
from backend.decision_hub.reasoning import generate_reasoning
from backend.agents.technical.agent import TechnicalAgent
from backend.agents.sentiment.agent import SentimentAgent
from backend.agents.fundamental.agent import FundamentalAgent

logger = logging.getLogger(__name__)

_hub = DecisionHub()
_AGENT_NAMES = ("technical", "sentiment", "fundamental")


async def run_agents(
    ticker: str,
    *,
    technical_timeout: float = 30.0,
    sentiment_timeout: float = 20.0,
    fundamental_timeout: float = 60.0,
) -> tuple[list[AgentSignal], dict[str, str]]:
    """
    Run all three agents in parallel via asyncio.gather.

    Returns:
        (signals, errors) where:
          - signals: list of valid AgentSignal from successful agents
          - errors: dict of agent_name → error description for failed agents
    """
    agents = [
        TechnicalAgent(timeout=technical_timeout),
        SentimentAgent(timeout=sentiment_timeout),
        FundamentalAgent(timeout=fundamental_timeout),
    ]

    results = await asyncio.gather(
        *[agent.run(ticker) for agent in agents],
        return_exceptions=True,
    )

    signals: list[AgentSignal] = []
    errors: dict[str, str] = {}

    for name, result in zip(_AGENT_NAMES, results):
        if isinstance(result, BaseException):
            logger.error("Agent '%s' raised exception for %s: %s", name, ticker, result)
            errors[name] = str(result)
        elif result is None:
            logger.warning("Agent '%s' returned None for %s", name, ticker)
            errors[name] = "Agent timed out or returned no signal."
        else:
            signals.append(result)

    return signals, errors


async def analyze(
    ticker: str,
    *,
    technical_timeout: float = 30.0,
    sentiment_timeout: float = 20.0,
    fundamental_timeout: float = 60.0,
) -> tuple[DecisionResult, dict[str, str]]:
    """
    Full analysis pipeline for a resolved ticker symbol.

    Args:
        ticker: Validated uppercase ticker symbol.
        *_timeout: Per-agent timeout in seconds.

    Returns:
        (DecisionResult with reasoning, agent_errors dict)

    Raises:
        RuntimeError: When zero agents succeed (caller should return 503).
    """
    signals, errors = await run_agents(
        ticker,
        technical_timeout=technical_timeout,
        sentiment_timeout=sentiment_timeout,
        fundamental_timeout=fundamental_timeout,
    )

    if not signals:
        raise RuntimeError(
            f"All agents failed for ticker '{ticker}'. Cannot produce a decision."
        )

    # Fuse signals (hub handles 1/2/3 agent degradation internally)
    result = _hub.fuse(signals)

    # Generate reasoning via LLM (non-blocking fallback on failure)
    try:
        reasoning = generate_reasoning(result)
    except Exception as exc:
        logger.warning("Reasoning generation failed, using fallback: %s", exc)
        reasoning = result.reasoning  # hub sets "" — fallback_reasoning() in reasoning.py

    # DecisionResult is frozen — create updated copy with reasoning filled in
    result = result.model_copy(update={"reasoning": reasoning})

    return result, errors
