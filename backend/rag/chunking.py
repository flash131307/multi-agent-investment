"""
Document chunking utilities for RAG pipeline.
Splits documents into optimal chunks for embedding and retrieval.
"""
from typing import List, Dict, Any, Optional
import tiktoken
import logging

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Handles text chunking for embeddings."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[str]:
        """
        Split text into overlapping chunks by tokens.

        Args:
            text: Text to chunk
            chunk_size: Override default chunk size
            overlap: Override default overlap

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap

        # Encode text to tokens
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        if total_tokens <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < total_tokens:
            # Get chunk of tokens
            end = min(start + chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move start position with overlap
            if end >= total_tokens:
                break
            start = end - overlap

        logger.info(f"✅ Chunked text into {len(chunks)} chunks ({total_tokens} tokens total)")
        return chunks

    def chunk_by_section(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Chunk a document that's already divided into sections.

        Args:
            sections: Dict mapping section names to their content

        Returns:
            List of dicts with chunk data including section metadata
        """
        all_chunks = []

        for section_name, section_text in sections.items():
            # Chunk this section
            chunks = self.chunk_text(section_text)

            # Add metadata to each chunk
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "section": section_name,
                    "chunk_index": i,
                    "total_chunks_in_section": len(chunks),
                    "token_count": self.count_tokens(chunk)
                })

        logger.info(f"✅ Created {len(all_chunks)} chunks from {len(sections)} sections")
        return all_chunks

    def create_chunk_metadata(
        self,
        chunk: str,
        source: str,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        date: Optional[str] = None,
        section: Optional[str] = None,
        **extra_metadata
    ) -> Dict[str, Any]:
        """
        Create metadata dict for a document chunk.

        Args:
            chunk: The text chunk
            source: Source of the document ("edgar", "news", "yfinance", etc.)
            ticker: Stock ticker (if applicable)
            doc_type: Type of document ("10-K", "news", "analysis", etc.)
            date: Document date (ISO format)
            section: Section name (if from structured document)
            **extra_metadata: Additional metadata fields

        Returns:
            Metadata dict for the chunk
        """
        metadata = {
            "source": source,
            "token_count": self.count_tokens(chunk),
            "chunk_length": len(chunk)
        }

        if ticker:
            metadata["ticker"] = ticker.upper()
        if doc_type:
            metadata["doc_type"] = doc_type
        if date:
            metadata["date"] = date
        if section:
            metadata["section"] = section

        # Add any extra metadata
        metadata.update(extra_metadata)

        return metadata

    def chunk_document(
        self,
        text: str,
        source: str,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document and create metadata for each chunk.

        Args:
            text: Document text
            source: Document source
            ticker: Stock ticker
            doc_type: Document type
            date: Document date

        Returns:
            List of dicts with 'text' and 'metadata' keys
        """
        chunks = self.chunk_text(text)

        chunk_docs = []
        for i, chunk in enumerate(chunks):
            metadata = self.create_chunk_metadata(
                chunk=chunk,
                source=source,
                ticker=ticker,
                doc_type=doc_type,
                date=date,
                chunk_index=i,
                total_chunks=len(chunks)
            )

            chunk_docs.append({
                "text": chunk,
                "metadata": metadata
            })

        return chunk_docs

    def chunk_edgar_filing(
        self,
        filing_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Chunk an EDGAR filing with section awareness.

        Args:
            filing_data: Dict from EDGARScraper.get_filing_summary()

        Returns:
            List of chunk dicts with text and metadata
        """
        ticker = filing_data.get("ticker", "UNKNOWN")
        filing_type = filing_data.get("filing_type", "UNKNOWN")
        filing_date = filing_data.get("filing_date", "")
        sections = filing_data.get("sections", {})

        # Chunk by section
        section_chunks = self.chunk_by_section(sections)

        # Add filing metadata to each chunk
        chunk_docs = []
        for chunk_data in section_chunks:
            metadata = self.create_chunk_metadata(
                chunk=chunk_data["text"],
                source="edgar",
                ticker=ticker,
                doc_type=filing_type,
                date=filing_date,
                section=chunk_data["section"],
                chunk_index=chunk_data["chunk_index"]
            )

            chunk_docs.append({
                "text": chunk_data["text"],
                "metadata": metadata
            })

        logger.info(f"✅ Created {len(chunk_docs)} chunks from {filing_type} for {ticker}")
        return chunk_docs


# Singleton instance
document_chunker = DocumentChunker(chunk_size=512, overlap=50)
