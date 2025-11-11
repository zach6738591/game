"""Advanced 2D GUI visualisation for the riot simulation."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .game import Simulation
from .player_actions import PLAYER_ACTIONS
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
    "#4E8098",
    "#7FB069",
]

ZONE_COLOR_PRESETS = {
    "civic": "#1F3B57",
    "residential": "#273C5A",
    "river": "#123049",
    "market": "#2F4C64",
    "aid": "#324F5A",
}


def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: Sequence[int]) -> str:
    r, g, b = [max(0, min(255, value)) for value in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"


def _blend_colors(entries: Sequence[Tuple[str, float]]) -> str:
    total_weight = sum(weight for _, weight in entries)
    if total_weight <= 0:
        return "#2F71B7"
    r = g = b = 0.0
    for color, weight in entries:
        cr, cg, cb = _hex_to_rgb(color)
        r += cr * weight
        g += cg * weight
        b += cb * weight
    return _rgb_to_hex((int(r / total_weight), int(g / total_weight), int(b / total_weight)))


def _morale_color(base_color: str, morale: float) -> str:
    normalized = max(0.0, min(1.0, morale / 100.0))
    factor = 0.45 + normalized * 0.55
    r, g, b = _hex_to_rgb(base_color)
    return _rgb_to_hex((int(r * factor), int(g * factor), int(b * factor)))


class SimulationGUI:
    """Render the simulation via an interactive, command-driven GUI."""

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

        self._paused = False
        self._after_id: Optional[str] = None
        self._latest_report: Optional[TickReport] = None
        self._log_messages: List[str] = []

        self.root = tk.Tk()
        self.root.title(
            f"Riot: Civil Unrest — Kosovo–Serbia Prototype — {scenario.metadata.get('title', 'Scenario')}"
        )
        self.root.geometry("1280x760")
        self.root.configure(bg="#101820")
        self.root.minsize(1100, 720)

        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:  # pragma: no cover - fallback when theme missing
            pass
        self.style.configure("Dark.TFrame", background="#101820")
        self.style.configure("Panel.TFrame", background="#172935")
        self.style.configure("Panel.TLabel", background="#172935", foreground="#F5F7FA")
        self.style.configure("Heading.TLabel", font=("Source Sans Pro", 18, "bold"), foreground="#F5F7FA")
        self.style.configure("Info.TLabel", font=("Source Sans Pro", 13), foreground="#DDE9F5")
        self.style.configure("Action.TButton", font=("Source Sans Pro", 11, "bold"))

        self.root.columnconfigure(0, weight=2)
        self.root.columnconfigure(1, weight=3)
        self.root.columnconfigure(2, weight=2)
        self.root.rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        self._build_bottom_bar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._refresh_faction_rows()
        self._refresh_action_buttons()

    # ------------------------------------------------------------------
    # Layout construction
    def _build_top_bar(self) -> None:
        frame = ttk.Frame(self.root, style="Dark.TFrame", padding=(16, 10))
        frame.grid(row=0, column=0, columnspan=3, sticky="nsew")

        self.title_var = tk.StringVar(value=self.scenario.metadata.get("title", "Scenario"))
        ttk.Label(frame, textvariable=self.title_var, style="Heading.TLabel").pack(side=tk.LEFT)

        spacer = ttk.Frame(frame, style="Dark.TFrame")
        spacer.pack(side=tk.LEFT, expand=True)

        self.time_var = tk.StringVar(value="Minute 00")
        self.escalation_var = tk.StringVar(value="Escalation: Stable")
        self.metrics_var = tk.StringVar(value="Humanitarian 0 | Transparency 0")

        ttk.Label(frame, textvariable=self.time_var, style="Info.TLabel").pack(side=tk.LEFT, padx=12)
        ttk.Label(frame, textvariable=self.escalation_var, style="Info.TLabel").pack(side=tk.LEFT, padx=12)
        ttk.Label(frame, textvariable=self.metrics_var, style="Info.TLabel").pack(side=tk.LEFT, padx=12)

        ttk.Label(frame, text="Posture", style="Info.TLabel").pack(side=tk.LEFT, padx=(24, 4))
        self.posture_var = tk.StringVar(value=self.simulation.posture_mode)
        posture_menu = ttk.OptionMenu(
            frame,
            self.posture_var,
            self.simulation.posture_mode,
            "Supportive",
            "Balanced",
            "Assertive",
            command=self._on_posture_change,
        )
        posture_menu.pack(side=tk.LEFT)

    def _build_left_panel(self) -> None:
        frame = ttk.Frame(self.root, style="Panel.TFrame", padding=12)
        frame.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(0, 8))
        self.root.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Faction Overview", style="Heading.TLabel").pack(anchor=tk.W)
        columns = ("Morale", "Avg Trust", "Resources")
        self.faction_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=14,
        )
        for column in columns:
            self.faction_tree.heading(column, text=column)
            self.faction_tree.column(column, anchor=tk.CENTER, width=110)
        self.faction_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 12))

        self._faction_rows: Dict[str, str] = {}
        for idx, faction_id in enumerate(self.scenario.factions.keys()):
            row_id = self.faction_tree.insert("", tk.END, values=("--", "--", "--"))
            self._faction_rows[faction_id] = row_id

        self.timeline = ttk.Progressbar(frame, orient=tk.HORIZONTAL, mode="determinate")
        self.timeline.pack(fill=tk.X, pady=(6, 0))
        self.timeline.configure(maximum=self.scenario.configuration.duration_minutes or 1)

    def _build_center_panel(self) -> None:
        frame = ttk.Frame(self.root, style="Panel.TFrame", padding=12)
        frame.grid(row=1, column=1, sticky="nsew", padx=8, pady=(0, 8))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Operational Map", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.map_canvas = tk.Canvas(frame, width=760, height=520, bg="#132330", highlightthickness=0)
        self.map_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self.show_crowd_var = tk.BooleanVar(value=True)
        self.show_units_var = tk.BooleanVar(value=True)
        toggle_frame = ttk.Frame(frame, style="Panel.TFrame")
        toggle_frame.grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(
            toggle_frame,
            text="Show Crowd Heat",
            variable=self.show_crowd_var,
            command=self._render_crowd_layer,
        ).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(
            toggle_frame,
            text="Show Unit Labels",
            variable=self.show_units_var,
            command=self._toggle_unit_labels,
        ).pack(side=tk.LEFT, padx=6)

        self.faction_palette: Dict[str, str] = {}
        for idx, faction_id in enumerate(self.scenario.factions.keys()):
            self.faction_palette[faction_id] = FACTION_COLORS[idx % len(FACTION_COLORS)]

        self._hotspot_items: List[Dict[str, int]] = []
        self._unit_items: List[Dict[str, int]] = []
        self._zone_items: List[int] = []
        self._draw_static_map()
        self._draw_units()

    def _build_right_panel(self) -> None:
        frame = ttk.Frame(self.root, style="Panel.TFrame", padding=12)
        frame.grid(row=1, column=2, sticky="nsew", padx=(8, 16), pady=(0, 8))
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Events & Actions", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.event_log = tk.Text(frame, height=24, width=36, bg="#101820", fg="#F5F7FA", wrap=tk.WORD)
        self.event_log.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.event_log.configure(state=tk.DISABLED)

    def _build_bottom_bar(self) -> None:
        frame = ttk.Frame(self.root, style="Dark.TFrame", padding=(16, 10))
        frame.grid(row=2, column=0, columnspan=3, sticky="nsew")

        ttk.Label(frame, text="Command Deck", style="Heading.TLabel").pack(anchor=tk.W)
        button_frame = ttk.Frame(frame, style="Dark.TFrame")
        button_frame.pack(fill=tk.X, pady=(6, 0))

        self._action_buttons: Dict[str, ttk.Button] = {}
        for action_id in PLAYER_ACTIONS:
            button = ttk.Button(
                button_frame,
                text=PLAYER_ACTIONS[action_id].label,
                style="Action.TButton",
                command=lambda a=action_id: self._attempt_action(a),
                width=26,
            )
            button.pack(side=tk.LEFT, padx=6)
            self._action_buttons[action_id] = button

        control_frame = ttk.Frame(frame, style="Dark.TFrame")
        control_frame.pack(fill=tk.X, pady=(8, 0))
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self._toggle_pause)
        self.pause_button.pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Step", command=self._step_once).pack(side=tk.LEFT, padx=6)
        ttk.Button(control_frame, text="Save Summary", command=self._export_snapshot).pack(side=tk.LEFT, padx=6)

        ttk.Label(control_frame, text="Tick Delay (ms)", style="Info.TLabel").pack(side=tk.LEFT, padx=(20, 4))
        self.delay_var = tk.IntVar(value=self.tick_delay_ms)
        delay_scale = ttk.Scale(
            control_frame,
            from_=200,
            to=1500,
            orient=tk.HORIZONTAL,
            command=self._on_delay_change,
        )
        delay_scale.set(self.tick_delay_ms)
        delay_scale.pack(side=tk.LEFT, padx=6)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var, style="Info.TLabel").pack(anchor=tk.W, pady=(8, 0))

    # ------------------------------------------------------------------
    # Simulation control
    def launch(self) -> None:
        self._schedule_next_tick()
        self.root.mainloop()

    def _schedule_next_tick(self) -> None:
        if self._paused:
            return
        self._after_id = self.root.after(self.tick_delay_ms, self._advance_simulation)

    def _advance_simulation(self) -> None:
        report = self.simulation.advance_one_minute()
        if report is None:
            self._handle_completion()
            return
        self._render_tick(report)
        self._schedule_next_tick()

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        if not self._paused:
            self.pause_button.configure(text="Pause")
            self._schedule_next_tick()
        else:
            self.pause_button.configure(text="Resume")
            self.status_var.set("Simulation paused")

    def _step_once(self) -> None:
        if not self._paused:
            self._toggle_pause()
        report = self.simulation.advance_one_minute()
        if report is None:
            self._handle_completion()
            return
        self._render_tick(report)

    def _on_delay_change(self, value: str) -> None:
        try:
            self.tick_delay_ms = max(100, int(float(value)))
            self.delay_var.set(self.tick_delay_ms)
        except ValueError:  # pragma: no cover - slider edge case
            pass

    # ------------------------------------------------------------------
    # Rendering helpers
    def _render_tick(self, report: TickReport) -> None:
        self._latest_report = report
        self.time_var.set(
            f"Minute {report.minute:02d} / {self.scenario.configuration.duration_minutes:02d}"
        )
        self.escalation_var.set(f"Escalation: {report.escalation.name.title()}")
        self.metrics_var.set(
            f"Humanitarian {report.humanitarian_index:.1f} | "
            f"Transparency {report.transparency_index:.1f} | Posture {report.posture_mode}"
        )
        self.timeline.configure(value=report.minute)

        self._refresh_faction_rows(report)
        self._render_crowd_layer(report)
        self._refresh_units(report)
        self._log_tick(report)
        self._refresh_action_buttons()

    def _refresh_faction_rows(self, report: Optional[TickReport] = None) -> None:
        if report:
            states = report.faction_states
        else:
            states = {
                fid: {
                    "name": faction.name,
                    "morale": faction.morale,
                    "trust": dict(faction.trust),
                    "resources": dict(faction.resources),
                    "humanitarian": self.simulation.logistics_system.snapshot(),
                    "transparency": self.simulation.media_system.snapshot(),
                }
                for fid, faction in self.scenario.factions.items()
            }
        for faction_id, row_id in self._faction_rows.items():
            state = states.get(faction_id)
            if not state:
                continue
            trust_map = state.get("trust", {})
            avg_trust = 0.0
            if trust_map:
                avg_trust = sum(trust_map.values()) / len(trust_map)
            resources = state.get("resources", {})
            resources_text = ", ".join(f"{key[:3]}:{value}" for key, value in resources.items()) or "--"
            self.faction_tree.item(
                row_id,
                values=(
                    f"{state.get('morale', 0.0):.1f}",
                    f"{avg_trust:.1f}",
                    resources_text,
                ),
            )

    def _emotion_color(self, percentages: Dict[str, float]) -> str:
        entries = []
        for emotion, value in percentages.items():
            color = EMOTION_COLORS.get(emotion, "#4E8098")
            entries.append((color, max(0.0, value)))
        return _blend_colors(entries)

    def _render_crowd_layer(self, report: Optional[TickReport] = None) -> None:
        if report is None:
            report = self._latest_report
        if not report:
            return
        if not self.show_crowd_var.get():
            for entry in self._hotspot_items:
                self.map_canvas.itemconfigure(entry["oval"], state=tk.HIDDEN)
            return
        dominant_color = self._emotion_color(report.crowd_emotions)
        for entry in self._hotspot_items:
            base_radius = entry["radius"]
            intensity = entry["intensity"]
            radius = base_radius * (0.85 + intensity * 0.3)
            cx, cy = entry["center"]
            self.map_canvas.coords(
                entry["oval"],
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            )
            self.map_canvas.itemconfigure(entry["oval"], fill=dominant_color, state=tk.NORMAL)

    def _refresh_units(self, report: Optional[TickReport]) -> None:
        if report is None:
            return
        faction_states = report.faction_states
        for entry in self._unit_items:
            faction_id = entry["faction"]
            state = faction_states.get(faction_id)
            morale = 60.0
            if state:
                morale = state.get("morale", morale)
            base_color = self.faction_palette.get(faction_id, "#6C7A89")
            fill = _morale_color(base_color, morale)
            self.map_canvas.itemconfigure(entry["shape"], fill=fill)
            if self.show_units_var.get():
                label = f"{entry['name']}\n{entry['posture']}"
                self.map_canvas.itemconfigure(entry["label"], text=label, state=tk.NORMAL)
            else:
                self.map_canvas.itemconfigure(entry["label"], state=tk.HIDDEN)

    def _log_tick(self, report: TickReport) -> None:
        entries: List[str] = []
        if report.triggered_events:
            for event in report.triggered_events:
                entries.append(f"Event: {event.get('name', 'Unnamed')}")
        if report.player_actions:
            for action in report.player_actions:
                entries.append(f"Action: {action['label']} ({action['acting_faction']})")
        if not entries:
            entries.append(f"Status: Escalation {report.escalation.name.title()}")

        for line in entries:
            self._log_messages.append(f"[M{report.minute:02d}] {line}")
        self._log_messages = self._log_messages[-200:]

        self.event_log.configure(state=tk.NORMAL)
        self.event_log.delete("1.0", tk.END)
        self.event_log.insert(tk.END, "\n".join(self._log_messages))
        self.event_log.configure(state=tk.DISABLED)
        self.event_log.see(tk.END)

    def _refresh_action_buttons(self) -> None:
        statuses = self.simulation.get_action_statuses()
        status_map = {status["id"]: status for status in statuses}
        for action_id, button in self._action_buttons.items():
            status = status_map.get(action_id)
            if not status:
                button.configure(state=tk.DISABLED, text=PLAYER_ACTIONS[action_id].label)
                continue
            lines = [PLAYER_ACTIONS[action_id].label]
            cost_text = ", ".join(
                f"{key[:3]}:{value}" for key, value in status["costs"].items()
            )
            lines.append(f"Costs {cost_text}")
            if status["cooldown"] > 0:
                lines.append(f"Cooldown {status['cooldown']}m")
                button.configure(state=tk.DISABLED)
            elif not status["available"]:
                lines.append("Insufficient resources")
                button.configure(state=tk.DISABLED)
            else:
                button.configure(state=tk.NORMAL)
            button.configure(text="\n".join(lines))

    # ------------------------------------------------------------------
    # Map construction
    def _draw_static_map(self) -> None:
        layout = self.scenario.map_layout or {}
        zones = layout.get("zones", [])
        for zone in zones:
            polygon = zone.get("polygon", [])
            if not polygon:
                continue
            coords = self._scale_points(polygon)
            zone_type = zone.get("type", "civic")
            fill = ZONE_COLOR_PRESETS.get(zone_type, "#1F3B57")
            poly_id = self.map_canvas.create_polygon(
                coords,
                fill=fill,
                outline="#0F1D2A",
                width=2,
            )
            self._zone_items.append(poly_id)
            label_pos = self._polygon_center(coords)
            self.map_canvas.create_text(
                label_pos[0],
                label_pos[1],
                text=zone.get("name", ""),
                fill="#F5F7FA",
                font=("Source Sans Pro", 12, "bold"),
            )

        for corridor in layout.get("corridors", []):
            path = self._scale_points(corridor.get("path", []))
            if len(path) >= 4:
                self.map_canvas.create_line(
                    path,
                    fill="#F6AE2D",
                    width=4,
                    smooth=True,
                    splinesteps=20,
                )
                if name := corridor.get("name"):
                    mid_x = (path[0] + path[-2]) / 2
                    mid_y = (path[1] + path[-1]) / 2
                    self.map_canvas.create_text(
                        mid_x,
                        mid_y,
                        text=name,
                        fill="#F5F7FA",
                        font=("Source Sans Pro", 11),
                    )

        for poi in layout.get("points_of_interest", []):
            x, y = self._scale_point(poi.get("position", [0.5, 0.5]))
            self.map_canvas.create_oval(
                x - 6,
                y - 6,
                x + 6,
                y + 6,
                fill="#F5B642",
                outline="",
            )
            self.map_canvas.create_text(
                x + 10,
                y - 10,
                text=poi.get("name", ""),
                fill="#F5F7FA",
                anchor=tk.W,
                font=("Source Sans Pro", 11),
            )

        for hotspot in self.scenario.crowd.density_hotspots:
            position = hotspot.get("position", None)
            if position is None:
                idx = self.scenario.crowd.density_hotspots.index(hotspot)
                fraction_x = 0.2 + idx * 0.3
                fraction_y = 0.55
            else:
                fraction_x, fraction_y = position
            cx, cy = self._scale_point([fraction_x, fraction_y])
            intensity = float(hotspot.get("intensity", 0.5))
            radius = 45 * (0.6 + intensity)
            oval = self.map_canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill="#3AAFA9",
                outline="",
                stipple="gray25",
            )
            label = self.map_canvas.create_text(
                cx,
                cy,
                text=hotspot.get("name", ""),
                fill="#F5F7FA",
                font=("Source Sans Pro", 11, "bold"),
            )
            self._hotspot_items.append(
                {
                    "oval": oval,
                    "label": label,
                    "center": (cx, cy),
                    "radius": radius,
                    "intensity": intensity,
                }
            )

    def _draw_units(self) -> None:
        self._unit_items.clear()
        for group in self.scenario.unit_groups:
            fraction_x, fraction_y = group.get("position", [0.5, 0.5])
            cx, cy = self._scale_point([float(fraction_x), float(fraction_y)])
            strength = float(group.get("strength", 1))
            radius = 14 + strength * 3
            faction_id = group.get("faction", "")
            color = self.faction_palette.get(faction_id, "#6C7A89")
            shape = self.map_canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill=color,
                outline="#0F1D2A",
                width=2,
            )
            label = self.map_canvas.create_text(
                cx,
                cy + radius + 12,
                text=f"{group.get('name', 'Unit')}\n{group.get('posture', '')}",
                fill="#F5F7FA",
                font=("Source Sans Pro", 11),
                justify=tk.CENTER,
            )
            self._unit_items.append(
                {
                    "shape": shape,
                    "label": label,
                    "faction": faction_id,
                    "name": group.get("name", "Unit"),
                    "posture": group.get("posture", ""),
                }
            )

    def _toggle_unit_labels(self) -> None:
        if not self.show_units_var.get():
            for entry in self._unit_items:
                self.map_canvas.itemconfigure(entry["label"], state=tk.HIDDEN)
        else:
            for entry in self._unit_items:
                self.map_canvas.itemconfigure(entry["label"], state=tk.NORMAL)

    # ------------------------------------------------------------------
    # Coordinate helpers
    def _scale_points(self, points: Sequence[Sequence[float]]) -> List[float]:
        coords: List[float] = []
        for point in points:
            x, y = self._scale_point(point)
            coords.extend([x, y])
        return coords

    def _scale_point(self, point: Sequence[float]) -> Tuple[float, float]:
        px, py = point
        width = float(self.map_canvas.winfo_width() or 760)
        height = float(self.map_canvas.winfo_height() or 520)
        inset = 40
        if width <= inset * 2:
            width = 760.0
        if height <= inset * 2:
            height = 520.0
        x = inset + max(0.0, min(1.0, px)) * (width - inset * 2)
        y = inset + max(0.0, min(1.0, py)) * (height - inset * 2)
        return x, y

    def _polygon_center(self, coords: Sequence[float]) -> Tuple[float, float]:
        xs = coords[0::2]
        ys = coords[1::2]
        if not xs or not ys:
            return (0.0, 0.0)
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    # ------------------------------------------------------------------
    # Interaction handlers
    def _attempt_action(self, action_id: str) -> None:
        success, message = self.simulation.issue_player_action(action_id)
        if success:
            self.status_var.set(message)
            self._refresh_action_buttons()
            self._refresh_faction_rows()
        else:
            self.status_var.set(message)

    def _on_posture_change(self, value: str) -> None:
        self.simulation.set_posture(value)
        self.status_var.set(f"Posture set to {value}")
        if self._latest_report:
            self.metrics_var.set(
                f"Humanitarian {self._latest_report.humanitarian_index:.1f} | "
                f"Transparency {self._latest_report.transparency_index:.1f} | Posture {value}"
            )

    # ------------------------------------------------------------------
    # Export / shutdown
    def _export_snapshot(self) -> None:
        summary = self.simulation.summary()
        path = self.log_path or Path("simulation_report.json")
        path.write_text(json.dumps(summary, indent=2))
        self.status_var.set(f"Summary exported to {path}")

    def _handle_completion(self) -> None:
        self._paused = True
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        summary = self.simulation.summary()
        if self.log_path:
            self.log_path.write_text(json.dumps(summary, indent=2))
        self._show_summary(summary)

    def _show_summary(self, summary: Dict[str, object]) -> None:
        window = tk.Toplevel(self.root)
        window.title("Simulation Summary")
        window.geometry("520x420")
        window.configure(bg="#172935")

        ttk.Label(window, text="Simulation Complete", style="Heading.TLabel").pack(pady=12)
        text = tk.Text(window, bg="#101820", fg="#F5F7FA", wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        text.insert(
            tk.END,
            json.dumps(summary, indent=2),
        )
        text.configure(state=tk.DISABLED)
        ttk.Button(window, text="Close", command=window.destroy).pack(pady=8)

    def _on_close(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self.root.quit()
        self.root.destroy()


__all__ = ["SimulationGUI"]
