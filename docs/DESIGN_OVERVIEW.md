# Riot: Civil Unrest — Kosovo–Serbia Prototype Design Overview

## Executive Snapshot
The prototype implements a turn-based simulation exploring community tensions and peacekeeping responsibilities in a fictionalized Kosovo–Serbia context. It prioritizes civilian protection, transparency, and non-violent resolution. The tone remains serious, empathetic, and mindful of ethical sensitivities.

## Playable Modes
- **Scenario Simulation**: Command staff orchestrate deployments, humanitarian support, and communication strategies across a dense urban map that now visualizes Kosovo and Serbian liaison formations.
- **Observer Timeline**: Media and NGO perspectives allow players to experience how coverage and aid logistics influence morale and political oversight.
- **Sandbox/Education**: Configurable rule sets to explore negotiation-first solutions. Sensitive data is abstracted or fictionalized.

## Key Systems
1. **Crowd Sentiment & Density**: Emotion states (Calm, Concerned, Agitated, Panicked) propagate via proximity and rumor channels. Density determines collision risks and humanitarian needs.
2. **Morale & Trust Loops**: Each faction carries morale (willingness to cooperate) and trust (confidence in other factions). Ethical choices raise trust; coercive actions reduce it and invite legal scrutiny. Liaison army units from both Kosovo and Serbia participate through a humanitarian lens, reinforcing joint accountability.
3. **Escalation Ladder**: Mission state transitions from Stable → Tense → Volatile → Crisis. Player actions adjust thresholds, and the ladder feeds into oversight and media narratives.
4. **Media & Legal Aftermath**: Transparent reporting improves international support. Suppressing information risks investigative penalties in post-mission reviews.
5. **Logistics Abstraction**: Resource tokens (Medical, Communications, Relief, Mediation) power abilities like “Deploy Mediators” or “Open Humanitarian Corridor.” Supplies regenerate via diplomatic agreements.
6. **Dynamic Events**: Story cards (e.g., “Rumor Surge”, “Unexpected Envoy Visit”, “Weather Shift”) trigger branching outcomes. Each card includes recommended de-escalation responses.

## Accessibility & Safety
- High-contrast UI theme, scalable text, and descriptive tooltips.
- Motion-reduced timeline visualization for sensitive users.
- Ethics guardrails ensure no tactical playbooks or realistic weapon depictions.
- Mandatory content warnings and in-game links to educational resources.

## Technical Pillars
- Modular Python architecture enabling deterministic simulations for academic review.
- Data-driven scenarios powered by JSON and easily inspected logs (JSON + Markdown).
- Separation between simulation core and presentation layer, now including a Tkinter-based command center with interactive map overlays, posture controls, and an action command deck.

## Milestones
1. **Prototype (Current)**: Turn-based CLI prototype plus an interactive 2D GUI command center with action queueing, real-time overlays, liaison unit tracking, and structured mission reporting.
2. **Alpha**: Expanded visual renderer with interactive overlays, advanced AI heuristics, deeper diplomacy loops, co-op network stub.
3. **Beta**: Full narrative campaign, sandbox editor, mod safety filters, educator toolkit.
4. **Release**: Accessibility certification, localization, comprehensive ethics review.

---
*Last updated: 2025-11-11*
