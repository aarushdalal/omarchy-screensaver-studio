"""Theme Engine for Omarchy Screensaver.

Extracts palette colors from the active Omarchy theme (~/.local/state/omarchy/current/theme/colors.toml),
supports custom theme TOML files, and provides live file watching for seamless runtime updates.
"""

import os
import time
import tomllib
import json
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


def color_luminance(hex_str: str) -> float:
    """Calculate relative luminance of hex color (0.0 = dark, 1.0 = light)."""
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        r = int(s[0] * 2, 16) / 255.0
        g = int(s[1] * 2, 16) / 255.0
        b = int(s[2] * 2, 16) / 255.0
    elif len(s) >= 6:
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
    else:
        return 0.5
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


class ThemePalette:
    """Holds parsed color strings and RGBA floats for Cairo/GTK rendering."""

    def __init__(self, name: str, data: Dict[str, str]):
        self.name = name
        self.raw_data = data

        # Base background colors (dark tones - pure void / pitch dark)
        self.hex_background = data.get("darker_background") or data.get("dark_background") or data.get("background", "#0a080c")
        self.hex_surface = data.get("dark_background") or data.get("lighter_background") or data.get("surface", "#110e14")

        # Foreground & text tones
        self.hex_foreground = data.get("foreground", "#e7e1e4")
        self.hex_bright_foreground = data.get("bright_foreground", "#ffffff")
        self.hex_dark_foreground = data.get("dark_foreground") or data.get("muted", "#978e96")

        # Muted / Selection / Darker tones
        self.hex_muted = data.get("muted", "#534856")
        self.hex_selection = data.get("selection") or self.hex_surface

        # Signature Accent (vibrant rich dark accent for moody screensavers)
        self.hex_accent = data.get("accent") or data.get("primary") or "#9434b5"
        self.hex_primary = self.hex_accent

        # Secondary color: pick harmonic companion
        cand_sec = data.get("secondary")
        cand_mag = data.get("magenta")
        cand_cyan = data.get("cyan")
        cand_blue = data.get("blue")

        if cand_sec:
            self.hex_secondary = cand_sec
        elif cand_mag and cand_cyan:
            self.hex_secondary = cand_mag if cand_mag != self.hex_accent else cand_cyan
        elif cand_cyan:
            self.hex_secondary = cand_cyan
        elif cand_mag:
            self.hex_secondary = cand_mag
        elif cand_blue:
            self.hex_secondary = cand_blue
        else:
            self.hex_secondary = self.hex_accent

        # Deeper dark accent tone for moody shadows, base gradients, and acoustic ribbons
        self.hex_dark_accent = data.get("dark_accent") or data.get("on_primary") or data.get("dark_foreground") or "#431652"

        # Chromatic accents directly from data
        self.hex_red = data.get("red", "#ff554a")
        self.hex_green = data.get("green", "#549e6a")
        self.hex_yellow = data.get("yellow", "#e0adfb")
        self.hex_blue = data.get("blue", "#9778ca")
        self.hex_magenta = data.get("magenta", "#a866c5")
        self.hex_cyan = data.get("cyan", "#9778ca")
        self.hex_orange = data.get("orange", "#f6bce7")

        # RGBA tuples (0.0 - 1.0)
        self.background = hex_to_rgba(self.hex_background)
        self.surface = hex_to_rgba(self.hex_surface)
        self.foreground = hex_to_rgba(self.hex_foreground)
        self.bright_foreground = hex_to_rgba(self.hex_bright_foreground)
        self.dark_foreground = hex_to_rgba(self.hex_dark_foreground)
        self.muted = hex_to_rgba(self.hex_muted)
        self.selection = hex_to_rgba(self.hex_selection)
        self.accent = hex_to_rgba(self.hex_accent)
        self.primary = hex_to_rgba(self.hex_primary)
        self.secondary = hex_to_rgba(self.hex_secondary)
        self.dark_accent = hex_to_rgba(self.hex_dark_accent)
        self.danger = hex_to_rgba(self.hex_red)
        self.warning = hex_to_rgba(self.hex_yellow)
        self.success = hex_to_rgba(self.hex_green)
        self.info = hex_to_rgba(self.hex_cyan)

        # Derived transparent variants for glowing and overlays
        self.bg_glow = with_alpha(self.accent, 0.08)
        self.card_bg = with_alpha(self.surface, 0.70)
        self.card_border = with_alpha(self.accent, 0.25)
        self.accent_glow = with_alpha(self.accent, 0.35)
        self.particle_color = with_alpha(self.accent, 0.85)

    @property
    def accent_rgb(self) -> Tuple[float, float, float]:
        return self.accent[:3]

    @property
    def primary_rgb(self) -> Tuple[float, float, float]:
        return self.primary[:3]

    @property
    def secondary_rgb(self) -> Tuple[float, float, float]:
        return self.secondary[:3]

    @property
    def muted_rgb(self) -> Tuple[float, float, float]:
        return self.muted[:3]

    @property
    def foreground_rgb(self) -> Tuple[float, float, float]:
        return self.foreground[:3]

    @property
    def background_rgb(self) -> Tuple[float, float, float]:
        return self.background[:3]


