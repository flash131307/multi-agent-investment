"""
SEC EDGAR 10-K filing loader using edgartools.
Fetches and extracts key sections from annual reports.
"""
import logging

logger = logging.getLogger(__name__)

# Section labels to search for in 10-K filings
_SECTION_NAMES = {
    "item1": ["item 1", "item1", "business"],
    "item7": ["item 7", "item7", "management", "md&a", "discussion and analysis"],
    "item8": ["item 8", "item8", "financial statements"],
}


def load_10k_sections(ticker: str, user_agent: str) -> dict[str, str]:
    """
    Fetch the most recent 10-K filing for a ticker and extract key sections.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        user_agent: User-agent string required by SEC EDGAR (e.g., "Name email@example.com").

    Returns:
        Dict with keys "item1", "item7", "item8" mapping to extracted text.
        Missing sections are represented as empty strings.

    Raises:
        ImportError: If edgartools is not installed.
        ValueError: If no 10-K filing is found for the ticker.
    """
    try:
        from edgar import Company, set_identity  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "edgartools is required for SEC EDGAR access. "
            "Install it with: pip install edgartools"
        ) from exc

    set_identity(user_agent)

    company = Company(ticker)

    try:
        filings = company.get_filings(form="10-K")
        if filings is None or len(filings) == 0:
            raise ValueError(f"No 10-K filings found for ticker '{ticker}'")

        filing = filings.latest(1)
        if filing is None:
            raise ValueError(f"No 10-K filings found for ticker '{ticker}'")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            f"Failed to retrieve 10-K filing for '{ticker}': {exc}"
        ) from exc

    sections: dict[str, str] = {"item1": "", "item7": "", "item8": ""}

    try:
        ten_k = filing.obj()
        sections = _extract_sections_from_obj(ten_k)
    except Exception as exc:
        logger.warning(
            "Could not parse 10-K object for '%s' via filing.obj(): %s. "
            "Falling back to stub extraction.",
            ticker,
            exc,
        )
        sections = {"item1": "", "item7": "", "item8": ""}

    return sections


def _extract_sections_from_obj(ten_k_obj: object) -> dict[str, str]:
    """
    Attempt to extract text sections from an edgartools filing object.

    Falls back gracefully if the expected attributes don't exist.
    """
    sections: dict[str, str] = {"item1": "", "item7": "", "item8": ""}

    # edgartools TenK objects often expose sections as attributes
    section_attr_map = {
        "item1": ["item1", "Item1", "business"],
        "item7": ["item7", "Item7", "mda"],
        "item8": ["item8", "Item8", "financial_statements"],
    }

    for key, attr_names in section_attr_map.items():
        for attr in attr_names:
            try:
                section = getattr(ten_k_obj, attr, None)
                if section is not None:
                    text = _coerce_to_str(section)
                    if text:
                        sections[key] = text
                        break
            except Exception:
                continue

    # If still empty, try iterating over items if the object is dict-like
    if all(v == "" for v in sections.values()):
        try:
            items = dict(ten_k_obj)  # type: ignore
            for raw_key, value in items.items():
                normalized = str(raw_key).lower().strip()
                for section_key, labels in _SECTION_NAMES.items():
                    if any(label in normalized for label in labels):
                        if sections[section_key] == "":
                            sections[section_key] = _coerce_to_str(value)
        except Exception:
            pass

    return sections


def _coerce_to_str(value: object) -> str:
    """Convert various edgartools section types to plain text."""
    if isinstance(value, str):
        return value.strip()
    try:
        # Some edgartools objects have a .text property
        text = getattr(value, "text", None)
        if isinstance(text, str):
            return text.strip()
    except Exception:
        pass
    try:
        return str(value).strip()
    except Exception:
        return ""
