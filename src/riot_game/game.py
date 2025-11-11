"""Simulation orchestrator."""

from __future__ import annotations

import random
from dataclasses import asdict
from typing import Dict, Generator, List

from .controllers import Decision, DecisionEngine
from .events import EventImpact, apply_event
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

    def run(self) -> Generator[TickReport, None, None]:
        minute = 0
        event_queue = self.scenario.sorted_events()
        events_iter = iter(event_queue)
        next_event = next(events_iter, None)

        while minute < self.scenario.configuration.duration_minutes:
            triggered: List[Dict[str, object]] = []
            media_visibility = 0
            while next_event and int(next_event.get("minute", 0)) == minute:
                impact = apply_event(self.scenario.factions, self.scenario.crowd, next_event)
                triggered.append({**next_event, "impact": asdict(impact)})
                media_visibility += impact.media_visibility
                self._notable_events.append(next_event.get("name", ""))
                next_event = next(events_iter, None)

            dominant = self.sentiment.dominant_emotion()
            if media_visibility:
                self.media_system.apply_visibility(media_visibility)

            decisions = self.decision_engine.evaluate(
                escalation=self.escalation_model.level,
                dominant_emotion=dominant,
                media_visibility=media_visibility,
            )
            trust_effects: Dict[str, Dict[str, float]] = {}
            for decision in decisions:
                self._apply_decision(decision, trust_effects)

            self.morale_system.apply_trust(trust_effects)
            self.sentiment.crowd.normalize()
            escalation = self.escalation_model.update(dominant, media_visibility)

            report = TickReport(
                minute=minute,
                escalation=escalation,
                crowd_emotions=self.sentiment.as_percentages(),
                faction_states=self._snapshot_factions(),
                triggered_events=triggered,
                media_visibility=media_visibility,
            )
            self._tick_reports.append(report)
            yield report

            minute += self.scenario.configuration.time_step

    def _apply_decision(self, decision: Decision, trust_effects: Dict[str, Dict[str, float]]) -> None:
        morale_adjustment = decision.morale_delta + self.random.uniform(-0.2, 0.4)
        self.morale_system.apply_morale(decision.faction_id, morale_adjustment)
        humanitarian_adjustment = decision.humanitarian_delta + self.random.uniform(-0.1, 0.3)
        self.logistics_system.apply_decision(decision.faction_id, humanitarian_adjustment)
        transparency_adjustment = decision.transparency_delta + self.random.uniform(-0.15, 0.35)
        self.media_system.apply_decision(transparency_adjustment)
        trust_effects[decision.faction_id] = {target: delta + self.random.uniform(-0.2, 0.4) for target, delta in decision.trust_effects.items()}

    def _snapshot_factions(self) -> Dict[str, Dict[str, float]]:
        snapshot: Dict[str, Dict[str, float]] = {}
        for faction in self.scenario.factions.values():
            snapshot[faction.identifier] = {
                "name": faction.name,
                "morale": faction.morale,
                "humanitarian": self.logistics_system.snapshot(),
                "transparency": self.media_system.snapshot(),
                "trust": dict(faction.trust),
            }
        return snapshot

    def summary(self) -> Dict[str, object]:
        return {
            "scenario_id": self.scenario.metadata.get("id", "unknown"),
            "total_minutes": self.scenario.configuration.duration_minutes,
            "final_escalation": self.escalation_model.level.name,
            "average_trust": self.morale_system.aggregate_average_trust(),
            "humanitarian_index": self.logistics_system.snapshot(),
            "transparency_index": self.media_system.snapshot(),
            "notable_events": [event for event in self._notable_events if event],
        }


__all__ = ["Simulation"]
