"""
Trust Score service.

    Trust Score = 100
                  - weighted penalty from detected patterns
                  - pricing transparency penalty
                  - pressure-language penalty
                  - checkout manipulation penalty

Each pattern contributes `penalty * (confidence/100) * severity_multiplier` to
the category it belongs to. Category scores are 100 minus their penalties
(clamped) and the overall score is a weighted average of categories.

The score is an analytical indicator, not a guarantee of safety or fraud.
Weights are configurable via `CATEGORY_WEIGHTS` / `SEVERITY_MULTIPLIER`.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from app.ml import PATTERNS, TRUST_CATEGORIES, Detection

CATEGORY_WEIGHTS: Dict[str, float] = {
    "transparency": 0.22,
    "pricing_clarity": 0.22,
    "ui_fairness": 0.18,
    "checkout_transparency": 0.20,
    "marketing_pressure": 0.18,
}
SEVERITY_MULTIPLIER = {"High": 1.0, "Medium": 0.75, "Low": 0.5}
MAX_CATEGORY_PENALTY = 70.0


def risk_level(score: int) -> str:
    if score >= 80:
        return "Low"
    if score >= 50:
        return "Moderate"
    return "High"


def risk_label(score: int) -> str:
    return {"Low": "Lower Risk / Safe Indicators", "Moderate": "Moderate Risk", "High": "High Risk"}[risk_level(score)]


def calculate_trust_score(detections: Iterable[Detection], features: Dict[str, Any]) -> Dict[str, Any]:
    penalties: Dict[str, float] = {k: 0.0 for k in TRUST_CATEGORIES}
    breakdown: List[Dict[str, Any]] = []

    for d in detections:
        pdef = PATTERNS[d.pattern]
        p = pdef.penalty * (d.confidence / 100.0) * SEVERITY_MULTIPLIER.get(d.severity, 0.75)
        penalties[pdef.category] += p
        breakdown.append({"pattern": d.name, "category": TRUST_CATEGORIES[pdef.category], "penalty": round(p, 1),
                          "confidence": d.confidence, "severity": d.severity})

    # Feature-level adjustments (independent of explicit detections)
    stats = features.get("stats", {})
    if features.get("cta_count", 0) >= 6:
        penalties["marketing_pressure"] += min(8.0, (features["cta_count"] - 5) * 1.5)
    if len(features.get("urgency_words", [])) >= 4:
        penalties["marketing_pressure"] += 4.0
    if stats.get("prechecked", 0) >= 2:
        penalties["checkout_transparency"] += 4.0
    if features.get("low_contrast_controls"):
        penalties["ui_fairness"] += min(6.0, len(features["low_contrast_controls"]) * 1.5)
    if features.get("discount_values") and max(features["discount_values"]) >= 70:
        penalties["pricing_clarity"] += 3.0

    categories: Dict[str, int] = {}
    for key, label in TRUST_CATEGORIES.items():
        pen = min(MAX_CATEGORY_PENALTY, penalties[key])
        categories[label] = int(round(max(0.0, 100.0 - pen)))

    score = int(round(sum(categories[TRUST_CATEGORIES[k]] * w for k, w in CATEGORY_WEIGHTS.items())))
    score = max(0, min(100, score))

    dets = list(detections)
    confidence = int(round(sum(d.confidence for d in dets) / len(dets))) if dets else 90

    return {
        "score": score,
        "riskLevel": risk_level(score),
        "riskLabel": risk_label(score),
        "categories": categories,
        "weights": {TRUST_CATEGORIES[k]: v for k, v in CATEGORY_WEIGHTS.items()},
        "breakdown": sorted(breakdown, key=lambda b: b["penalty"], reverse=True),
        "confidence": confidence,
        "disclaimer": "The Trust Score is an analytical indicator derived from detected UI signals. It is not a guarantee of safety or proof of wrongdoing.",
    }
