"""
Explanation service – converts technical detections into consumer-friendly,
explainable results.

Every detection answers three questions:
  1. What was detected?      -> type / evidence / location
  2. Why might it be deceptive? -> reason / explanation
  3. What should I consider?  -> recommendation

Language is deliberately cautious ("potential", "may", "indicator") — the
system never asserts fraud or intent.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from app.ml import PATTERNS, Detection

_CONFIDENCE_LABEL = [(90, "High-confidence detection"), (70, "Likely manipulation indicator"), (0, "Suspicious UI signal")]


def confidence_label(confidence: int) -> str:
    for threshold, label in _CONFIDENCE_LABEL:
        if confidence >= threshold:
            return label
    return "Suspicious UI signal"


def explain_detection(d: Detection) -> Dict[str, Any]:
    pdef = PATTERNS[d.pattern]
    explanation = pdef.explanation
    # Enrich with structured meta where available
    if d.pattern == "fake_scarcity" and d.meta.get("count") is not None:
        explanation += f" The page claims only {d.meta['count']} unit(s) remain."
    if d.pattern == "misleading_discount" and d.meta.get("ratio"):
        explanation += f" The reference price is about {d.meta['ratio']}× the selling price, which is unusually large."
    if d.meta.get("rationale"):
        explanation += f" AI reviewer note: {d.meta['rationale']}"

    return {
        "id": uuid.uuid4().hex[:12],
        "pattern": d.pattern,
        "type": d.name,
        "severity": d.severity,
        "confidence": d.confidence,
        "confidenceLabel": confidence_label(d.confidence),
        "evidence": d.evidence,
        "evidenceItems": d.evidence_items,
        "location": d.location,
        "element": d.element,
        "reason": pdef.reason,
        "explanation": explanation,
        "recommendation": pdef.recommendation,
        "category": pdef.category,
        "sources": d.sources,
    }


def explain_all(detections: List[Detection]) -> List[Dict[str, Any]]:
    return [explain_detection(d) for d in detections]


def summarize(website: str, trust: Dict[str, Any], detections: List[Dict[str, Any]]) -> str:
    n = len(detections)
    high = sum(1 for d in detections if d["severity"] == "High")
    if n == 0:
        return f"No dark pattern indicators were detected on {website}. The page shows mostly transparent design signals, but always review the final price before paying."
    top = ", ".join(d["type"] for d in detections[:3])
    return (
        f"{website} shows {n} potential dark pattern{'s' if n != 1 else ''} ({high} high severity), including {top}. "
        f"Trust Score {trust['score']}/100 indicates {trust['riskLabel'].lower()}. "
        "Review the highlighted elements and the recommendations before completing a purchase."
    )
