"""
LLM-based detector (Gemini / Groq / mock).

The LLM is asked to reason over a compact summary of the page and return a
JSON list of suspected dark patterns with confidence, evidence and a short
rationale. Provider clients are pluggable and *never* called in mock mode.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.ml.base_model import DarkPatternModel, ModelInfo, Signal
from app.ml.patterns import PATTERNS

logger = logging.getLogger(__name__)

DETECTION_PROMPT = """You are Dark Shield, an expert reviewer of deceptive UI/UX ("dark patterns").
Analyse the extracted webpage content below and list potential dark patterns.
Use ONLY these pattern keys: {keys}.
Be conservative: do not claim fraud; flag *potential* manipulation indicators.

Return STRICT JSON: {{"detections":[{{"pattern":"<key>","confidence":0-1,"evidence":"<quoted text>","location":"<where>","rationale":"<one sentence>"}}]}}

PAGE URL: {url}
VISIBLE TEXT (truncated):
{text}

BUTTONS: {buttons}
PRE-CHECKED OPTIONS: {checked}
TIMERS: {timers}
PRICES: {prices}
"""


class LLMProvider:
    name = "base"

    async def complete(self, prompt: str, *, system: Optional[str] = None, json_mode: bool = True) -> str:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Returns an empty detection set – rule + semantic engines carry demo mode."""

    name = "mock"

    async def complete(self, prompt: str, *, system: Optional[str] = None, json_mode: bool = True) -> str:
        return json.dumps({"detections": []})


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key, self.model = api_key, model

    async def complete(self, prompt: str, *, system: Optional[str] = None, json_mode: bool = True) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body: Dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_mode:
            body["generationConfig"] = {"responseMimeType": "application/json", "temperature": 0.2}
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        self.api_key, self.model = api_key, model

    async def complete(self, prompt: str, *, system: Optional[str] = None, json_mode: bool = True) -> str:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body: Dict[str, Any] = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]


def build_provider(mode: str, *, gemini_key: str = "", gemini_model: str = "", groq_key: str = "", groq_model: str = "") -> LLMProvider:
    if mode in ("gemini", "hybrid") and gemini_key:
        return GeminiProvider(gemini_key, gemini_model or "gemini-1.5-flash")
    if mode in ("groq", "hybrid") and groq_key:
        return GroqProvider(groq_key, groq_model or "llama-3.1-8b-instant")
    if mode in ("gemini", "groq") and not (gemini_key or groq_key):
        logger.warning("AI_MODE=%s but no API key configured – falling back to mock provider.", mode)
    return MockLLMProvider()


def _extract_json(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"detections": []}


class LLMDetector(DarkPatternModel):
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
        self.info = ModelInfo(name="LLMDetector", version="1.0", kind="llm", mode=provider.name,
                              description="LLM reasoning over extracted page features (Gemini/Groq).")

    async def analyze(self, text: str, context: Dict[str, Any]) -> List[Signal]:
        if isinstance(self.provider, MockLLMProvider):
            return []
        prompt = DETECTION_PROMPT.format(
            keys=", ".join(PATTERNS.keys()),
            url=context.get("url", ""),
            text=(text or "")[:6000],
            buttons=json.dumps(context.get("button_text", [])[:40]),
            checked=json.dumps([c.get("label") for c in context.get("checkbox_state", []) if c.get("checked")][:20]),
            timers=json.dumps(context.get("timer_elements", [])[:10]),
            prices=json.dumps(context.get("price_values", [])[:20]),
        )
        try:
            raw = await self.provider.complete(prompt, system="Respond with strict JSON only.")
        except Exception as exc:  # network / quota – degrade gracefully
            logger.error("LLM provider %s failed: %s", self.provider.name, exc)
            return []
        data = _extract_json(raw)
        signals: List[Signal] = []
        for d in data.get("detections", [])[:25]:
            key = str(d.get("pattern", "")).strip().lower()
            if key not in PATTERNS:
                continue
            try:
                conf = float(d.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            signals.append(Signal(key, max(0.0, min(1.0, conf)), str(d.get("evidence", ""))[:300], "llm",
                                  str(d.get("location", context.get("page_type", "Page"))),
                                  meta={"rationale": d.get("rationale", ""), "provider": self.provider.name}))
        return signals
