"""Crowd sentiment analytics."""

from __future__ import annotations

from collections import Counter
from typing import Dict

from ..state import CrowdEmotion, CrowdState


class SentimentAnalyzer:
    """Derives aggregate metrics from the crowd state."""

    def __init__(self, crowd: CrowdState) -> None:
        self.crowd = crowd

    def dominant_emotion(self) -> CrowdEmotion:
        return max(self.crowd.emotion_distribution.items(), key=lambda item: item[1])[0]

    def as_percentages(self) -> Dict[str, float]:
        return {
            emotion.name.lower(): round(share * 100, 2)
            for emotion, share in self.crowd.emotion_distribution.items()
        }


__all__ = ["SentimentAnalyzer"]
