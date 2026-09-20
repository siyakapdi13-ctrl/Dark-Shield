"""
Hybrid detector – fuses rule, semantic, DOM/CSS and LLM signals.

    Rule score + NLP score + DOM signal + CSS/UI signal + LLM reasoning
    = Final detection confidence

Fusion strategy (per pattern):
  1. Group signals by pattern key.
  2. Take a weighted "noisy-OR" of source confidences so that independent
     agreeing sources increase confidence, but a single weak source stays weak.
  3. Add a small agreement bonus when >= 2 distinct sources fire.
  4. Keep the top evidence snippets for explainability.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.ml.base_model import DarkPatternModel, ModelInfo, Signal
from app.ml.patterns import PATTERNS, SEVERITY_ORDER

logger = logging.getLogger(__name__)

SOURCE_WEIGHTS: Dict[str, float] = {"rule": 0.9, "dom": 0.95, "css": 0.6, "semantic": 0.75, "llm": 0.85}
AGREEMENT_BONUS = 0.08
MIN_CONFIDENCE = 0.5


@dataclass
class Detection:
    pattern: str
    name: str
    severity: str
    confidence: int                       # 0-100
    evidence: str
    location: str
    sources: List[str]
    evidence_items: List[str] = field(default_factory=list)
    element: str | None = None
    meta: Dict[str, Any] = field(default_factory=dict)


def _severity_for(pattern: str, confidence: float, n_sources: int) -> str:
    base = PATTERNS[pattern].default_severity
    rank = SEVERITY_ORDER[base]
    if confidence >= 0.9 and n_sources >= 2:
        rank = min(3, rank + 1)
    elif confidence < 0.65:
        rank = max(1, rank - 1)
    return {3: "High", 2: "Medium", 1: "Low"}[rank]


def fuse_signals(signals: List[Signal]) -> List[Detection]:
    grouped: Dict[str, List[Signal]] = defaultdict(list)
    for s in signals:
        if s.pattern in PATTERNS:
            grouped[s.pattern].append(s)

    detections: List[Detection] = []
    for pattern, sigs in grouped.items():
        # per-source best confidence
        per_source: Dict[str, float] = {}
        for s in sigs:
            per_source[s.source] = max(per_source.get(s.source, 0.0), s.confidence)
        # weighted noisy-OR
        not_prob = 1.0
        for src, conf in per_source.items():
            not_prob *= 1.0 - conf * SOURCE_WEIGHTS.get(src, 0.7)
        fused = 1.0 - not_prob
        if len(per_source) >= 2:
            fused = min(0.99, fused + AGREEMENT_BONUS)
        if fused < MIN_CONFIDENCE:
            continue
        sigs_sorted = sorted(sigs, key=lambda s: s.confidence, reverse=True)
        top = sigs_sorted[0]
        evidence_items = list(dict.fromkeys(s.evidence for s in sigs_sorted if s.evidence))[:5]
        detections.append(
            Detection(
                pattern=pattern,
                name=PATTERNS[pattern].name,
                severity=_severity_for(pattern, fused, len(per_source)),
                confidence=int(round(fused * 100)),
                evidence=top.evidence,
                location=top.location,
                sources=sorted(per_source.keys()),
                evidence_items=evidence_items,
                element=top.element,
                meta={"signals": len(sigs), "per_source": {k: round(v, 3) for k, v in per_source.items()},
                      **{k: v for k, v in top.meta.items() if k in ("rationale", "count", "ratio", "percent")}},
            )
        )
    detections.sort(key=lambda d: (SEVERITY_ORDER[d.severity], d.confidence), reverse=True)
    return detections


class HybridDetector(DarkPatternModel):
    def __init__(self, detectors: List[DarkPatternModel]) -> None:
        self.detectors = detectors
        self.info = ModelInfo(name="HybridDetector", version="1.0", kind="hybrid",
                              mode="+".join(d.info.mode for d in detectors),
                              description="Weighted fusion of " + ", ".join(d.info.name for d in detectors))

    async def analyze(self, text: str, context: Dict[str, Any]) -> List[Signal]:
        results = await asyncio.gather(*(d.analyze(text, context) for d in self.detectors), return_exceptions=True)
        signals: List[Signal] = []
        for det, res in zip(self.detectors, results):
            if isinstance(res, Exception):
                logger.error("Detector %s failed: %s", det.info.name, res)
                continue
            signals.extend(res)
        return signals

    async def detect(self, text: str, context: Dict[str, Any]) -> List[Detection]:
        return fuse_signals(await self.analyze(text, context))
