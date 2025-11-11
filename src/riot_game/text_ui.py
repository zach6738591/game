"""Terminal presentation layer for the prototype."""

from __future__ import annotations

from textwrap import fill
from typing import Dict

from .state import Scenario, SimulationSummary, TickReport


class TextUI:
    """Simple textual renderer with accessibility options."""

    def __init__(self, high_contrast: bool = False, verbose_events: bool = False) -> None:
        self.high_contrast = high_contrast
        self.verbose_events = verbose_events

    def _wrap(self, text: str) -> str:
        return fill(text, width=88)

    def print_intro(self, scenario: Scenario) -> None:
        divider = "=" * 88 if self.high_contrast else "-" * 88
        print(divider)
        print(f"Scenario: {scenario.metadata.get('title', scenario.metadata.get('id'))}")
        print(self._wrap(scenario.metadata.get("summary", "")))
        print("Content Warning:", scenario.metadata.get("content_warning", ""))
        print(divider)

    def render_tick(self, report: TickReport) -> None:
        divider = "#" * 88 if self.high_contrast else "-" * 88
        print(divider)
        print(f"Minute {report.minute:02d} | Escalation: {report.escalation.name}")
        emotion_summary = ", ".join(
            f"{emotion}: {value:.1f}%" for emotion, value in report.crowd_emotions.items()
        )
        print("Crowd Sentiment:", emotion_summary)
        print(
            "Humanitarian Index: "
            f"{report.humanitarian_index:.2f} | Transparency: {report.transparency_index:.2f} | "
            f"Posture: {report.posture_mode}"
        )
        for faction, state in report.faction_states.items():
            print(
                f"[{state['name']}] Morale: {state['morale']:.1f} | Humanitarian: {state['humanitarian']:.1f} | "
                f"Transparency: {state['transparency']:.1f}"
            )
        if report.triggered_events:
            event_names = ", ".join(event.get("name", "Unknown") for event in report.triggered_events)
            print("Events:", event_names)
            if self.verbose_events:
                for event in report.triggered_events:
                    recommendations = event.get("recommended_responses", [])
                    if recommendations:
                        print("  Recommended Responses:")
                        for tip in recommendations:
                            print("   -", tip)
        if report.player_actions:
            print("Player Actions:")
            for action in report.player_actions:
                print(
                    f"  - {action['label']} ({action['acting_faction']})"
                )
        print(divider)

    def render_summary(self, summary: Dict[str, object]) -> None:
        divider = "=" * 88 if self.high_contrast else "-" * 88
        print(divider)
        print("Simulation Complete")
        print(f"Scenario ID: {summary['scenario_id']}")
        print(f"Total Minutes: {summary['total_minutes']}")
        print(f"Final Escalation: {summary['final_escalation']}")
        print("Average Trust Levels:")
        for faction, value in summary["average_trust"].items():
            print(f"  - {faction}: {value:.2f}")
        print(f"Humanitarian Index: {summary['humanitarian_index']:.2f}")
        print(f"Transparency Index: {summary['transparency_index']:.2f}")
        if summary["notable_events"]:
            print("Notable Events:")
            for item in summary["notable_events"]:
                print("  -", item)
        if summary.get("player_actions"):
            print("Player Action Log:")
            for entry in summary["player_actions"]:
                print(f"  - Minute {entry['minute']:02d}: {entry['label']}")
        if summary.get("posture_history"):
            print("Posture History:")
            for change in summary["posture_history"]:
                print(f"  - Minute {change['minute']:02d}: {change['mode']}")
        print(divider)

    def print_log_location(self, path) -> None:
        print(f"Detailed summary written to {path}")


__all__ = ["TextUI"]
