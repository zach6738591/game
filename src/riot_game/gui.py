"""Simple 2D GUI visualisation for the riot simulation."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from typing import Dict, Iterator, Optional

from .game import Simulation
from .state import Scenario, TickReport

EMOTION_COLORS: Dict[str, str] = {
    "calm": "#3AAFA9",
    "concerned": "#F5B642",
    "agitated": "#C94C4C",
    "panicked": "#7A2F2F",
}

FACTION_COLORS = [
    "#2F71B7",
    "#7A5195",
    "#45B29D",
    "#EF8354",
    "#5C6B73",
    "#F6AE2D",
]


class SimulationGUI:
    """Render the simulation via a high-level 2D interface."""

    def __init__(
        self,
        simulation: Simulation,
        scenario: Scenario,
        tick_delay_ms: int = 750,
        log_path: Optional[Path] = None,
    ) -> None:
        self.simulation = simulation
        self.scenario = scenario
        self.tick_delay_ms = tick_delay_ms
        self.log_path = log_path

        self._tick_iterator: Optional[Iterator[TickReport]] = None
        self._faction_widgets: Dict[str, Dict[str, int]] = {}
        self._emotion_widgets: Dict[str, Dict[str, int]] = {}
        self._unit_widgets: list[int] = []
        self._summary_window: Optional[tk.Toplevel] = None

        self.root = tk.Tk()
        self.root.title(
            f"Riot: Civil Unrest — Kosovo–Serbia Prototype — {scenario.metadata.get('title', 'Scenario')}"
        )
        self.root.geometry("960x640")
        self.root.configure(bg="#101820")
        self.canvas = tk.Canvas(self.root, width=960, height=640, bg="#101820", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._create_static_layers()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def launch(self) -> None:
        """Start the GUI loop and simulation updates."""

        self._tick_iterator = self.simulation.run()
        self.root.after(100, self._advance_simulation)
        self.root.mainloop()

    # ------------------------------------------------------------------
    # GUI construction helpers
    def _create_static_layers(self) -> None:
        # Background panels
        self.canvas.create_rectangle(20, 20, 300, 620, fill="#172935", outline="")
        self.canvas.create_rectangle(320, 20, 940, 620, fill="#1F2E3A", outline="")

        self.canvas.create_text(
            160,
            40,
            text="Crowd Sentiment",
            fill="#F5F7FA",
            font=("Source Sans Pro", 18, "bold"),
        )
        self.canvas.create_text(
            630,
            40,
            text="Operational Overview",
            fill="#F5F7FA",
            font=("Source Sans Pro", 18, "bold"),
        )
        self.canvas.create_text(
            160,
            320,
            text="Factions",
            fill="#F5F7FA",
            font=("Source Sans Pro", 18, "bold"),
        )

        # Emotion bars setup
        base_y = 90
        for idx, emotion in enumerate(["calm", "concerned", "agitated", "panicked"]):
            y = base_y + idx * 50
            self.canvas.create_text(60, y, text=emotion.title(), anchor="w", fill="#E0E6ED")
            bar_bg = self.canvas.create_rectangle(60, y + 15, 260, y + 30, fill="#0F1A24", outline="#274050")
            bar = self.canvas.create_rectangle(60, y + 15, 60, y + 30, fill=EMOTION_COLORS[emotion], outline="")
            value = self.canvas.create_text(260, y + 22, text="0%", anchor="e", fill="#F5F7FA")
            self._emotion_widgets[emotion] = {"bar": bar, "value": value, "background": bar_bg}

        # Faction cards placeholder area
        faction_ids = list(self.scenario.factions.keys())
        for idx, faction_id in enumerate(faction_ids):
            color = FACTION_COLORS[idx % len(FACTION_COLORS)]
            top = 340 + (idx * 55)
            rect = self.canvas.create_rectangle(40, top, 280, top + 45, outline="", fill=color)
            name_text = self.canvas.create_text(50, top + 12, anchor="w", fill="#F5F7FA", text="")
            morale_text = self.canvas.create_text(50, top + 28, anchor="w", fill="#F5F7FA", text="")
            trust_text = self.canvas.create_text(50, top + 40, anchor="w", fill="#DDE9F5", text="")
            self._faction_widgets[faction_id] = {
                "background": rect,
                "name": name_text,
                "morale": morale_text,
                "trust": trust_text,
            }

        # Map area border
        self.canvas.create_rectangle(340, 80, 920, 600, outline="#2F71B7", width=2)
        self.canvas.create_text(
            630,
            70,
            text="Humanitarian Map",
            fill="#F5F7FA",
            font=("Source Sans Pro", 16, "bold"),
        )

        # Legend for unit types
        self.canvas.create_text(360, 590, anchor="w", fill="#F5F7FA", text="Legend: circles = unit groups, squares = aid hubs")

        # Render static humanitarian markers
        for idx, hotspot in enumerate(self.scenario.crowd.density_hotspots):
            x = 360 + (idx * 180)
            self.canvas.create_rectangle(x, 520, x + 30, 550, fill="#F6AE2D", outline="")
            self.canvas.create_text(x + 15, 560, text=hotspot.get("name", ""), anchor="n", fill="#F5F7FA")

        # Unit group placeholders
        self._draw_units()

    def _draw_units(self) -> None:
        if not self.scenario.unit_groups:
            return
        map_width = 920 - 340
        map_height = 600 - 80
        for idx, group in enumerate(self.scenario.unit_groups):
            fraction_x, fraction_y = group.get("position", [0.5, 0.5])
            x = 340 + max(0.05, min(0.95, float(fraction_x))) * map_width
            y = 80 + max(0.05, min(0.95, float(fraction_y))) * map_height
            color = FACTION_COLORS[idx % len(FACTION_COLORS)]
            radius = 12 + (float(group.get("strength", 1)) * 2)
            circle = self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=color,
                outline="",
            )
            label = self.canvas.create_text(
                x,
                y + radius + 12,
                text=f"{group.get('name', 'Unit')}\n{group.get('posture', '')}",
                fill="#F5F7FA",
                font=("Source Sans Pro", 11),
                justify=tk.CENTER,
            )
            self._unit_widgets.extend([circle, label])

    # ------------------------------------------------------------------
    # Simulation update pipeline
    def _advance_simulation(self) -> None:
        if self._tick_iterator is None:
            return
        try:
            report = next(self._tick_iterator)
        except StopIteration:
            self._handle_completion()
            return
        self._render_tick(report)
        self.root.after(self.tick_delay_ms, self._advance_simulation)

    def _render_tick(self, report: TickReport) -> None:
        for emotion, widgets in self._emotion_widgets.items():
            value = report.crowd_emotions.get(emotion, 0.0)
            width = 200 * (value / 100.0)
            y1, y2 = self._bar_vertical_bounds(widgets["bar"])
            self.canvas.coords(widgets["bar"], 60, y1, 60 + width, y2)
            self.canvas.itemconfigure(widgets["value"], text=f"{value:.1f}%")

        for faction_id, widgets in self._faction_widgets.items():
            state = report.faction_states.get(faction_id, {})
            name = state.get("name", faction_id)
            morale = state.get("morale", 0.0)
            trust_map = state.get("trust", {})
            average_trust = 0.0
            if trust_map:
                average_trust = sum(trust_map.values()) / len(trust_map)
            self.canvas.itemconfigure(widgets["name"], text=name)
            self.canvas.itemconfigure(widgets["morale"], text=f"Morale: {morale:.1f}")
            self.canvas.itemconfigure(
                widgets["trust"],
                text=f"Avg. Trust: {average_trust:.1f}",
            )

        # Update title with minute/escalation
        self.root.title(
            f"Minute {report.minute} — Escalation: {report.escalation.name.title()} — {self.scenario.metadata.get('title', '')}"
        )

        # Display latest notable events within map area
        y_base = 100
        self.canvas.delete("event_text")
        self.canvas.create_text(
            860,
            90,
            text="Events",
            fill="#F5F7FA",
            font=("Source Sans Pro", 16, "bold"),
            tags="event_text",
        )
        for idx, event in enumerate(report.triggered_events[:5]):
            label = event.get("name", "Event")
            self.canvas.create_text(
                860,
                y_base + idx * 24,
                text=f"• {label}",
                fill="#E0E6ED",
                anchor="e",
                font=("Source Sans Pro", 12),
                tags="event_text",
            )

    def _handle_completion(self) -> None:
        summary = self.simulation.summary()
        if self.log_path:
            self.log_path.write_text(json.dumps(summary, indent=2))
        self._show_summary(summary)

    def _show_summary(self, summary: Dict[str, object]) -> None:
        if self._summary_window:
            return
        window = tk.Toplevel(self.root)
        window.title("Simulation Summary")
        window.geometry("420x360")
        window.configure(bg="#1F2E3A")
        header = tk.Label(
            window,
            text="Simulation Complete",
            bg="#1F2E3A",
            fg="#F5F7FA",
            font=("Source Sans Pro", 16, "bold"),
        )
        header.pack(pady=10)

        for key, value in summary.items():
            text = tk.Text(
                window,
                height=2,
                wrap=tk.WORD,
                bg="#172935",
                fg="#F5F7FA",
                relief=tk.FLAT,
            )
            text.insert(tk.END, f"{key}:\n{value}")
            text.configure(state=tk.DISABLED)
            text.pack(fill=tk.X, padx=12, pady=4)

        close_button = tk.Button(
            window,
            text="Close",
            command=self._on_close,
            bg="#2F71B7",
            fg="#F5F7FA",
            activebackground="#254B7C",
        )
        close_button.pack(pady=12)
        self._summary_window = window

    def _on_close(self) -> None:
        self.root.quit()
        self.root.destroy()

    def _bar_vertical_bounds(self, bar_id: int) -> tuple[float, float]:
        x1, y1, x2, y2 = self.canvas.coords(bar_id)
        return y1, y2


__all__ = ["SimulationGUI"]
