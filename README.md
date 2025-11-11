# Riot: Civil Unrest — Kosovo–Serbia Prototype

> **Content Warning**: This interactive prototype explores sensitive themes of civil unrest, diplomacy, and peacekeeping. It is a fictional educational simulation that avoids real-world tactical guidance and emphasizes civilian safety, dialogue, and humanitarian response. Review with local legal and ethics advisors before any public demonstration.

This repository contains a narrative-driven systems prototype for _Riot: Civil Unrest — Kosovo–Serbia_. It focuses on:

- Crowd sentiment simulation with emotional contagion and density modelling.
- Multi-faction morale, trust, and reputation loops influenced by transparent decision-making.
- A political-diplomatic meta layer with media, humanitarian, and legal repercussions.
- Commander, squad, and media observer perspectives with accessibility-conscious UI flows.
- A lightweight 2D GUI map for visualizing Kosovo and Serbian liaison units alongside humanitarian overlays.

The goal is to provide a safe, ethically-aware sandbox to explore non-violent crisis management techniques. All mechanics remain abstract and do **not** offer operational real-world instructions.

## Project Structure

```
├── README.md                  # Project overview and safety notice
├── docs/
│   ├── DESIGN_OVERVIEW.md     # High-level design package
│   └── SAFETY_AND_ETHICS.md   # Ethical guardrails and review checklist
├── data/
│   └── scenarios/
│       └── bridge_of_dialogue.json  # Sample scenario configuration
└── src/
    └── riot_game/
        ├── __init__.py
        ├── __main__.py        # CLI entry point
        ├── config.py          # Loading utilities and constants
        ├── controllers.py     # Player/AI decision layers
        ├── events.py          # Narrative and systemic events
        ├── game.py            # Simulation orchestrator
        ├── loader.py          # Scenario/data loading helpers
        ├── logging_utils.py   # Structured logging helpers
        ├── state.py           # Core data models (factions, crowd, world)
        ├── text_ui.py         # Terminal visualization for the prototype
        └── systems/
            ├── escalation.py
            ├── logistics.py
            ├── media.py
            ├── morale.py
            └── sentiment.py
```

## Quick Start

1. **Install the package** (Python 3.10+ recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
   > The current prototype relies solely on the Python standard library; installation ensures the `riot_game` module is discoverable.

2. **Run the sample scenario** (terminal view):
   ```bash
   python -m riot_game --scenario bridge_of_dialogue
   ```

   Or launch the visual prototype:

   ```bash
   python -m riot_game --scenario bridge_of_dialogue --gui
   ```

3. **Inspect simulation reports**: A structured log is emitted to the terminal and to `simulation_report.json` for further analysis.

## Development Notes

- The simulation is deterministic by default; pass `--seed random` to introduce variation.
- Accessibility toggles (high contrast, verbose descriptions) are available via CLI flags, and the GUI supports adjustable tick delays.
- The game loop abstracts away any real-world operational tactics and focuses on ethical decision-making, negotiation, and humanitarian coordination.
- Contributions must follow the ethical guidelines outlined in `docs/SAFETY_AND_ETHICS.md`.

## License

Released under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. Commercial or militarized usage is strictly prohibited.
