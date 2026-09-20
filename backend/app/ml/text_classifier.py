"""
Text classifier (transformer-backed) for dark pattern categories.

Two implementations:

* `MockTextClassifier`        – lexical heuristic scoring; no model download.
* `TransformerTextClassifier` – wraps a HuggingFace sequence-classification
                                model such as a fine-tuned DeBERTa-v3 or
                                MiniLM. Loaded lazily only when AI_MODE=local.

Both expose `classify(sentences) -> list[dict(pattern, score)]`.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from app.ml.patterns import PATTERNS

logger = logging.getLogger(__name__)

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

# Lightweight lexical cues (per pattern) used by the mock classifier.
_CUES: Dict[str, List[str]] = {
    "fake_scarcity": ["left", "stock", "remaining", "gone", "selling", "last"],
    "urgency": ["now", "hurry", "soon", "today", "expire", "limited", "quick", "fast", "miss"],
    "confirmshaming": ["don't want", "rather", "no thanks", "prefer to pay", "hate"],
    "hidden_charges": ["fee", "charge", "surcharge", "additional", "extra"],
    "preselected_addons": ["protect", "warranty", "insurance", "add", "premium", "priority"],
    "misleading_discount": ["off", "save", "was", "discount", "deal", "mrp", "regular"],
    "forced_continuity": ["trial", "renew", "subscription", "recurring", "charged", "cancel"],
    "social_pressure": ["people", "viewing", "bought", "others", "trending", "cart"],
    "manipulative_consent": ["accept", "agree", "cookies", "consent", "continue"],
    "obstruction": ["call", "contact", "cancel", "leave", "sure"],
}


def split_sentences(text: str, max_len: int = 240) -> List[str]:
    parts = [p.strip() for p in SENTENCE_SPLIT.split(text or "") if p and p.strip()]
    return [p[:max_len] for p in parts if len(p) >= 8]


class MockTextClassifier:
    name = "mock-lexical-classifier"

    def classify(self, sentences: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for s in sentences:
            low = s.lower()
            best_pattern, best_score = None, 0.0
            for pattern, cues in _CUES.items():
                hits = sum(1 for c in cues if c in low)
                if hits == 0:
                    continue
                score = min(0.95, 0.35 + 0.18 * hits)
                if score > best_score:
                    best_pattern, best_score = pattern, score
            results.append({"text": s, "pattern": best_pattern, "score": round(best_score, 3)})
        return results


class TransformerTextClassifier:
    """
    Real classifier backed by `transformers`. Expects a model fine-tuned on the
    dark-pattern label set (labels must map to keys in `PATTERNS`, plus "none").
    Example models: `microsoft/deberta-v3-small` or `microsoft/MiniLM-L12-H384-uncased`
    after fine-tuning.
    """

    def __init__(self, model_name: str = "microsoft/deberta-v3-small") -> None:
        self.model_name = model_name
        self.name = f"transformer:{model_name}"
        self._pipe = None

    def load(self) -> None:  # pragma: no cover - heavy
        from transformers import pipeline

        self._pipe = pipeline("text-classification", model=self.model_name, top_k=1, truncation=True)
        logger.info("Loaded transformer classifier %s", self.model_name)

    def classify(self, sentences: List[str]) -> List[Dict[str, Any]]:  # pragma: no cover - heavy
        if self._pipe is None:
            self.load()
        out = []
        for s, preds in zip(sentences, self._pipe(sentences)):
            top = preds[0] if isinstance(preds, list) else preds
            label = top["label"].lower()
            pattern = label if label in PATTERNS else None
            out.append({"text": s, "pattern": pattern, "score": float(top["score"]) if pattern else 0.0})
        return out


def build_text_classifier(mode: str, model_name: Optional[str] = None):
    if mode == "local":
        return TransformerTextClassifier(model_name or "microsoft/deberta-v3-small")
    return MockTextClassifier()
