"""
Semantic detector.

Compares page sentences with curated *prototype* phrases for each dark pattern
using sentence embeddings (MiniLM via sentence-transformers when AI_MODE=local),
then combines that similarity with the text classifier score.

In mock mode a cheap token-overlap similarity stands in for embeddings so the
whole pipeline runs without model downloads.
"""
from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Sequence

from app.ml.base_model import DarkPatternModel, ModelInfo, Signal
from app.ml.text_classifier import build_text_classifier, split_sentences

logger = logging.getLogger(__name__)

PROTOTYPES: Dict[str, List[str]] = {
    "fake_scarcity": ["Only a few items left in stock", "Hurry, this product is almost sold out", "Limited stock available, selling fast"],
    "urgency": ["Offer ends soon, buy now", "Limited time deal, act now before it expires", "Flash sale ends in minutes"],
    "confirmshaming": ["No thanks, I don't want to save money", "No, I prefer paying full price", "I don't care about protecting my purchase"],
    "hidden_charges": ["A service fee will be added at checkout", "Additional processing charges apply", "Convenience fee included in total"],
    "preselected_addons": ["Add purchase protection to your order", "Yes, add extended warranty", "Priority delivery selected for you"],
    "misleading_discount": ["Was a much higher price, now 80% off", "Compare at regular price, you save", "Massive discount from list price"],
    "forced_continuity": ["Your free trial will automatically renew as a paid subscription", "You will be charged after the trial ends unless you cancel", "Subscription continues automatically"],
    "social_pressure": ["Many people are viewing this item right now", "Someone just bought this product", "Trending, others have this in their cart"],
    "manipulative_consent": ["Accept all cookies to continue", "By continuing you agree to share your data", "Agree and continue"],
    "obstruction": ["Call customer support to cancel your subscription", "Are you sure you want to leave? Consider this retention offer", "Cancellation requests are processed manually"],
}

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _tokens(s: str) -> set:
    return set(_TOKEN_RE.findall(s.lower())) - {"the", "a", "an", "to", "of", "and", "is", "in", "your", "you", "this", "for", "on"}


class MockEmbedder:
    """Token-overlap cosine used in mock mode."""

    name = "mock-token-overlap"

    def similarity(self, a: str, b: str) -> float:
        ta, tb = _tokens(a), _tokens(b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / math.sqrt(len(ta) * len(tb))


class SentenceTransformerEmbedder:  # pragma: no cover - heavy
    name = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name)

    def similarity(self, a: str, b: str) -> float:
        if self._model is None:
            self._load()
        from sentence_transformers import util

        ea, eb = self._model.encode([a, b], convert_to_tensor=True, normalize_embeddings=True)
        return float(util.cos_sim(ea, eb))


class SemanticDetector(DarkPatternModel):
    def __init__(self, mode: str = "mock", threshold: float = 0.42) -> None:
        self.mode = mode
        self.threshold = threshold
        self.embedder = SentenceTransformerEmbedder() if mode == "local" else MockEmbedder()
        self.classifier = build_text_classifier(mode)
        self.info = ModelInfo(
            name="SemanticDetector", version="1.0", kind="semantic", mode=mode,
            description="Embedding similarity to pattern prototypes + transformer text classification.",
        )

    async def analyze(self, text: str, context: Dict[str, Any]) -> List[Signal]:
        sentences = split_sentences(text)[:120]
        # include button / popup text as first-class candidates
        extra: Sequence[str] = list(context.get("button_text", []))[:40] + list(context.get("popup_text", []))[:20]
        candidates = list(dict.fromkeys([*sentences, *extra]))
        if not candidates:
            return []

        cls = {r["text"]: r for r in self.classifier.classify(candidates)}
        signals: List[Signal] = []
        page_type = context.get("page_type", "Page")

        for sent in candidates:
            best_pattern: Optional[str] = None
            best_sim = 0.0
            for pattern, protos in PROTOTYPES.items():
                sim = max(self.embedder.similarity(sent, p) for p in protos)
                if sim > best_sim:
                    best_pattern, best_sim = pattern, sim
            c = cls.get(sent, {})
            cls_pattern, cls_score = c.get("pattern"), c.get("score", 0.0)

            # Fuse: agreement boosts confidence; disagreement keeps the stronger.
            if best_pattern and best_pattern == cls_pattern:
                conf = min(0.97, 0.5 * best_sim + 0.5 * cls_score + 0.15)
                pattern = best_pattern
            elif best_sim >= self.threshold:
                conf, pattern = 0.55 * best_sim + 0.25, best_pattern
            elif cls_pattern and cls_score >= 0.6:
                conf, pattern = 0.6 * cls_score, cls_pattern
            else:
                continue
            if conf >= 0.45 and pattern:
                signals.append(Signal(pattern, round(conf, 3), sent[:200], "semantic", page_type,
                                      meta={"similarity": round(best_sim, 3), "classifier": round(cls_score, 3), "embedder": self.embedder.name}))
        return signals
