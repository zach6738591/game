"""High-level player action definitions for the GUI command deck."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping

from .state import CrowdEmotion


@dataclass(frozen=True)
class ActionEffect:
    """Effect payload applied when a player-triggered action resolves."""

    crowd_shift: Mapping[CrowdEmotion, float] = field(default_factory=dict)
    morale: Mapping[str, float] = field(default_factory=dict)
    trust: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    humanitarian: float = 0.0
    transparency: float = 0.0
    media_visibility: int = 0
    escalation_bias: float = 0.0


@dataclass(frozen=True)
class ActionSpec:
    """Describes a player-initiated strategic action."""

    identifier: str
    label: str
    description: str
    acting_faction: str
    resource_costs: Mapping[str, int]
    cooldown: int
    effect: ActionEffect


def _trust_map(source: str, targets: Iterable[str], value: float) -> Dict[str, Dict[str, float]]:
    return {source: {target: value for target in targets}}


PLAYER_ACTIONS: Dict[str, ActionSpec] = {
    "community_dialogue_forum": ActionSpec(
        identifier="community_dialogue_forum",
        label="Community Dialogue Forum",
        description=(
            "Host a dialogue circle moderated by civic leaders and humanitarian observers to reduce agitation "
            "and reinforce civilian-first priorities."
        ),
        acting_faction="kosovo_civil_security",
        resource_costs={"mediation": 1, "communications": 1},
        cooldown=4,
        effect=ActionEffect(
            crowd_shift={
                CrowdEmotion.CALM: 0.06,
                CrowdEmotion.CONCERNED: -0.03,
                CrowdEmotion.AGITATED: -0.03,
            },
            morale={"kosovo_civil_security": 1.8, "local_serb_community": 1.2},
            trust=_trust_map(
                "kosovo_civil_security",
                [
                    "local_serb_community",
                    "serbian_gendarmerie",
                    "serbian_defense_liaison",
                ],
                2.4,
            ),
            humanitarian=0.4,
            transparency=1.0,
            media_visibility=1,
            escalation_bias=-0.2,
        ),
    ),
    "joint_security_walk": ActionSpec(
        identifier="joint_security_walk",
        label="Joint Security Walk",
        description=(
            "Deploy Kosovo and Serbian liaison units on a coordinated reassurance walk, demonstrating unity "
            "and focusing on de-escalation."
        ),
        acting_faction="serbian_gendarmerie",
        resource_costs={"mediation": 1},
        cooldown=3,
        effect=ActionEffect(
            crowd_shift={
                CrowdEmotion.CALM: 0.04,
                CrowdEmotion.CONCERNED: -0.02,
                CrowdEmotion.AGITATED: -0.02,
            },
            morale={"serbian_gendarmerie": 1.4, "kosovo_security_force": 1.1},
            trust={
                "serbian_gendarmerie": {
                    "kosovo_civil_security": 1.8,
                    "kosovo_security_force": 2.0,
                }
            },
            humanitarian=0.6,
            transparency=0.8,
            media_visibility=2,
            escalation_bias=-0.25,
        ),
    ),
    "humanitarian_airlift": ActionSpec(
        identifier="humanitarian_airlift",
        label="Humanitarian Airlift",
        description=(
            "Coordinate with KFOR to rapidly deliver medical and relief packages via airlift, strengthening "
            "corridor security and community trust."
        ),
        acting_faction="kfor",
        resource_costs={"relief": 2, "medical": 1},
        cooldown=5,
        effect=ActionEffect(
            crowd_shift={
                CrowdEmotion.CALM: 0.05,
                CrowdEmotion.CONCERNED: -0.02,
                CrowdEmotion.PANICKED: -0.03,
            },
            morale={"kfor": 1.5, "ngo_media": 1.0},
            trust={
                "kfor": {
                    "kosovo_civil_security": 2.2,
                    "serbian_gendarmerie": 2.0,
                    "serbian_defense_liaison": 1.8,
                    "local_serb_community": 2.4,
                }
            },
            humanitarian=2.6,
            transparency=1.2,
            media_visibility=3,
            escalation_bias=-0.35,
        ),
    ),
    "media_transparency_forum": ActionSpec(
        identifier="media_transparency_forum",
        label="Transparency Forum",
        description=(
            "NGO and media coalitions host a live transparency forum, publishing fact-checked updates and "
            "highlighting peaceful cooperation."
        ),
        acting_faction="ngo_media",
        resource_costs={"communications": 2},
        cooldown=3,
        effect=ActionEffect(
            crowd_shift={
                CrowdEmotion.CALM: 0.03,
                CrowdEmotion.CONCERNED: -0.02,
            },
            morale={"ngo_media": 1.0, "kfor": 0.6},
            trust={
                "ngo_media": {
                    "kosovo_civil_security": 1.6,
                    "local_serb_community": 2.0,
                    "serbian_defense_liaison": 1.2,
                }
            },
            humanitarian=0.3,
            transparency=3.0,
            media_visibility=4,
            escalation_bias=-0.15,
        ),
    ),
    "evacuation_corridor": ActionSpec(
        identifier="evacuation_corridor",
        label="Secure Evacuation Corridor",
        description=(
            "Open a protected humanitarian lane with Kosovo Security Force escorts and medical teams to reassure "
            "vulnerable attendees."
        ),
        acting_faction="kosovo_security_force",
        resource_costs={"medical": 1, "relief": 1},
        cooldown=4,
        effect=ActionEffect(
            crowd_shift={
                CrowdEmotion.CALM: 0.05,
                CrowdEmotion.PANICKED: -0.04,
                CrowdEmotion.AGITATED: -0.01,
            },
            morale={"kosovo_security_force": 1.7, "kosovo_civil_security": 1.2},
            trust={
                "kosovo_security_force": {
                    "local_serb_community": 2.1,
                    "kfor": 1.5,
                }
            },
            humanitarian=1.8,
            transparency=0.9,
            media_visibility=2,
            escalation_bias=-0.3,
        ),
    ),
}


__all__ = ["ActionSpec", "ActionEffect", "PLAYER_ACTIONS"]
