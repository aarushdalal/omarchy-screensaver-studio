"""Configuration manager for Omarchy Screensaver.

Handles loading, parsing, validating, and writing ~/.config/omarchy-screensaver/config.toml.
Provides typed access to all user settings and performance profiles.
"""

import dataclasses
import os
import tomllib
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG_TOML = """# ==============================================================================
# Omarchy Screensaver Configuration
# ==============================================================================
# Location: ~/.config/omarchy-screensaver/config.toml
# Reload: Restart screensaver to apply major changes. Themes update dynamically!

[general]
enabled = true
# Modes: "clock", "matrix", "particles", "warp", "geometry", "singularity", "terminal", "system", "visualizer", "aurora", "auto"
mode = "clock"
# When rotation is true, screensaver smoothly cycles through rotation_modes
rotation = false
rotation_interval = 300
rotation_modes = [
    "clock",
    "matrix",
    "particles",
    "warp",
    "geometry",
    "singularity",
    "system",
    "terminal",
    "aurora",
    "visualizer"
]
# Theme: "auto" (matches active Omarchy theme) or a theme filename in themes/
theme = "auto"

[display]
# Target framerate on AC power
fps = 60
# Multi-monitor mode: "independent", "mirror", "single"
multi_monitor = "independent"
# Input handling: dismiss screensaver on interaction
exit_on_mouse_move = true
mouse_move_threshold = 12
exit_on_key_press = true
# OLED burn-in prevention: pure #000000 true black subpixel shutoff & continuous orbital drift
oled_mode = true
burn_in_protection = true

[ambient]
# Ambient / Study desk display settings (omarchy-screensaver-toggle)
# When active as study desk display: ONLY the shortcut will toggle/close it
exit_on_mouse_move = false
mouse_move_threshold = 100
exit_on_key_press = false
exit_on_mouse_click = false

[performance]
# Profile: "low" (20-30 FPS, minimal effects), "balanced" (30-60 FPS), "high" (60 FPS, richer)
profile = "balanced"

[battery]
# Automatically reduce framerate and particle density when running on battery
auto_detect = true
reduce_fps = true
battery_fps = 30
particle_multiplier = 0.5

[clock]
format_24h = true
show_seconds = false
show_date = true
show_system_info = true
colon_blink = true

[particles]
count = 160
speed = 0.18
connection_distance = 120
particle_size = 1.8
glow = true

[terminal]
cursor_blink_rate = 0.55
show_real_metrics = true
event_interval = 3.5
max_log_lines = 12

[system]
graph_history_points = 50
update_interval = 0.8

[visualizer]
style = "spectrum"
bar_count = 36
auto_switch_on_play = true
fallback_mode = "clock"

[aurora]
speed = 0.25
wave_count = 4
dust_count = 60

[matrix]
speed = 1.0
rain_length = 24
density = 0.85
font_size = 14

[warp]
star_count = 450
warp_speed = 1.2
streak_length = 1.0

[geometry]
shape = "tesseract"
rotation_speed = 0.6
line_width = 1.6
glow = true

[singularity]
particle_count = 350
swirl_speed = 1.0
disk_tilt = 0.45
beaming = true
"""


