"""
Step 1 of Plan-and-Solve: build the company profile.
"""
from typing import TYPE_CHECKING

from backend.models.fundamental import CompanyProfile
from backend.agents.fundamental.tools.company_profile import build_company_profile

if TYPE_CHECKING:
    from backend.rag.retriever import HybridRetriever


def build_profile(
    ticker: str,
    retriever: "HybridRetriever | None",
) -> CompanyProfile:
    """
    Build a CompanyProfile for the given ticker (Plan-and-Solve Step 1).

    Args:
        ticker: Stock ticker symbol.
        retriever: Optional HybridRetriever for RAG augmentation.

    Returns:
        Frozen CompanyProfile Pydantic model.
    """
    return build_company_profile(ticker, retriever)
