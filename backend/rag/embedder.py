"""
Text embedding using sentence_transformers with zero-vector fallback.
"""
import logging

logger = logging.getLogger(__name__)

_DEFAULT_DIMENSION = 768


class Embedder:
    """
    Wraps sentence_transformers for text embedding.
    Falls back to zero-vectors when sentence_transformers is unavailable.
    """

    def __init__(self, model_name: str, device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dimension = _DEFAULT_DIMENSION
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load sentence_transformers model."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name, device=self.device)
            # Infer dimension from a test encode
            test_embedding = self._model.encode(["test"], convert_to_numpy=True)
            self._dimension = int(test_embedding.shape[1])
            logger.info(
                "Loaded sentence_transformers model '%s' (dim=%d)",
                self.model_name,
                self._dimension,
            )
        except ImportError:
            logger.warning(
                "sentence_transformers not available; using zero-vector embeddings "
                "(dim=%d). Install with: pip install sentence-transformers",
                _DEFAULT_DIMENSION,
            )
            self._model = None
            self._dimension = _DEFAULT_DIMENSION
        except Exception as exc:
            logger.warning(
                "Failed to load model '%s': %s. Using zero-vector fallback.",
                self.model_name,
                exc,
            )
            self._model = None
            self._dimension = _DEFAULT_DIMENSION

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts.

        Args:
            texts: Input strings to embed.

        Returns:
            List of float vectors, one per input text.
        """
        if not texts:
            return []

        if self._model is None:
            return [[0.0] * self._dimension for _ in texts]

        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return [list(map(float, vec)) for vec in embeddings]
        except Exception as exc:
            logger.error("Embedding failed: %s. Returning zero vectors.", exc)
            return [[0.0] * self._dimension for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string.

        Args:
            text: Query string.

        Returns:
            Float vector of length self.dimension.
        """
        results = self.embed([text])
        return results[0] if results else [0.0] * self._dimension
