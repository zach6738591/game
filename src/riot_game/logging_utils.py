"""Structured logging helpers for simulation output."""

from __future__ import annotations

from dataclasses import asdict
from typing import List

from .state import TickReport


class SimulationLogger:
    """Collects tick reports for optional persistence."""

    def __init__(self) -> None:
        self._ticks: List[dict] = []

    def capture_tick(self, report: TickReport) -> None:
        payload = asdict(report)
        payload["escalation"] = report.escalation.name
        payload["triggered_events"] = [event.get("name") for event in report.triggered_events]
        self._ticks.append(payload)

    @property
    def ticks(self) -> List[dict]:
        return list(self._ticks)


__all__ = ["SimulationLogger"]
