"""
Detection service – builds the detector stack from configuration and runs it.

    AI_MODE=mock    -> RuleBased + Semantic(mock)                      (no downloads, no API)
    AI_MODE=local   -> RuleBased + Semantic(MiniLM/DeBERTa)             (local transformers)
    AI_MODE=gemini  -> RuleBased + Semantic(mock) + LLM(Gemini)
    AI_MODE=groq    -> RuleBased + Semantic(mock) + LLM(Groq)
    AI_MODE=hybrid  -> RuleBased + Semantic(local) + LLM(first available)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.config import Settings, get_settings
from app.ml import Detection, HybridDetector, LLMDetector, RuleBasedDetector, SemanticDetector, build_provider
from app.ml.reinforcement_learning import FeedbackPolicy

logger = logging.getLogger(__name__)


class DetectionService:
    def __init__(self, settings: Optional[Settings] = None, policy: Optional[FeedbackPolicy] = None) -> None:
        self.settings = settings or get_settings()
        self.policy = policy or FeedbackPolicy()
        self.detector = self._build()

    def _build(self) -> HybridDetector:
        s = self.settings
        detectors = [RuleBasedDetector()]
        semantic_mode = "local" if s.ai_mode in ("local", "hybrid") else "mock"
        detectors.append(SemanticDetector(mode=semantic_mode))
        if s.ai_mode in ("gemini", "groq", "hybrid"):
            provider = build_provider(s.ai_mode, gemini_key=s.gemini_api_key, gemini_model=s.gemini_model,
                                      groq_key=s.groq_api_key, groq_model=s.groq_model)
            detectors.append(LLMDetector(provider))
        hybrid = HybridDetector(detectors)
        logger.info("Detection stack: %s (AI_MODE=%s)", hybrid.info.description, s.ai_mode)
        return hybrid

    async def detect(self, features: Dict[str, Any]) -> List[Detection]:
        detections = await self.detector.detect(features.get("visible_text", ""), features)
        # Apply RL feedback adjustment (identity until enough feedback collected)
        for d in detections:
            factor = self.policy.adjustment(d.pattern)
            if factor != 1.0:
                d.confidence = int(max(1, min(99, round(d.confidence * factor))))
                d.meta["rlAdjustment"] = factor
        return detections

    def describe(self) -> Dict[str, Any]:
        return {
            "aiMode": self.settings.ai_mode,
            "detectors": [{"name": d.info.name, "kind": d.info.kind, "mode": d.info.mode, "description": d.info.description} for d in self.detector.detectors],
        }


_service: Optional[DetectionService] = None


def get_detection_service() -> DetectionService:
    global _service
    if _service is None:
        _service = DetectionService()
    return _service
