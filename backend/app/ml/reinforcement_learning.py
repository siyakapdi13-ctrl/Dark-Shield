"""
Reinforcement-learning feedback architecture.

    Prediction -> User Feedback -> Feedback Storage -> Reward Signal
               -> Model Evaluation -> Future Model Improvement

IMPORTANT: This module implements the *data-collection and reward* side of the
loop. It does NOT train a policy. Until an actual trained policy is supplied,
RL is an extensibility component: rewards are aggregated per pattern and can be
used to (a) re-weight source confidences and (b) build a labelled dataset for
supervised fine-tuning or RLHF-style training later.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

FEEDBACK_TYPES = ("correct", "incorrect", "helpful", "not_helpful", "false_positive")

# Reward shaping – positive rewards reinforce, negative rewards penalise.
REWARDS: Dict[str, float] = {
    "correct": 1.0,
    "helpful": 0.5,
    "not_helpful": -0.25,
    "incorrect": -1.0,
    "false_positive": -1.0,
}


@dataclass
class RewardSummary:
    pattern: str
    samples: int
    total_reward: float
    mean_reward: float
    suggested_weight_adjustment: float  # multiplicative factor for fused confidence


def reward_for(feedback_type: str) -> float:
    if feedback_type not in REWARDS:
        raise ValueError(f"Unknown feedback type '{feedback_type}'. Expected one of {FEEDBACK_TYPES}.")
    return REWARDS[feedback_type]


class FeedbackPolicy:
    """
    Minimal 'bandit-style' evaluator.

    Given historical feedback for a pattern it proposes a confidence
    multiplier in [0.7, 1.15]. A future trained policy can replace this class
    while keeping the same interface (`adjustment(pattern) -> float`).
    """

    def __init__(self, learning_rate: float = 0.05) -> None:
        self.learning_rate = learning_rate
        self._stats: Dict[str, Dict[str, float]] = {}

    def observe(self, pattern: str, feedback_type: str) -> float:
        r = reward_for(feedback_type)
        st = self._stats.setdefault(pattern, {"n": 0, "sum": 0.0})
        st["n"] += 1
        st["sum"] += r
        return r

    def observe_many(self, rows: Iterable[Dict[str, str]]) -> None:
        for row in rows:
            if row.get("pattern") and row.get("feedbackType") in REWARDS:
                self.observe(row["pattern"], row["feedbackType"])

    def summary(self, pattern: str) -> Optional[RewardSummary]:
        st = self._stats.get(pattern)
        if not st or st["n"] == 0:
            return None
        mean = st["sum"] / st["n"]
        return RewardSummary(pattern, int(st["n"]), round(st["sum"], 2), round(mean, 3), round(self.adjustment(pattern), 3))

    def adjustment(self, pattern: str) -> float:
        st = self._stats.get(pattern)
        if not st or st["n"] < 3:  # need a few samples before adjusting
            return 1.0
        mean = st["sum"] / st["n"]
        # shrink toward 1.0 with a small learning rate, clamp to safe range
        factor = 1.0 + self.learning_rate * mean * min(1.0, st["n"] / 20)
        return max(0.7, min(1.15, factor))
