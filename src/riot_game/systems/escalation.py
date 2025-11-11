"""Escalation model for the simulation."""

from __future__ import annotations

from dataclasses import dataclass

from ..state import CrowdEmotion, EscalationLevel


@dataclass
class EscalationModel:
    """Tracks and updates escalation state."""

    level: EscalationLevel = EscalationLevel.STABLE
    tension_score: float = 0.0
    posture_bias: float = 0.0

    def update(self, dominant_emotion: CrowdEmotion, media_visibility: int) -> EscalationLevel:
        adjustment = 0.0
        if dominant_emotion == CrowdEmotion.CALM:
            adjustment -= 0.4
        elif dominant_emotion == CrowdEmotion.CONCERNED:
            adjustment += 0.2
        elif dominant_emotion == CrowdEmotion.AGITATED:
            adjustment += 0.6
        elif dominant_emotion == CrowdEmotion.PANICKED:
            adjustment += 1.2

        adjustment += media_visibility * 0.1
        adjustment += self.posture_bias
        self.tension_score = max(0.0, self.tension_score + adjustment)

        if self.tension_score < 1.5:
            self.level = EscalationLevel.STABLE
        elif self.tension_score < 3.5:
            self.level = EscalationLevel.TENSE
        elif self.tension_score < 5.5:
            self.level = EscalationLevel.VOLATILE
        else:
            self.level = EscalationLevel.CRISIS

        return self.level

    def set_posture_bias(self, bias: float) -> None:
        """Adjust how assertive or conciliatory the current posture is."""

        self.posture_bias = bias

    def apply_bias(self, delta: float) -> None:
        """Apply minute-level bias from player decisions (negative reduces tension)."""

        self.tension_score = max(0.0, self.tension_score + delta)


__all__ = ["EscalationModel"]
