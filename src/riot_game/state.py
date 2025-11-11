"""Core data models for the Riot: Civil Unrest prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List

from .config import ScenarioConfiguration


class CrowdEmotion(Enum):
    CALM = auto()
    CONCERNED = auto()
    AGITATED = auto()
    PANICKED = auto()


class EscalationLevel(Enum):
    STABLE = auto()
    TENSE = auto()
    VOLATILE = auto()
    CRISIS = auto()


@dataclass
class Faction:
    """Represents a faction's current state."""

    identifier: str
    name: str
    role: str
    morale: float
    trust: Dict[str, float]
    resources: Dict[str, int]

    def adjust_morale(self, delta: float) -> None:
        self.morale = max(0.0, min(100.0, self.morale + delta))

    def adjust_trust(self, target: str, delta: float) -> None:
        if target in self.trust:
            self.trust[target] = max(0.0, min(100.0, self.trust[target] + delta))

    def spend_resource(self, resource: str, amount: int = 1) -> bool:
        if self.resources.get(resource, 0) >= amount:
            self.resources[resource] -= amount
            return True
        return False


@dataclass
class CrowdState:
    """Aggregated crowd sentiment and density tracking."""

    population: int
    emotion_distribution: Dict[CrowdEmotion, float]
    density_hotspots: List[Dict[str, float]]

    def normalize(self) -> None:
        total = sum(self.emotion_distribution.values())
        if total == 0:  # pragma: no cover - defensive
            equal = 1.0 / len(self.emotion_distribution)
            for emotion in self.emotion_distribution:
                self.emotion_distribution[emotion] = equal
            return
        for emotion, value in list(self.emotion_distribution.items()):
            self.emotion_distribution[emotion] = max(0.0, value) / total

    def shift(self, adjustments: Dict[CrowdEmotion, float]) -> None:
        for emotion, delta in adjustments.items():
            self.emotion_distribution[emotion] = max(
                0.0, self.emotion_distribution.get(emotion, 0.0) + delta
            )
        self.normalize()


@dataclass
class Scenario:
    """A playable scenario loaded from data."""

    metadata: Dict[str, str]
    configuration: ScenarioConfiguration
    factions: Dict[str, Faction]
    crowd: CrowdState
    event_deck: List[Dict[str, object]]
    unit_groups: List[Dict[str, object]] = field(default_factory=list)
    map_layout: Dict[str, object] = field(default_factory=dict)

    def sorted_events(self) -> List[Dict[str, object]]:
        return sorted(self.event_deck, key=lambda e: int(e.get("minute", 0)))


@dataclass
class TickReport:
    """Snapshot of the simulation at a specific minute."""

    minute: int
    escalation: EscalationLevel
    crowd_emotions: Dict[str, float]
    faction_states: Dict[str, Dict[str, object]]
    triggered_events: List[Dict[str, object]] = field(default_factory=list)
    media_visibility: int = 0
    humanitarian_index: float = 0.0
    transparency_index: float = 0.0
    player_actions: List[Dict[str, object]] = field(default_factory=list)
    posture_mode: str = "Balanced"


@dataclass
class SimulationSummary:
    """Aggregate metrics after the simulation completes."""

    scenario_id: str
    total_minutes: int
    final_escalation: EscalationLevel
    average_trust: Dict[str, float]
    humanitarian_index: float
    transparency_index: float
    notable_events: List[str]


__all__ = [
    "CrowdEmotion",
    "EscalationLevel",
    "Faction",
    "CrowdState",
    "Scenario",
    "TickReport",
    "SimulationSummary",
]
