"""
Layer 1 — Article filtering: relevance, deduplication, and limit.
"""
import logging

from backend.models.sentiment import NewsArticle

logger = logging.getLogger(__name__)

_MAX_ARTICLES = 25
_DEDUP_THRESHOLD = 0.8  # Jaccard similarity above this → duplicate

# Source credibility weights
_SOURCE_WEIGHTS: dict[str, float] = {
    "reuters": 1.2,
    "bloomberg": 1.0,
}
_DEFAULT_SOURCE_WEIGHT = 0.7


def get_source_weight(source: str) -> float:
    """
    Return a credibility multiplier for a news source.

    Known sources: reuters=1.2, bloomberg=1.0.
    All others: 0.7.
    """
    return _SOURCE_WEIGHTS.get(source.lower(), _DEFAULT_SOURCE_WEIGHT)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    """Split text into lowercase word tokens."""
    return set(text.lower().split())


def _jaccard_similarity(a: str, b: str) -> float:
    """Return token-overlap Jaccard similarity between two strings."""
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    union = tokens_a | tokens_b
    common = tokens_a & tokens_b
    return len(common) / len(union)


def _is_relevant(article: NewsArticle, ticker: str, company_name: str) -> bool:
    """Return True if the article mentions the ticker or company name."""
    ticker_lower = ticker.lower()
    company_lower = company_name.lower()
    combined = f"{article.headline} {article.summary}".lower()
    return ticker_lower in combined or (company_lower and company_lower in combined)


def _deduplicate(articles: list[NewsArticle]) -> list[NewsArticle]:
    """Remove near-duplicate articles based on headline Jaccard similarity."""
    kept: list[NewsArticle] = []
    for candidate in articles:
        is_duplicate = False
        for existing in kept:
            if _jaccard_similarity(candidate.headline, existing.headline) > _DEDUP_THRESHOLD:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(candidate)
    return kept


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_articles(
    articles: list[NewsArticle],
    ticker: str,
    company_name: str = "",
) -> list[NewsArticle]:
    """
    Three-step filter pipeline for news articles.

    Step 1 — Relevance: keep articles that mention the ticker or company.
              If none qualify, fall back to the full list.
    Step 2 — Deduplication: remove articles whose headline is >80% similar
              to an already-accepted article.
    Step 3 — Limit: keep at most 25 most-recent articles.

    Args:
        articles: Raw list of NewsArticle objects (any order).
        ticker: Ticker symbol used for relevance matching.
        company_name: Optional company name for additional matching.

    Returns:
        Filtered list of NewsArticle objects.
    """
    if not articles:
        return []

    # Step 1 — Relevance filter
    relevant = [a for a in articles if _is_relevant(a, ticker, company_name)]
    if not relevant:
        logger.debug(
            "No relevant articles found for %s; using all %d articles as fallback.",
            ticker,
            len(articles),
        )
        relevant = list(articles)

    # Step 2 — Deduplication
    deduplicated = _deduplicate(relevant)

    # Step 3 — Sort by recency and cap
    sorted_articles = sorted(deduplicated, key=lambda a: a.published_at, reverse=True)
    limited = sorted_articles[:_MAX_ARTICLES]

    logger.debug(
        "filter_articles: %d → %d relevant → %d deduped → %d final",
        len(articles),
        len(relevant),
        len(deduplicated),
        len(limited),
    )
    return limited
