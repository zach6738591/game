"""Humanitarian and logistics abstraction."""

from __future__ import annotations

from typing import Dict

from ..state import Faction


class LogisticsSystem:
    """Tracks humanitarian and resource indices."""

    def __init__(self, factions: Dict[str, Faction]) -> None:
        self.factions = factions
        self.humanitarian_index = 65.0

    def apply_decision(self, faction_id: str, humanitarian_delta: float) -> None:
        self.humanitarian_index = max(
            0.0, min(100.0, self.humanitarian_index + humanitarian_delta)
        )
        if faction_id in self.factions and humanitarian_delta > 0:
            self.factions[faction_id].adjust_morale(humanitarian_delta * 0.4)

    def snapshot(self) -> float:
        return round(self.humanitarian_index, 2)


__all__ = ["LogisticsSystem"]
