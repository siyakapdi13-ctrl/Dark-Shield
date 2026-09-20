"""
AI Consumer Assistant ("Dark Shield AI").

    React Chat -> FastAPI -> AIService -> Gemini / Groq / Mock provider -> Response

The provider is the same abstraction used by the LLM detector, so switching
`AI_MODE` upgrades both detection and the assistant. In mock mode a knowledge-
base responder answers common consumer questions and can reference a specific
analysis when `analysisId` is supplied.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from app.config import Settings, get_settings
from app.ml import PATTERNS
from app.ml.llm_detector import LLMProvider, MockLLMProvider, build_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Dark Shield AI, a friendly consumer-protection assistant.
You explain deceptive UI/UX patterns ("dark patterns") in plain language, help people interpret
Dark Shield analysis results, and suggest what to check before buying.
Rules: never claim a site is fraudulent; describe *potential* manipulation indicators; be concise;
use short paragraphs or bullet points; if given analysis context, reference concrete detections."""

_GREETING = "Hi! I'm Dark Shield AI. Ask me about a website's analysis, what a specific dark pattern means, or what to check before you buy."

_FAQ = [
    (r"\b(safe|trust|risk)\b.*\b(site|website|shop|store|this)\b|\bis (this|it) safe\b",
     "I can't guarantee any website is safe, but I can help you interpret the signals. Run an analysis on the URL and look at the Trust Score: 80–100 suggests mostly transparent design, 50–79 means some pressure or pricing tactics were found, and below 50 means several high-severity indicators. Always compare the final total at checkout with the advertised price."),
    (r"what (is|does|are).*(dark pattern)",
     "A dark pattern is a user-interface design that nudges or tricks you into a decision you might not make with clear information — for example fake countdown timers, pre-ticked paid add-ons, or guilt-laden 'No thanks' buttons. Dark Shield detects these signals and explains them so you can decide for yourself."),
    (r"checkout|cart|basket",
     "On a checkout page, check three things: (1) every pre-selected checkbox or add-on, (2) fee lines such as 'service' or 'convenience' fees that were not in the advertised price, and (3) whether a trial converts to a paid subscription. If any of these appear, Dark Shield will usually flag Pre-selected Add-on, Hidden Charges or Forced Continuity."),
    (r"why .*(suspicious|flagged|marked|detected)",
     "Items are flagged when several independent signals agree — keyword rules, semantic similarity to known manipulative phrasing, page structure (e.g. a pre-checked box), and optionally an LLM review. Open the detection card to see the exact evidence text, the confidence, and the reasoning."),
    (r"confidence|score.*(calculat|work)",
     "Each detector produces a confidence between 0 and 1. The hybrid engine fuses them with a weighted noisy-OR so that agreeing sources increase confidence, then adds a small bonus when two or more sources agree. The Trust Score subtracts weighted penalties for each detection from 100 across five categories: Transparency, Pricing Clarity, UI Fairness, Checkout Transparency and Marketing Pressure."),
    (r"hello|hi\b|hey", _GREETING),
]


def _pattern_answer(question: str) -> Optional[str]:
    q = question.lower()
    for pdef in PATTERNS.values():
        names = {pdef.name.lower(), pdef.key.replace("_", " ")}
        if any(n in q for n in names):
            return (f"**{pdef.name}** — {pdef.explanation}\n\n"
                    f"Why it matters: {pdef.reason}\n\n"
                    f"What to do: {pdef.recommendation}")
    return None


def _analysis_answer(question: str, analysis: Dict[str, Any]) -> str:
    dets = analysis.get("detections", [])
    site = analysis.get("website", analysis.get("url"))
    if not dets:
        return f"For {site}, Dark Shield found no dark pattern indicators. Trust Score is {analysis.get('trustScore')}/100. That's a good sign, but still verify the final total before paying."
    lines = [f"Here's what I see for **{site}** (Trust Score {analysis.get('trustScore')}/100, {analysis.get('riskLevel')} risk):"]
    for d in dets[:5]:
        lines.append(f"• **{d['type']}** ({d['severity']}, {d['confidence']}% confidence) — evidence: “{d['evidence'][:90]}”. {d['recommendation']}")
    if len(dets) > 5:
        lines.append(f"…and {len(dets) - 5} more. Open the full report for details.")
    q = question.lower()
    if "concern" in q or "worried" in q or "should i" in q:
        high = sum(1 for d in dets if d["severity"] == "High")
        lines.append(f"\nMy take: {high} high-severity indicator(s). Proceed carefully, double-check every line item, and consider comparing with another retailer.")
    return "\n".join(lines)


class AIService:
    def __init__(self, settings: Optional[Settings] = None, provider: Optional[LLMProvider] = None) -> None:
        self.settings = settings or get_settings()
        s = self.settings
        self.provider = provider or build_provider(s.ai_mode, gemini_key=s.gemini_api_key, gemini_model=s.gemini_model,
                                                   groq_key=s.groq_api_key, groq_model=s.groq_model)

    @property
    def provider_name(self) -> str:
        return self.provider.name

    async def answer(self, question: str, history: List[Dict[str, str]], analysis: Optional[Dict[str, Any]] = None) -> str:
        if isinstance(self.provider, MockLLMProvider):
            return self._mock_answer(question, analysis)
        prompt = ""
        if analysis:
            compact = {k: analysis.get(k) for k in ("website", "url", "trustScore", "riskLevel", "summary")}
            compact["detections"] = [{k: d.get(k) for k in ("type", "severity", "confidence", "evidence", "recommendation")} for d in analysis.get("detections", [])[:8]]
            prompt += f"ANALYSIS CONTEXT (JSON): {compact}\n\n"
        for m in history[-8:]:
            prompt += f"{m['role'].upper()}: {m['content']}\n"
        prompt += f"USER: {question}\nASSISTANT:"
        try:
            return (await self.provider.complete(prompt, system=SYSTEM_PROMPT, json_mode=False)).strip()
        except Exception as exc:
            logger.error("Assistant provider failed: %s", exc)
            return self._mock_answer(question, analysis) + "\n\n_(Live AI provider unavailable — answered from the built-in knowledge base.)_"

    def _mock_answer(self, question: str, analysis: Optional[Dict[str, Any]]) -> str:
        q = question.strip()
        if not q:
            return _GREETING
        if analysis and re.search(r"this|website|site|product|page|checkout|result|report|safe|concern", q.lower()):
            return _analysis_answer(q, analysis)
        pa = _pattern_answer(q)
        if pa:
            return pa
        for pattern, answer in _FAQ:
            if re.search(pattern, q.lower()):
                return answer
        return ("I can help with three things: explaining a dark pattern (e.g. “What does confirmshaming mean?”), "
                "interpreting an analysis (“Why was this product marked suspicious?”), or advising what to check before buying "
                "(“Should I be concerned about this checkout page?”). What would you like to know?")


_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _service
    if _service is None:
        _service = AIService()
    return _service
