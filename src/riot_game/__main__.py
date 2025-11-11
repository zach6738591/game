"""Command line entry point for the Riot: Civil Unrest prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import DEFAULT_OUTPUT_PATH
from .game import Simulation
from .gui import SimulationGUI
from .loader import load_scenario
from .logging_utils import SimulationLogger
from .text_ui import TextUI


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fictionalized, ethics-focused simulation of civic unrest and "
            "peacekeeping dynamics."
        )
    )
    parser.add_argument(
        "--scenario",
        default="bridge_of_dialogue",
        help="Scenario identifier located in data/scenarios/",
    )
    parser.add_argument(
        "--seed",
        default="fixed",
        help="Random seed (integer) or 'random' for entropy-based seeding.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Override scenario duration in minutes (optional).",
    )
    parser.add_argument(
        "--high-contrast",
        action="store_true",
        help="Enable high contrast text output for accessibility.",
    )
    parser.add_argument(
        "--verbose-events",
        action="store_true",
        help="Print expanded descriptions for every triggered event.",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Skip writing simulation_report.json",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the high-level 2D GUI instead of the terminal view.",
    )
    parser.add_argument(
        "--tick-delay",
        type=int,
        default=750,
        help="GUI only: delay in milliseconds between simulated minutes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scenario = load_scenario(args.scenario)

    if args.duration:
        scenario.configuration.duration_minutes = args.duration

    if args.seed == "random":
        from random import SystemRandom

        scenario.configuration.initial_seed = SystemRandom().randint(0, 2**31 - 1)
    elif args.seed in {"fixed", "default"}:
        pass
    else:
        try:
            scenario.configuration.initial_seed = int(args.seed)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise SystemExit(f"Invalid seed value: {args.seed}") from exc

    sim = Simulation(scenario)

    if args.gui:
        log_path: Path | None = None
        if not args.no_log:
            log_path = Path(DEFAULT_OUTPUT_PATH)
        gui = SimulationGUI(
            simulation=sim,
            scenario=scenario,
            tick_delay_ms=max(100, args.tick_delay),
            log_path=log_path,
        )
        gui.launch()
        return 0

    ui = TextUI(
        high_contrast=args.high_contrast or scenario.configuration.accessibility.high_contrast,
        verbose_events=args.verbose_events or scenario.configuration.accessibility.verbose_events,
    )
    logger = SimulationLogger()

    ui.print_intro(scenario)
    for tick_report in sim.run():
        ui.render_tick(tick_report)
        logger.capture_tick(tick_report)

    summary = sim.summary()
    ui.render_summary(summary)
    if not args.no_log:
        output_path = Path(DEFAULT_OUTPUT_PATH)
        output_path.write_text(json.dumps(summary, indent=2))
        ui.print_log_location(output_path)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main(sys.argv[1:]))
