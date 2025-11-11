"""Event handling and transformation logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .state import CrowdEmotion, CrowdState, Faction


@dataclass
class EventImpact:
    """Normalized impact extracted from scenario data."""

    crowd_shift: Dict[CrowdEmotion, float]
    trust_delta: Dict[str, float]
    resource_costs: Dict[str, int]
    media_visibility: int
    narrative: str
    recommended_responses: List[str]


def parse_event(event: Dict[str, object]) -> EventImpact:
    impact = event.get("impact", {})
    crowd_shift = {
        CrowdEmotion[key.upper()]: float(value)
        for key, value in impact.get("crowd_state_shift", {}).items()
    }
    resource_costs = {k: int(v) for k, v in impact.get("logistics_cost", {}).items()}
    trust_delta = {k: float(v) for k, v in impact.get("trust_delta", {}).items()}
    return EventImpact(
        crowd_shift=crowd_shift,
        trust_delta=trust_delta,
        resource_costs=resource_costs,
        media_visibility=int(impact.get("media_visibility", 0)),
        narrative=str(event.get("name", "")),
        recommended_responses=[str(r) for r in event.get("recommended_responses", [])],
    )


def apply_event(
    factions: Dict[str, Faction], crowd: CrowdState, event: Dict[str, object]
) -> EventImpact:
    impact = parse_event(event)
    if impact.crowd_shift:
        crowd.shift(impact.crowd_shift)
    for faction_id, delta in impact.trust_delta.items():
        if faction_id in factions:
            for other_id in factions:
                if other_id != faction_id:
                    factions[other_id].adjust_trust(faction_id, delta)
    for faction in factions.values():
        for resource, cost in impact.resource_costs.items():
            if cost > 0:
                faction.spend_resource(resource, min(cost, faction.resources.get(resource, 0)))
    return impact


__all__ = ["apply_event", "parse_event", "EventImpact"]