class ThemeManager:
    """Manages active theme, detection, custom theme loading, and live updates."""

    OMARCHY_THEME_DIR = os.path.expanduser("~/.local/state/omarchy/current/theme")
    OMARCHY_THEME_NAME_FILE = os.path.expanduser("~/.local/state/omarchy/current/theme.name")
    OMARCHY_COLORS_FILE = os.path.expanduser("~/.local/state/omarchy/current/theme/colors.toml")
    CAELESTIA_SCHEME_FILE = os.path.expanduser("~/.local/state/caelestia/scheme.json")

    def __init__(self, theme_setting: str = "auto", custom_themes_dir: str = ""):
        self.theme_setting = theme_setting
        self.custom_themes_dir = custom_themes_dir or os.path.expanduser("~/.config/omarchy-screensaver/themes")
        self._palette: Optional[ThemePalette] = None
        self._last_mtime: float = 0.0
        self._watch_path: str = ""
        self._last_theme_name: str = ""
        self._last_colors_target: str = ""
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
            # Check if Caelestia shell is actively running in the session
            is_caelestia_running = False
            try:
                import subprocess
                res = subprocess.run(["pgrep", "-f", "qs -c caelestia"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    is_caelestia_running = True
            except Exception:
                pass

            # If Caelestia is actively running, load Caelestia's generated scheme
            if is_caelestia_running and os.path.exists(self.CAELESTIA_SCHEME_FILE):
                try:
                    with open(self.CAELESTIA_SCHEME_FILE, "r", encoding="utf-8") as f:
                        scheme = json.load(f)
                    colours = scheme.get("colours", {})
                    # In M3 dark mode, select vibrant dark key tones from scheme.json (e.g. rich dark purple 9434b5, secondary 6430ba):
                    accent_dark = (
                        colours.get("accent")
                        or colours.get("primary")
                        or "9434b5"
                    )
                    secondary_dark = (
                        colours.get("secondary")
                        or colours.get("tertiary")
                        or "6430ba"
                    )
                    dark_accent = (
                        colours.get("dark_accent")
                        or colours.get("primaryContainer")
                        or "431652"
                    )
                    magenta_dark = accent_dark
                    cyan_dark = colours.get("tertiary") or secondary_dark

                    raw_colors = {
                        "background": f"#{colours.get('surfaceContainerLowest', colours.get('background', '100d10'))}",
                        "darker_background": f"#{colours.get('surfaceContainerLowest', '0e0c0e')}",
                        "dark_background": f"#{colours.get('surfaceContainer', '1d1b1d')}",
                        "foreground": f"#{colours.get('onSurfaceVariant', colours.get('onBackground', 'cec3cc'))}",
                        "bright_foreground": f"#{colours.get('onSurface', 'e7e1e4')}",
                        "dark_foreground": f"#{colours.get('outline', '978e96')}",
                        "muted": f"#{colours.get('secondaryContainer', '534856')}",
                        "selection": f"#{colours.get('surfaceContainerHigh', '2c292c')}",
                        "accent": f"#{accent_dark}",
                        "primary": f"#{accent_dark}",
                        "secondary": f"#{secondary_dark}",
                        "dark_accent": f"#{dark_accent}",
                        "blue": f"#{secondary_dark}",
                        "cyan": f"#{cyan_dark}",
                        "magenta": f"#{magenta_dark}",
                        "red": f"#{colours.get('errorContainer', '93000a')}",
                        "green": f"#{colours.get('tertiaryContainer', 'be8792')}",
                        "yellow": f"#{colours.get('primaryContainer', 'a88cb1')}",
                        "orange": f"#{colours.get('secondaryContainer', '534856')}",
                    }
                    theme_name = f"caelestia-{scheme.get('name', 'dynamic')}"
                    self._watch_path = self.CAELESTIA_SCHEME_FILE
                    self._last_mtime = os.path.getmtime(self.CAELESTIA_SCHEME_FILE)
                    self._last_colors_target = os.path.realpath(self.CAELESTIA_SCHEME_FILE)
                except Exception:
                    raw_colors = {}

            # Primary: Use Omarchy's authoritative active theme colors.toml
            if not raw_colors and os.path.exists(self.OMARCHY_COLORS_FILE):
                self._watch_path = self.OMARCHY_COLORS_FILE
                try:
                    self._last_mtime = os.path.getmtime(self.OMARCHY_COLORS_FILE)
                    self._last_colors_target = os.path.realpath(self.OMARCHY_COLORS_FILE)
                    with open(self.OMARCHY_COLORS_FILE, "rb") as f:
                        raw_colors = tomllib.load(f)
                    if os.path.exists(self.OMARCHY_THEME_NAME_FILE):
                        with open(self.OMARCHY_THEME_NAME_FILE, "r", encoding="utf-8") as f:
                            theme_name = f.read().strip()
                    else:
                        theme_target = os.path.realpath(self.OMARCHY_THEME_DIR)
                        theme_name = os.path.basename(theme_target)
                except Exception:
                    pass

            self._last_theme_name = theme_name
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
            current_name = self._last_theme_name
            if self.theme_setting == "auto":
                if self._watch_path == self.OMARCHY_COLORS_FILE:
                    if os.path.exists(self.OMARCHY_THEME_NAME_FILE):
                        with open(self.OMARCHY_THEME_NAME_FILE, "r", encoding="utf-8") as f:
                            current_name = f.read().strip()
                    else:
                        current_name = os.path.basename(os.path.realpath(self.OMARCHY_THEME_DIR))
                elif self._watch_path == self.CAELESTIA_SCHEME_FILE:
                    with open(self.CAELESTIA_SCHEME_FILE, "r", encoding="utf-8") as f:
                        current_name = f"caelestia-{json.load(f).get('name', 'dynamic')}"
            colors_target = os.path.realpath(self._watch_path)
            if (
                mtime != self._last_mtime
                or current_name != self._last_theme_name
                or colors_target != self._last_colors_target
            ):
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

