"""
FinBERT sentiment classification service (singleton, lazy-loaded).
"""
import logging
from typing import TYPE_CHECKING

from backend.models.sentiment import SentimentLabel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Maps FinBERT output label strings to our SentimentLabel enum
_LABEL_MAP: dict[str, SentimentLabel] = {
    "positive": SentimentLabel.POSITIVE,
    "negative": SentimentLabel.NEGATIVE,
    "neutral": SentimentLabel.NEUTRAL,
}

_BATCH_SIZE = 32


class FinBERTService:
    """
    Wraps ProsusAI/finbert for financial sentiment classification.

    The model is lazy-loaded on the first call to classify().
    """

    def __init__(self) -> None:
        self._pipeline = None  # loaded lazily
        self._device: str | None = None
        self._transformers_available: bool = self._check_transformers()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _check_transformers() -> bool:
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_model(self) -> None:
        """Load the FinBERT pipeline. Called once on first classify()."""
        from transformers import pipeline  # type: ignore[import]

        from backend.config.settings import settings

        device_setting = settings.finbert_device
        # Map device string to integer index expected by HF pipeline
        if device_setting == "cpu":
            device = -1
        else:
            # e.g. "cuda", "cuda:0", "mps"
            try:
                import torch
                if device_setting.startswith("cuda"):
                    device = int(device_setting.split(":")[-1]) if ":" in device_setting else 0
                else:
                    device = device_setting  # pass string for mps, etc.
            except ImportError:
                device = -1

        self._device = device_setting
        model_name = settings.finbert_model_name
        logger.info("Loading FinBERT model '%s' on device '%s'", model_name, device_setting)
        self._pipeline = pipeline(
            "text-classification",
            model=model_name,
            device=device,
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT model loaded successfully.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if transformers and torch are installed."""
        return self._transformers_available

    def classify(self, texts: list[str]) -> list[tuple[SentimentLabel, float]]:
        """
        Classify a list of texts using FinBERT.

        Args:
            texts: List of financial text snippets.

        Returns:
            List of (SentimentLabel, confidence) tuples in the same order.
        """
        if not self._transformers_available:
            raise RuntimeError("transformers/torch not installed; FinBERT unavailable.")

        if self._pipeline is None:
            self._load_model()

        results: list[tuple[SentimentLabel, float]] = []
        # Process in batches
        for batch_start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[batch_start : batch_start + _BATCH_SIZE]
            raw_outputs = self._pipeline(batch)  # type: ignore[operator]
            for output in raw_outputs:
                raw_label: str = output["label"].lower()
                confidence: float = float(output["score"])
                label = _LABEL_MAP.get(raw_label, SentimentLabel.NEUTRAL)
                results.append((label, confidence))

        return results


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_SINGLETON: FinBERTService | None = None


def get_finbert_service() -> FinBERTService:
    """Return the module-level FinBERTService singleton (created on first call)."""
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = FinBERTService()
    return _SINGLETON
