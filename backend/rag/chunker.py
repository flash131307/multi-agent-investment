"""
Text chunking for RAG pipeline.
Supports llama_index SentenceWindowNodeParser with simple fallback.
"""
import logging
import re

logger = logging.getLogger(__name__)

_CHUNK_WORD_LIMIT = 200


def chunk_text(text: str, source_metadata: dict) -> list[dict]:
    """
    Split text into overlapping chunks suitable for embedding and retrieval.

    Args:
        text: Raw text to chunk.
        source_metadata: Metadata dict to attach to every chunk (e.g., ticker, section).

    Returns:
        List of dicts: {"text": str, "metadata": {**source_metadata, "chunk_id": int}}
    """
    if not text or not text.strip():
        return []

    chunks = _chunk_with_llama_index(text)
    if chunks is None:
        chunks = _simple_chunk(text)

    return [
        {"text": chunk, "metadata": {**source_metadata, "chunk_id": idx}}
        for idx, chunk in enumerate(chunks)
        if chunk.strip()
    ]


def _chunk_with_llama_index(text: str) -> list[str] | None:
    """
    Attempt chunking via llama_index SentenceWindowNodeParser.

    Returns list of strings on success, None if llama_index is unavailable.
    """
    try:
        from llama_index.core.node_parser import SentenceWindowNodeParser  # type: ignore
        from llama_index.core import Document  # type: ignore

        parser = SentenceWindowNodeParser.from_defaults(window_size=3)
        documents = [Document(text=text)]
        nodes = parser.get_nodes_from_documents(documents)
        return [node.get_content() for node in nodes if node.get_content().strip()]
    except ImportError:
        logger.warning(
            "llama_index not available; falling back to simple sentence chunking."
        )
        return None
    except Exception as exc:
        logger.warning(
            "llama_index chunking failed (%s); falling back to simple chunking.", exc
        )
        return None


def _simple_chunk(text: str) -> list[str]:
    """
    Fallback chunker: split by sentence boundary, group into ~200-word chunks.
    """
    # Split on ". " or end of string with uppercase start (sentence boundaries)
    raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    chunks: list[str] = []
    current_words: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_word_count + word_count > _CHUNK_WORD_LIMIT and current_words:
            chunks.append(" ".join(current_words))
            current_words = []
            current_word_count = 0

        current_words.append(sentence)
        current_word_count += word_count

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
