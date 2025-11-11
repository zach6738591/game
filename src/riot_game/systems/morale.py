"""Morale and trust calculations."""

from __future__ import annotations

from typing import Dict

from ..state import Faction


class MoraleSystem:
    """Applies morale and trust deltas based on decisions."""

    def __init__(self, factions: Dict[str, Faction]) -> None:
        self.factions = factions

    def apply_morale(self, faction_id: str, delta: float) -> None:
        if faction_id in self.factions:
            self.factions[faction_id].adjust_morale(delta)

    def apply_trust(self, effects: Dict[str, Dict[str, float]]) -> None:
        for source, delta_map in effects.items():
            if source not in self.factions:
                continue
            for target, delta in delta_map.items():
                self.factions[source].adjust_trust(target, delta)

    def aggregate_average_trust(self) -> Dict[str, float]:
        averages: Dict[str, float] = {}
        for faction in self.factions.values():
            if faction.trust:
                averages[faction.identifier] = sum(faction.trust.values()) / len(faction.trust)
            else:
                averages[faction.identifier] = 0.0
        return averages


__all__ = ["MoraleSystem"]
