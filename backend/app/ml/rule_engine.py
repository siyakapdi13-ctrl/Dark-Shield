"""
Rule-based dark pattern detector.

Deterministic, explainable and fast. Uses keyword/regex rules over visible text
plus structural signals from the extracted features (pre-checked checkboxes,
timers, price pairs). Acts as the high-precision backbone of the hybrid system.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from app.ml.base_model import DarkPatternModel, ModelInfo, Signal
from app.ml.patterns import PATTERNS

_SCARCITY_RE = re.compile(r"\bonly\s+(\d{1,3})\s+(?:items?\s+|units?\s+|pieces?\s+)?left\b", re.I)
_TIMER_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_PERCENT_OFF_RE = re.compile(r"(\d{2,3})\s*%\s*off", re.I)
_PRICE_RE = re.compile(r"[$€£₹]\s?\d[\d,]*(?:\.\d{2})?")


def _sentences_with(text: str, needle: str, window: int = 80) -> List[str]:
    """Return short evidence snippets around each keyword occurrence."""
    out: List[str] = []
    low = text.lower()
    start = 0
    needle_l = needle.lower()
    while True:
        idx = low.find(needle_l, start)
        if idx == -1 or len(out) >= 3:
            break
        a, b = max(0, idx - window // 2), min(len(text), idx + len(needle) + window // 2)
        snippet = text[a:b].strip().replace("\n", " ")
        out.append(("…" if a > 0 else "") + snippet + ("…" if b < len(text) else ""))
        start = idx + len(needle)
    return out


class RuleBasedDetector(DarkPatternModel):
    info = ModelInfo(name="RuleBasedDetector", version="1.0", kind="rule", mode="local",
                     description="Keyword, regex and DOM heuristics for known dark-pattern signatures.")

    async def analyze(self, text: str, context: Dict[str, Any]) -> List[Signal]:
        signals: List[Signal] = []
        text = text or ""
        low = text.lower()
        buttons: List[str] = context.get("button_text", [])
        checkboxes: List[Dict[str, Any]] = context.get("checkbox_state", [])
        timers: List[str] = context.get("timer_elements", [])
        prices: List[Dict[str, Any]] = context.get("price_values", [])
        popups: List[str] = context.get("popup_text", [])
        page_type = context.get("page_type", "Page")

        # --- keyword rules -----------------------------------------------------
        for key, pdef in PATTERNS.items():
            for kw in pdef.keywords:
                kw_pattern = kw.replace("{n}", r"\d+")
                if "{n}" in kw:
                    for m in re.finditer(kw_pattern, low):
                        snippet = text[max(0, m.start() - 30): m.end() + 30].strip()
                        signals.append(Signal(key, 0.85, snippet, "rule", page_type, meta={"rule": kw}))
                elif kw in low:
                    for snippet in _sentences_with(text, kw):
                        signals.append(Signal(key, 0.7, snippet, "rule", page_type, meta={"rule": kw}))

        # --- fake scarcity with explicit count ---------------------------------
        for m in _SCARCITY_RE.finditer(text):
            n = int(m.group(1))
            conf = 0.9 if n <= 5 else 0.6
            signals.append(Signal("fake_scarcity", conf, m.group(0), "rule", page_type, meta={"count": n}))

        # --- countdown timers ----------------------------------------------------
        for t in timers[:5]:
            signals.append(Signal("countdown_timer", 0.9, t, "dom", page_type, meta={"rule": "timer_element"}))
        if not timers and _TIMER_RE.search(text) and any(w in low for w in ("ends", "left", "hurry", "offer", "deal")):
            signals.append(Signal("countdown_timer", 0.6, _TIMER_RE.search(text).group(0), "rule", page_type))

        # --- confirmshaming in buttons -------------------------------------------
        for b in buttons:
            bl = b.lower()
            if bl.startswith("no") and any(w in bl for w in ("don't", "dont", "rather", "hate", "prefer", "want")):
                signals.append(Signal("confirmshaming", 0.9, b, "dom", "Dialog / modal", meta={"rule": "decline_button"}))
        for p in popups:
            pl = p.lower()
            if any(k in pl for k in ("no, i", "no thanks, i", "i don't want")):
                signals.append(Signal("confirmshaming", 0.85, p, "dom", "Popup", meta={"rule": "popup_decline"}))

        # --- pre-selected add-ons ---------------------------------------------------
        for cb in checkboxes:
            if cb.get("checked") and cb.get("optional", True):
                label = cb.get("label", "checkbox")
                paid_hint = any(w in label.lower() for w in ("$", "₹", "€", "£", "insurance", "warranty", "protection", "donat", "premium", "priority", "subscription", "newsletter"))
                signals.append(Signal("preselected_addons", 0.9 if paid_hint else 0.6, label, "dom", "Checkout form",
                                      element=cb.get("selector"), meta={"rule": "prechecked"}))

        # --- misleading discounts -------------------------------------------------------
        for m in _PERCENT_OFF_RE.finditer(text):
            pct = int(m.group(1))
            if pct >= 70:
                signals.append(Signal("misleading_discount", 0.65, text[max(0, m.start() - 40): m.end() + 20].strip(), "rule", "Pricing", meta={"percent": pct}))
        for p in prices:
            orig, cur = p.get("original"), p.get("current")
            if orig and cur and cur > 0 and orig / cur >= 2.5:
                signals.append(Signal("misleading_discount", 0.75, f"{p.get('label', 'Price')}: {orig} → {cur}", "dom", "Pricing",
                                      meta={"ratio": round(orig / cur, 2)}))

        # --- hidden charges via fee lines --------------------------------------------------
        for p in prices:
            label = (p.get("label") or "").lower()
            if any(w in label for w in ("fee", "surcharge", "charge")) and p.get("current"):
                signals.append(Signal("hidden_charges", 0.8, f"{p.get('label')}: {p.get('current')}", "dom", "Checkout summary"))

        # --- CTA pressure (many CTAs)  -----------------------------------------------------
        if context.get("cta_count", 0) >= 8:
            signals.append(Signal("urgency", 0.5, f"{context['cta_count']} call-to-action buttons detected", "css", page_type, meta={"rule": "cta_density"}))

        return signals
