"""Simulation orchestrator."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import asdict
from typing import Dict, Generator, List, Optional

from .controllers import Decision, DecisionEngine
from .events import EventImpact, apply_event
from .player_actions import ActionSpec, PLAYER_ACTIONS
from .state import (
    CrowdEmotion,
    EscalationLevel,
    Scenario,
    SimulationSummary,
    TickReport,
)
from .systems.escalation import EscalationModel
from .systems.logistics import LogisticsSystem
from .systems.media import MediaSystem
from .systems.morale import MoraleSystem
from .systems.sentiment import SentimentAnalyzer


class Simulation:
    """Coordinates scenario progression."""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.random = random.Random(scenario.configuration.initial_seed)
        self.sentiment = SentimentAnalyzer(scenario.crowd)
        self.escalation_model = EscalationModel()
        self.morale_system = MoraleSystem(scenario.factions)
        self.logistics_system = LogisticsSystem(scenario.factions)
        self.media_system = MediaSystem()
        self.decision_engine = DecisionEngine(scenario.factions)
        self._notable_events: List[str] = []
        self._tick_reports: List[TickReport] = []
        self._pending_actions: List[ActionSpec] = []
        self.action_cooldowns: Dict[str, int] = {key: 0 for key in PLAYER_ACTIONS}
        self.player_action_log: List[Dict[str, object]] = []
        self.posture_mode = "Balanced"
        self.posture_history: List[Dict[str, object]] = [
            {"minute": 0, "mode": self.posture_mode}
        ]

        self.minute = 0
        self._duration = scenario.configuration.duration_minutes
        event_queue = self.scenario.sorted_events()
        self._events_iter = iter(event_queue)
        self._next_event: Optional[Dict[str, object]] = next(self._events_iter, None)

    def run(self) -> Generator[TickReport, None, None]:
        while True:
            report = self.advance_one_minute()
            if report is None:
                break
            yield report

    def advance_one_minute(self) -> Optional[TickReport]:
        """Resolve a single simulated minute."""

        if self.minute >= self._duration:
            return None

        triggered: List[Dict[str, object]] = []
        media_visibility = 0
        while self._next_event and int(self._next_event.get("minute", 0)) == self.minute:
            impact = apply_event(self.scenario.factions, self.scenario.crowd, self._next_event)
            triggered.append({**self._next_event, "impact": asdict(impact)})
            media_visibility += impact.media_visibility
            self._notable_events.append(self._next_event.get("name", ""))
            self._next_event = next(self._events_iter, None)

        action_trust, action_bias, applied_actions, action_visibility = self._apply_player_actions()
        media_visibility += action_visibility

        dominant = self.sentiment.dominant_emotion()
        if media_visibility:
            self.media_system.apply_visibility(media_visibility)
        if action_bias:
            self.escalation_model.apply_bias(action_bias)

        trust_effects: Dict[str, Dict[str, float]] = action_trust
        decisions = self.decision_engine.evaluate(
            escalation=self.escalation_model.level,
            dominant_emotion=dominant,
            media_visibility=media_visibility,
        )
        for decision in decisions:
            self._apply_decision(decision, trust_effects)

        self.morale_system.apply_trust(trust_effects)
        self.sentiment.crowd.normalize()
        escalation = self.escalation_model.update(dominant, media_visibility)

        report = TickReport(
            minute=self.minute,
            escalation=escalation,
            crowd_emotions=self.sentiment.as_percentages(),
            faction_states=self._snapshot_factions(),
            triggered_events=triggered,
            media_visibility=media_visibility,
            humanitarian_index=self.logistics_system.snapshot(),
            transparency_index=self.media_system.snapshot(),
            player_actions=applied_actions,
            posture_mode=self.posture_mode,
        )
        self._tick_reports.append(report)

        self.minute += self.scenario.configuration.time_step
        self._decrement_cooldowns()
        return report

    def _apply_decision(self, decision: Decision, trust_effects: Dict[str, Dict[str, float]]) -> None:
        morale_adjustment = decision.morale_delta + self.random.uniform(-0.2, 0.4)
        self.morale_system.apply_morale(decision.faction_id, morale_adjustment)
        humanitarian_adjustment = decision.humanitarian_delta + self.random.uniform(-0.1, 0.3)
        self.logistics_system.apply_decision(decision.faction_id, humanitarian_adjustment)
        transparency_adjustment = decision.transparency_delta + self.random.uniform(-0.15, 0.35)
        self.media_system.apply_decision(transparency_adjustment)
        existing = trust_effects.setdefault(decision.faction_id, {})
        for target, delta in decision.trust_effects.items():
            existing[target] = existing.get(target, 0.0) + delta + self.random.uniform(-0.2, 0.4)

    def _snapshot_factions(self) -> Dict[str, Dict[str, float]]:
        snapshot: Dict[str, Dict[str, float]] = {}
        for faction in self.scenario.factions.values():
            snapshot[faction.identifier] = {
                "name": faction.name,
                "morale": faction.morale,
                "humanitarian": self.logistics_system.snapshot(),
                "transparency": self.media_system.snapshot(),
                "trust": dict(faction.trust),
                "resources": dict(faction.resources),
            }
        return snapshot

    def _apply_player_actions(self) -> tuple[Dict[str, Dict[str, float]], float, List[Dict[str, object]], int]:
        """Apply queued player actions and return their aggregated impacts."""

        if not self._pending_actions:
            return {}, 0.0, [], 0

        trust_effects: Dict[str, Dict[str, float]] = defaultdict(dict)
        escalation_bias = 0.0
        applied: List[Dict[str, object]] = []
        visibility = 0

        for action in list(self._pending_actions):
            for faction_id, delta in action.effect.morale.items():
                self.morale_system.apply_morale(faction_id, delta)
            for source, targets in action.effect.trust.items():
                dest = trust_effects[source]
                for target, delta in targets.items():
                    dest[target] = dest.get(target, 0.0) + delta
            if action.effect.crowd_shift:
                self.sentiment.crowd.shift(dict(action.effect.crowd_shift))
            if action.effect.humanitarian:
                self.logistics_system.apply_decision(action.acting_faction, action.effect.humanitarian)
            if action.effect.transparency:
                self.media_system.apply_decision(action.effect.transparency)
            visibility += action.effect.media_visibility
            escalation_bias += action.effect.escalation_bias
            applied.append(
                {
                    "id": action.identifier,
                    "label": action.label,
                    "description": action.description,
                    "acting_faction": action.acting_faction,
                }
            )
            self.player_action_log.append(
                {
                    "minute": self.minute,
                    "id": action.identifier,
                    "label": action.label,
                }
            )

        self._pending_actions.clear()
        normalized_trust = {source: dict(targets) for source, targets in trust_effects.items()}
        return normalized_trust, escalation_bias, applied, visibility

    def _decrement_cooldowns(self) -> None:
        for action_id, value in self.action_cooldowns.items():
            if value > 0:
                self.action_cooldowns[action_id] = value - 1

    def issue_player_action(self, action_id: str) -> tuple[bool, str]:
        """Queue a player action if resources and cooldown permit."""

        spec = PLAYER_ACTIONS.get(action_id)
        if not spec:
            return False, "Unknown action"
        if self.action_cooldowns.get(action_id, 0) > 0:
            return False, "Action is recharging"

        faction = self.scenario.factions.get(spec.acting_faction)
        if faction is None:
            return False, "Acting faction unavailable"

        for resource, cost in spec.resource_costs.items():
            if faction.resources.get(resource, 0) < cost:
                return False, f"Insufficient {resource}"

        for resource, cost in spec.resource_costs.items():
            faction.spend_resource(resource, cost)

        self._pending_actions.append(spec)
        self.action_cooldowns[action_id] = spec.cooldown
        return True, f"Queued {spec.label}"

    def get_action_statuses(self) -> List[Dict[str, object]]:
        statuses: List[Dict[str, object]] = []
        for action_id, spec in PLAYER_ACTIONS.items():
            faction = self.scenario.factions.get(spec.acting_faction)
            resources = {
                resource: (faction.resources.get(resource, 0) if faction else 0)
                for resource in spec.resource_costs
            }
            affordable = all(resources[res] >= cost for res, cost in spec.resource_costs.items())
            statuses.append(
                {
                    "id": action_id,
                    "label": spec.label,
                    "description": spec.description,
                    "acting_faction": spec.acting_faction,
                    "costs": dict(spec.resource_costs),
                    "cooldown": self.action_cooldowns.get(action_id, 0),
                    "available": affordable and self.action_cooldowns.get(action_id, 0) == 0,
                    "resources": resources,
                }
            )
        return statuses

    def set_posture(self, mode: str) -> None:
        posture_map = {
            "Supportive": -0.35,
            "Balanced": 0.0,
            "Assertive": 0.25,
        }
        bias = posture_map.get(mode, 0.0)
        self.posture_mode = mode
        self.escalation_model.set_posture_bias(bias)
        self.posture_history.append({"minute": self.minute, "mode": mode})

    def summary(self) -> Dict[str, object]:
        return {
            "scenario_id": self.scenario.metadata.get("id", "unknown"),
            "total_minutes": self.scenario.configuration.duration_minutes,
            "final_escalation": self.escalation_model.level.name,
            "average_trust": self.morale_system.aggregate_average_trust(),
            "humanitarian_index": self.logistics_system.snapshot(),
            "transparency_index": self.media_system.snapshot(),
            "notable_events": [event for event in self._notable_events if event],
            "player_actions": list(self.player_action_log),
            "posture_history": list(self.posture_history),
        }


__all__ = ["Simulation"]
