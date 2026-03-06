"""
Company profile tool: fetches data from yfinance and optionally augments
with RAG-retrieved context.
"""
import logging
from typing import TYPE_CHECKING

import yfinance as yf

from backend.models.fundamental import CompanyProfile

if TYPE_CHECKING:
    from backend.rag.retriever import HybridRetriever

logger = logging.getLogger(__name__)


def build_company_profile(
    ticker: str,
    retriever: "HybridRetriever | None" = None,
) -> CompanyProfile:
    """
    Build a CompanyProfile for a given ticker using yfinance data.

    Optionally augments the business description with passages retrieved
    from the RAG index.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        retriever: Optional HybridRetriever to augment description via RAG.

    Returns:
        A frozen CompanyProfile Pydantic model.
    """
    info: dict = {}
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
    except Exception as exc:
        logger.error("Failed to fetch yfinance info for '%s': %s", ticker, exc)

    name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector") or "Unknown"
    industry = info.get("industry") or "Unknown"
    description = info.get("longBusinessSummary") or ""
    market_cap = _safe_float(info.get("marketCap"))
    pe_ratio = _safe_float(info.get("trailingPE"))
    revenue_growth = _safe_float(info.get("revenueGrowth"))

    # Augment description with RAG passages if retriever is provided
    if retriever is not None and retriever:
        try:
            rag_results = retriever.retrieve(
                "business overview competitive advantage", top_k=3
            )
            if rag_results:
                rag_texts = [r["text"] for r in rag_results if r.get("text")]
                if rag_texts:
                    rag_context = " | ".join(rag_texts[:3])
                    if description:
                        description = f"{description}\n\n[RAG Context]: {rag_context}"
                    else:
                        description = f"[RAG Context]: {rag_context}"
        except Exception as exc:
            logger.warning(
                "RAG augmentation failed for '%s': %s", ticker, exc
            )

    return CompanyProfile(
        ticker=ticker.upper(),
        name=name,
        sector=sector,
        industry=industry,
        description=description,
        market_cap=market_cap,
        pe_ratio=pe_ratio,
        revenue_growth=revenue_growth,
    )


def _safe_float(value: object) -> float | None:
    """Return float(value) or None if conversion fails."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
