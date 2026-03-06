"""
RAG search tool: thin wrapper around HybridRetriever.retrieve().
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.rag.retriever import HybridRetriever

logger = logging.getLogger(__name__)


def rag_search(
    query: str,
    retriever: "HybridRetriever",
    top_k: int = 5,
) -> list[str]:
    """
    Retrieve relevant document passages for a query.

    Args:
        query: Natural language query string.
        retriever: Initialized HybridRetriever instance.
        top_k: Number of passages to return.

    Returns:
        List of text strings (passage content only, no metadata).
    """
    try:
        results = retriever.retrieve(query, top_k=top_k)
        return [r["text"] for r in results if r.get("text")]
    except Exception as exc:
        logger.error("RAG search failed for query '%s': %s", query, exc)
        return []