class Config:
    """Loaded configuration with fallback defaults."""

    CONFIG_DIR = os.path.expanduser("~/.config/omarchy-screensaver")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.toml")
    THEMES_DIR = os.path.join(CONFIG_DIR, "themes")
    LOGS_DIR = os.path.join(CONFIG_DIR, "logs")
    BACKUPS_DIR = os.path.join(CONFIG_DIR, "backups")
    PID_FILE = os.path.join(CONFIG_DIR, "screensaver.pid")

    def __init__(self, raw: Optional[Dict[str, Any]] = None):
        self.raw = raw or {}

        # [general]
        gen = self.raw.get("general", {})
        self.enabled: bool = gen.get("enabled", True)
        self.mode: str = gen.get("mode", "clock")
        self.rotation: bool = gen.get("rotation", False)
        self.rotation_interval: int = int(gen.get("rotation_interval", 300))
        self.rotation_modes: List[str] = gen.get(
            "rotation_modes", [
                "clock", "matrix", "particles", "warp", "geometry",
                "singularity", "system", "terminal", "aurora", "visualizer"
            ]
        )
        self.theme: str = gen.get("theme", "auto")

        # [display]
        disp = self.raw.get("display", {})
        self.fps: int = int(disp.get("fps", 60))
        self.multi_monitor: str = disp.get("multi_monitor", "independent")
        self.exit_on_mouse_move: bool = disp.get("exit_on_mouse_move", True)
        self.mouse_move_threshold: int = int(disp.get("mouse_move_threshold", 12))
        self.exit_on_key_press: bool = disp.get("exit_on_key_press", True)
        self.oled_mode: bool = disp.get("oled_mode", True)
        self.burn_in_protection: bool = disp.get("burn_in_protection", True)

        # [ambient]
        amb = self.raw.get("ambient", {})
        self.ambient_exit_on_mouse_move: bool = amb.get("exit_on_mouse_move", False)
        self.ambient_mouse_move_threshold: int = int(amb.get("mouse_move_threshold", 100))
        self.ambient_exit_on_key_press: bool = amb.get("exit_on_key_press", False)
        self.ambient_exit_on_mouse_click: bool = amb.get("exit_on_mouse_click", False)

        # [performance]
        perf = self.raw.get("performance", {})
        self.profile: str = perf.get("profile", "balanced")

        # [battery]
        bat = self.raw.get("battery", {})
        self.battery_auto_detect: bool = bat.get("auto_detect", True)
        self.battery_reduce_fps: bool = bat.get("reduce_fps", True)
        self.battery_fps: int = int(bat.get("battery_fps", 30))
        self.particle_multiplier: float = float(bat.get("particle_multiplier", 0.5))

        # [clock]
        clk = self.raw.get("clock", {})
        self.clock_format_24h: bool = clk.get("format_24h", True)
        self.clock_show_seconds: bool = clk.get("show_seconds", False)
        self.clock_show_date: bool = clk.get("show_date", True)
        self.clock_show_system_info: bool = clk.get("show_system_info", True)
        self.clock_colon_blink: bool = clk.get("colon_blink", True)

        # [particles]
        part = self.raw.get("particles", {})
        self.particles_count: int = int(part.get("count", 160))
        self.particles_speed: float = float(part.get("speed", 0.18))
        self.particles_connection_distance: int = int(part.get("connection_distance", 120))
        self.particles_size: float = float(part.get("particle_size", 1.8))
        self.particles_glow: bool = part.get("glow", True)

        # [terminal]
        term = self.raw.get("terminal", {})
        self.terminal_cursor_blink_rate: float = float(term.get("cursor_blink_rate", 0.55))
        self.terminal_show_real_metrics: bool = term.get("show_real_metrics", True)
        self.terminal_event_interval: float = float(term.get("event_interval", 3.5))
        self.terminal_max_log_lines: int = int(term.get("max_log_lines", 12))

        # [system]
        sys_sec = self.raw.get("system", {})
        self.system_graph_history_points: int = int(sys_sec.get("graph_history_points", 50))
        self.system_update_interval: float = float(sys_sec.get("update_interval", 0.8))

        # [visualizer]
        vis = self.raw.get("visualizer", {})
        self.visualizer_style: str = vis.get("style", "spectrum")
        self.visualizer_bar_count: int = int(vis.get("bar_count", 36))
        self.visualizer_auto_switch_on_play: bool = vis.get("auto_switch_on_play", True)
        self.visualizer_fallback_mode: str = vis.get("fallback_mode", "selected")

        # [aurora]
        aur = self.raw.get("aurora", {})
        self.aurora_speed: float = float(aur.get("speed", 0.25))
        self.aurora_wave_count: int = int(aur.get("wave_count", 4))
        self.aurora_dust_count: int = int(aur.get("dust_count", 60))

        # [matrix]
        mat = self.raw.get("matrix", {})
        self.matrix_speed: float = float(mat.get("speed", 1.0))
        self.matrix_rain_length: int = int(mat.get("rain_length", 24))
        self.matrix_density: float = float(mat.get("density", 0.85))
        self.matrix_font_size: int = int(mat.get("font_size", 14))

        # [warp]
        wrp = self.raw.get("warp", {})
        self.warp_star_count: int = int(wrp.get("star_count", 450))
        self.warp_speed: float = float(wrp.get("warp_speed", 1.2))
        self.warp_streak_length: float = float(wrp.get("streak_length", 1.0))

        # [geometry]
        geo = self.raw.get("geometry", {})
        self.geometry_shape: str = geo.get("shape", "tesseract")
        self.geometry_rotation_speed: float = float(geo.get("rotation_speed", 0.6))
        self.geometry_line_width: float = float(geo.get("line_width", 1.6))
        self.geometry_glow: bool = geo.get("glow", True)

        # [singularity]
        sing = self.raw.get("singularity", {})
        self.singularity_particle_count: int = int(sing.get("particle_count", 350))
        self.singularity_swirl_speed: float = float(sing.get("swirl_speed", 1.0))
        self.singularity_disk_tilt: float = float(sing.get("disk_tilt", 0.45))
        self.singularity_beaming: bool = sing.get("beaming", True)

        # Apply profile tuning
        if self.profile == "low":
            self.fps = min(self.fps, 30)
            self.particles_count = int(self.particles_count * 0.5)
            self.aurora_wave_count = 2
            self.aurora_dust_count = 30
            self.warp_star_count = int(self.warp_star_count * 0.5)
            self.singularity_particle_count = int(self.singularity_particle_count * 0.5)
        elif self.profile == "high":
            self.fps = max(self.fps, 60)
            self.particles_count = int(self.particles_count * 1.3)
            self.aurora_wave_count = 5
            self.warp_star_count = int(self.warp_star_count * 1.3)
            self.singularity_particle_count = int(self.singularity_particle_count * 1.3)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Load configuration from TOML file or create default if not found."""
        config_path = path or cls.CONFIG_FILE
        raw = {}

        if not os.path.exists(config_path):
            cls.ensure_defaults()

        if os.path.exists(config_path):
            try:
                with open(config_path, "rb") as f:
                    raw = tomllib.load(f)
            except Exception as e:
                print(f"[omarchy-screensaver] Warning: Could not parse {config_path}: {e}")

        return cls(raw)

    @classmethod
    def ensure_defaults(cls):
        """Create config directory, default config.toml, themes, and dirs."""
        for d in [cls.CONFIG_DIR, cls.THEMES_DIR, cls.LOGS_DIR, cls.BACKUPS_DIR]:
            os.makedirs(d, exist_ok=True)

        if not os.path.exists(cls.CONFIG_FILE):
            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG_TOML)
