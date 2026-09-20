"""
Core ML contracts.

Every detector — rule-based, semantic (DeBERTa / MiniLM), LLM (Gemini / Groq)
or hybrid — implements `DarkPatternModel.analyze(text, context)` and returns a
list of `Signal` objects. Signals are later aggregated into `Detection`s by the
`HybridDetector` and enriched by the explanation service.

Keeping this contract tiny is what allows the mock implementations to be
swapped for real models without touching services or API routes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Signal:
    """A single piece of evidence emitted by one detector."""

    pattern: str                 # canonical pattern key, e.g. "fake_scarcity"
    confidence: float            # 0..1
    evidence: str                # the text/element that triggered the signal
    source: str                  # "rule" | "semantic" | "llm" | "dom" | "css"
    location: str = "Page"       # human readable location (e.g. "Checkout form")
    element: Optional[str] = None  # CSS selector / element id when known
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInfo:
    name: str
    version: str
    kind: str           # "rule" | "semantic" | "llm" | "hybrid"
    mode: str           # "mock" | "local" | "gemini" | "groq"
    description: str = ""


class DarkPatternModel(ABC):
    """Abstract detector. Implementations must be side-effect free."""

    info: ModelInfo

    @abstractmethod
    async def analyze(self, text: str, context: Dict[str, Any]) -> List[Signal]:
        """
        :param text:    Visible page text (already extracted).
        :param context: Extracted features (buttons, prices, timers, checkboxes...).
        :return:        List of signals. May be empty.
        """
        raise NotImplementedError

    async def warmup(self) -> None:  # pragma: no cover - optional
        """Load weights / clients. Called once on startup."""
        return None
