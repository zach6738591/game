"""Scenario loading utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .config import DATA_PATH, AccessibilityConfig, ScenarioConfiguration
from .state import CrowdEmotion, CrowdState, Faction, Scenario


@dataclass
class RawScenario:
    metadata: Dict[str, object]
    configuration: Dict[str, object]
    factions: list[Dict[str, object]]
    crowd: Dict[str, object]
    event_deck: list[Dict[str, object]]
    unit_groups: list[Dict[str, object]]
    map_layout: Dict[str, object]


def _load_json(identifier: str) -> RawScenario:
    path = DATA_PATH / f"{identifier}.json"
    if not path.exists():  # pragma: no cover - user feedback path
        raise FileNotFoundError(
            f"Scenario '{identifier}' not found at {path}. Available files: "
            f"{[p.stem for p in DATA_PATH.glob('*.json')]}"
        )
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return RawScenario(
        metadata=payload.get("metadata", {}),
        configuration=payload.get("configuration", {}),
        factions=payload.get("factions", []),
        crowd=payload.get("crowd", {}),
        event_deck=payload.get("event_deck", []),
        unit_groups=payload.get("unit_groups", []),
        map_layout=payload.get("map", {}),
    )


def _build_accessibility(config: Dict[str, object]) -> AccessibilityConfig:
    access = config.get("accessibility", {})
    return AccessibilityConfig(
        high_contrast=bool(access.get("high_contrast", False)),
        verbose_events=bool(access.get("verbose_events", False)),
    )


def _build_configuration(raw: RawScenario) -> ScenarioConfiguration:
    config = raw.configuration
    accessibility = _build_accessibility(config)
    return ScenarioConfiguration(
        duration_minutes=int(config.get("duration_minutes", 30)),
        time_step=int(config.get("time_step", 1)),
        initial_seed=int(config.get("initial_seed", 0)),
        accessibility=accessibility,
    )


def _build_factions(raw: RawScenario) -> Dict[str, Faction]:
    factions: Dict[str, Faction] = {}
    for entry in raw.factions:
        faction = Faction(
            identifier=str(entry["id"]),
            name=str(entry.get("name", entry["id"])),
            role=str(entry.get("role", "")),
            morale=float(entry.get("initial_morale", 50.0)),
            trust={k: float(v) for k, v in entry.get("initial_trust", {}).items()},
            resources={k: int(v) for k, v in entry.get("resources", {}).items()},
        )
        factions[faction.identifier] = faction
    return factions


def _build_crowd(raw: RawScenario) -> CrowdState:
    distribution = {
        CrowdEmotion[key.upper()]: float(value)
        for key, value in raw.crowd.get("initial_state_distribution", {}).items()
    }
    crowd = CrowdState(
        population=int(raw.crowd.get("population", 0)),
        emotion_distribution=distribution,
        density_hotspots=list(raw.crowd.get("density_hotspots", [])),
    )
    crowd.normalize()
    return crowd


def load_scenario(identifier: str) -> Scenario:
    """Load and normalize a scenario by identifier."""

    raw = _load_json(identifier)
    configuration = _build_configuration(raw)
    factions = _build_factions(raw)
    crowd = _build_crowd(raw)
    return Scenario(
        metadata={str(k): str(v) for k, v in raw.metadata.items()},
        configuration=configuration,
        factions=factions,
        crowd=crowd,
        event_deck=raw.event_deck,
        unit_groups=list(raw.unit_groups),
        map_layout=dict(raw.map_layout),
    )


__all__ = ["load_scenario"]
