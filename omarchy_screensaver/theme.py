"""Theme Engine for Omarchy Screensaver.

Extracts palette colors from the active Omarchy theme (~/.local/state/omarchy/current/theme/colors.toml),
supports custom theme TOML files, and provides live file watching for seamless runtime updates.
"""

import os
import time
import tomllib
from typing import Callable, Dict, List, Optional, Tuple


def hex_to_rgba(hex_str: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    """Convert hex string (#RGB, #RRGGBB, #RRGGBBAA) to RGBA tuple of floats (0.0 - 1.0)."""
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        r = int(s[0] * 2, 16) / 255.0
        g = int(s[1] * 2, 16) / 255.0
        b = int(s[2] * 2, 16) / 255.0
        return (r, g, b, alpha)
    elif len(s) == 6:
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        return (r, g, b, alpha)
    elif len(s) == 8:
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        a = (int(s[6:8], 16) / 255.0) * alpha
        return (r, g, b, a)
    return (1.0, 1.0, 1.0, alpha)


def with_alpha(rgba: Tuple[float, float, float, float], alpha: float) -> Tuple[float, float, float, float]:
    """Return new RGBA tuple with altered alpha."""
    return (rgba[0], rgba[1], rgba[2], alpha)


class ThemePalette:
    """Holds parsed color strings and RGBA floats for Cairo/GTK rendering."""

    def __init__(self, name: str, data: Dict[str, str]):
        self.name = name
        self.raw_data = data

        # Default fallback hexes
        self.hex_background = data.get("darker_background") or data.get("background", "#0c1512")
        self.hex_surface = data.get("dark_background") or data.get("lighter_background", "#111c18")
        self.hex_foreground = data.get("foreground", "#C1C497")
        self.hex_bright_foreground = data.get("bright_foreground", "#F7E8B2")
        self.hex_muted = data.get("muted", "#53685B")
        self.hex_accent = data.get("accent", "#509475")
        self.hex_primary = data.get("blue") or data.get("accent", "#509475")
        self.hex_secondary = data.get("cyan") or data.get("magenta", "#2DD5B7")
        self.hex_red = data.get("red", "#FF5345")
        self.hex_green = data.get("green", "#549e6a")
        self.hex_yellow = data.get("yellow", "#459451")
        self.hex_blue = data.get("blue", "#509475")
        self.hex_magenta = data.get("magenta", "#D2689C")
        self.hex_cyan = data.get("cyan", "#2DD5B7")
        self.hex_orange = data.get("orange", "#a2734b")

        # RGBA tuples (0.0 - 1.0)
        self.background = hex_to_rgba(self.hex_background)
        self.surface = hex_to_rgba(self.hex_surface)
        self.foreground = hex_to_rgba(self.hex_foreground)
        self.bright_foreground = hex_to_rgba(self.hex_bright_foreground)
        self.muted = hex_to_rgba(self.hex_muted)
        self.accent = hex_to_rgba(self.hex_accent)
        self.primary = hex_to_rgba(self.hex_primary)
        self.secondary = hex_to_rgba(self.hex_secondary)
        self.danger = hex_to_rgba(self.hex_red)
        self.warning = hex_to_rgba(self.hex_yellow)
        self.success = hex_to_rgba(self.hex_green)
        self.info = hex_to_rgba(self.hex_cyan)

        # Derived transparent variants for glowing and overlays
        self.bg_glow = with_alpha(self.primary, 0.08)
        self.card_bg = with_alpha(self.surface, 0.70)
        self.card_border = with_alpha(self.primary, 0.25)
        self.accent_glow = with_alpha(self.accent, 0.35)
        self.particle_color = with_alpha(self.primary, 0.85)


class ThemeManager:
    """Manages active theme, detection, custom theme loading, and live updates."""

    OMARCHY_THEME_DIR = os.path.expanduser("~/.local/state/omarchy/current/theme")
    OMARCHY_THEME_NAME_FILE = os.path.expanduser("~/.local/state/omarchy/current/theme.name")
    OMARCHY_COLORS_FILE = os.path.expanduser("~/.local/state/omarchy/current/theme/colors.toml")

    def __init__(self, theme_setting: str = "auto", custom_themes_dir: str = ""):
        self.theme_setting = theme_setting
        self.custom_themes_dir = custom_themes_dir or os.path.expanduser("~/.config/omarchy-screensaver/themes")
        self._palette: Optional[ThemePalette] = None
        self._last_mtime: float = 0.0
        self._watch_path: str = ""
        self._listeners: List[Callable[[ThemePalette], None]] = []

        self.reload()

    @property
    def palette(self) -> ThemePalette:
        if self._palette is None:
            self.reload()
        return self._palette

    def add_listener(self, callback: Callable[[ThemePalette], None]):
        """Register a callback when theme changes."""
        self._listeners.append(callback)

    def reload(self) -> ThemePalette:
        """Load or reload theme palette."""
        theme_name = "omarchy"
        raw_colors = {}

        if self.theme_setting == "auto":
            # 1. Read Omarchy theme name
            if os.path.exists(self.OMARCHY_THEME_NAME_FILE):
                try:
                    with open(self.OMARCHY_THEME_NAME_FILE, "r", encoding="utf-8") as f:
                        theme_name = f.read().strip()
                except Exception:
                    theme_name = "auto"

            # 2. Read Omarchy colors.toml
            if os.path.exists(self.OMARCHY_COLORS_FILE):
                self._watch_path = self.OMARCHY_COLORS_FILE
                try:
                    self._last_mtime = os.path.getmtime(self.OMARCHY_COLORS_FILE)
                    with open(self.OMARCHY_COLORS_FILE, "rb") as f:
                        raw_colors = tomllib.load(f)
                except Exception:
                    pass
        else:
            # Custom theme file from ~/.config/omarchy-screensaver/themes/<name>.toml
            theme_file = os.path.join(self.custom_themes_dir, f"{self.theme_setting}.toml")
            if os.path.exists(theme_file):
                self._watch_path = theme_file
                try:
                    self._last_mtime = os.path.getmtime(theme_file)
                    with open(theme_file, "rb") as f:
                        data = tomllib.load(f)
                        raw_colors = data.get("colors", data)
                        theme_name = data.get("name", self.theme_setting)
                except Exception:
                    pass

        self._palette = ThemePalette(theme_name, raw_colors)
        return self._palette

    def check_for_updates(self) -> bool:
        """Check if theme file has changed on disk. If so, reload and trigger listeners."""
        if not self._watch_path or not os.path.exists(self._watch_path):
            return False

        try:
            mtime = os.path.getmtime(self._watch_path)
            if mtime > self._last_mtime:
                self._last_mtime = mtime
                self.reload()
                for cb in self._listeners:
                    try:
                        cb(self._palette)
                    except Exception:
                        pass
                return True
        except Exception:
            pass
        return False
