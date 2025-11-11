"""Configuration constants for the Riot: Civil Unrest prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT_PATH / "data" / "scenarios"
DEFAULT_OUTPUT_PATH = ROOT_PATH / "simulation_report.json"


@dataclass
class AccessibilityConfig:
    """Accessibility toggles."""

    high_contrast: bool = False
    verbose_events: bool = False


@dataclass
class ScenarioConfiguration:
    """Simulation configuration metadata."""

    duration_minutes: int
    time_step: int
    initial_seed: int
    accessibility: AccessibilityConfig


__all__ = [
    "ROOT_PATH",
    "DATA_PATH",
    "DEFAULT_OUTPUT_PATH",
    "AccessibilityConfig",
    "ScenarioConfiguration",
]
