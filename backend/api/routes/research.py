"""
Research API endpoint — single POST /api/research/analyze.
"""
import logging

from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from backend.models.api import (
    AnalysisRequest,
    AnalysisResponse,
    ErrorResponse,
)
from backend.services.ticker_resolver import ticker_resolver
from backend.orchestrator.runner import analyze

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/research",
    tags=["research"],
    responses={
        503: {"model": ErrorResponse, "description": "All agents unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a stock ticker",
    description=(
        "Run three analysis agents (Technical, Sentiment, Fundamental) in parallel, "
        "fuse their signals via the Decision Hub, and return a structured investment decision."
    ),
    responses={
        200: {"description": "Decision produced successfully", "model": AnalysisResponse},
        400: {"description": "Invalid ticker", "model": ErrorResponse},
        503: {"description": "All agents failed — no decision possible", "model": ErrorResponse},
    },
)
async def analyze_ticker(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a stock and return a BUY / NEUTRAL / SELL decision.

    Steps:
    1. Resolve ticker symbol via TickerResolver.
    2. Run TechnicalAgent, SentimentAgent, FundamentalAgent in parallel.
    3. Fuse agent signals through the Decision Hub.
    4. Generate human-readable reasoning.
    5. Return AnalysisResponse with decision + per-agent signals.
    """
    raw_ticker = request.ticker.strip().upper()
    logger.info("Received analysis request for ticker: %s", raw_ticker)

    # --- Step 1: Resolve ticker ---
    try:
        resolved = await ticker_resolver.resolve(raw_ticker)
    except Exception as exc:
        logger.error("Ticker resolution error for '%s': %s", raw_ticker, exc)
        resolved = None

    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve ticker '{raw_ticker}'. Please provide a valid stock symbol.",
        )

    logger.info("Resolved '%s' → '%s'", raw_ticker, resolved)

    # --- Steps 2-4: Run agents + fuse ---
    try:
        from backend.config.settings import settings
        result, agent_errors = await analyze(
            resolved,
            technical_timeout=float(settings.agent_timeout_technical),
            sentiment_timeout=float(settings.agent_timeout_sentiment),
            fundamental_timeout=float(settings.agent_timeout_fundamental),
        )
    except RuntimeError as exc:
        # All agents failed
        logger.error("All agents failed for '%s': %s", resolved, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error analyzing '%s': %s", resolved, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )

    # --- Step 5: Build response ---
    response = AnalysisResponse.from_decision_result(
        ticker=resolved,
        result=result,
        agent_errors=agent_errors,
    )

    logger.info(
        "Analysis complete for '%s': %s (confidence=%.2f, agents=%d/%d)",
        resolved,
        result.direction.value,
        result.confidence,
        len(result.signals),
        3,
    )

    return response


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Research API health check",
    tags=["health"],
)
async def health_check():
    """Check if the research API is available."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "research-api",
    }
