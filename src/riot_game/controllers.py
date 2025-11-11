"""Decision-making heuristics for factions and observers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .state import CrowdEmotion, EscalationLevel, Faction


@dataclass
class Decision:
    """Represents a high-level decision taken by a faction."""

    faction_id: str
    summary: str
    morale_delta: float
    trust_effects: Dict[str, float]
    transparency_delta: float
    humanitarian_delta: float


class DecisionEngine:
    """Simple rule-based decision helper."""

    def __init__(self, factions: Dict[str, Faction]) -> None:
        self.factions = factions

    def evaluate(
        self,
        escalation: EscalationLevel,
        dominant_emotion: CrowdEmotion,
        media_visibility: int,
    ) -> List[Decision]:
        decisions: List[Decision] = []
        for faction in self.factions.values():
            decisions.append(
                self._baseline_decision(faction, escalation, dominant_emotion, media_visibility)
            )
        return decisions

    def _baseline_decision(
        self,
        faction: Faction,
        escalation: EscalationLevel,
        dominant_emotion: CrowdEmotion,
        media_visibility: int,
    ) -> Decision:
        summary_parts = ["Reaffirm commitment to dialogue"]
        morale_delta = 0.4
        transparency_delta = 0.6
        humanitarian_delta = 0.5
        trust_effects: Dict[str, float] = {}

        if escalation in {EscalationLevel.VOLATILE, EscalationLevel.CRISIS}:
            summary_parts.append("deploy additional mediators")
            if faction.spend_resource("mediation"):
                morale_delta += 1.0
                humanitarian_delta += 1.2
            else:
                summary_parts.append("request support from partners")
        else:
            summary_parts.append("maintain calm presence")

        if dominant_emotion in {CrowdEmotion.AGITATED, CrowdEmotion.PANICKED}:
            if faction.spend_resource("communications"):
                summary_parts.append("broadcast reassurance")
                trust_effects = {other: 1.5 for other in faction.trust.keys()}
            else:
                summary_parts.append("coordinate with NGOs for messaging")
                trust_effects = {other: 0.8 for other in faction.trust.keys()}

        if media_visibility >= 3:
            transparency_delta += 1.0
            summary_parts.append("host press briefing")

        return Decision(
            faction_id=faction.identifier,
            summary="; ".join(summary_parts),
            morale_delta=morale_delta,
            trust_effects=trust_effects,
            transparency_delta=transparency_delta,
            humanitarian_delta=humanitarian_delta,
        )


__all__ = ["Decision", "DecisionEngine"]
