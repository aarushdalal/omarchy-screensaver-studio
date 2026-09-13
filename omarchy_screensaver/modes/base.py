"""Base class and rendering helpers for screensaver visual modes.
"""

import math
import time
from typing import Optional, Tuple

import cairo
import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha


class BaseMode:
    """Abstract base class for screensaver modes."""

    # Cached font names
    FONT_MONO = "JetBrainsMono Nerd Font, JetBrains Mono, monospace"
    FONT_SANS = "Liberation Sans, Adwaita Sans, Noto Sans, sans-serif"

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        self.theme = theme
        self.config = config
        self.monitor_index = monitor_index
        self.time: float = 0.0
        self.burn_x: float = 0.0
        self.burn_y: float = 0.0
        self.luminance_factor: float = 1.0
        self.jitter_x: float = 0.0
        self.jitter_y: float = 0.0
        self._last_jitter_time: float = 0.0

    def update_theme(self, theme: ThemePalette):
        """Update active theme palette without recreating simulation."""
        self.theme = theme

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        """Advance physics, state simulation, and OLED protection."""
        self.time += dt

        burn_in_active = getattr(self.config, "burn_in_protection", True)
        oled_active = getattr(self.config, "oled_mode", True)

        if burn_in_active or oled_active:
            # Multi-frequency Lissajous orbital trajectory (non-repeating, ~24-36 min cycle)
            # Produces a gentle, organic drift over 65x45 px radius
            freq_x = 0.0032
            freq_y = 0.0025
            phase = float(self.monitor_index) * 1.5708
            self.burn_x = (
                math.sin(self.time * freq_x + phase) * 65.0
                + math.sin(self.time * 0.008 + phase * 0.5) * 12.0
            )
            self.burn_y = (
                math.cos(self.time * freq_y + phase) * 45.0
                + math.cos(self.time * 0.006 + phase * 0.5) * 8.0
            )

            # Subpixel micro-jitter: discrete 0.75-1.5px shift every 60 seconds
            # Ensures static high-contrast font edges relax across neighboring subpixels
            if self.time - self._last_jitter_time > 60.0:
                self._last_jitter_time = self.time
                step = int(self.time / 60.0)
                self.jitter_x = ((step * 7) % 5 - 2) * 0.75
                self.jitter_y = ((step * 11) % 5 - 2) * 0.75

            # Dynamic luminance breathing: gentle 0.82 to 0.98 alpha oscillation
            # Relieves continuous thermal strain on OLED blue/white phosphors
            self.luminance_factor = 0.90 + 0.08 * math.sin(self.time * 0.04)
        else:
            self.burn_x = 0.0
            self.burn_y = 0.0
            self.jitter_x = 0.0
            self.jitter_y = 0.0
            self.luminance_factor = 1.0

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        """Render frame to Cairo graphics context."""
        raise NotImplementedError

    def on_resize(self, width: int, height: int):
        """Handle window or resolution change."""
        pass

    # Helper rendering utilities
    def clear_background(self, cr: cairo.Context, width: int, height: int, custom_bg=None):
        """Fill background with pure OLED black or dark theme color.

        When OLED mode is active, guarantees pure rgba(0, 0, 0, 1.0) so OLED subpixels
        are completely turned off (0 nits, 0 watts, zero burn-in).
        """
        if getattr(self.config, "oled_mode", True) and custom_bg is None:
            cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        else:
            bg = custom_bg or self.theme.background
            cr.set_source_rgba(*bg)
        cr.paint()

    def oled_color(self, rgba: Tuple[float, float, float, float], alpha_mult: float = 1.0) -> Tuple[float, float, float, float]:
        """Apply luminance breathing factor to RGBA color for OLED phosphor relief."""
        r, g, b, a = rgba
        return (r, g, b, max(0.0, min(1.0, a * alpha_mult * self.luminance_factor)))

    def create_pango_layout(
        self,
        cr: cairo.Context,
        text: str,
        font_family: str,
        font_size_pt: float,
        weight: Pango.Weight = Pango.Weight.NORMAL,
        alignment: Pango.Alignment = Pango.Alignment.CENTER,
    ) -> Pango.Layout:
        """Create and configure a Pango layout."""
        layout = PangoCairo.create_layout(cr)
        desc = Pango.FontDescription()
        desc.set_family(font_family)
        desc.set_size(int(font_size_pt * Pango.SCALE))
        desc.set_weight(weight)
        layout.set_font_description(desc)
        layout.set_text(text, -1)
        layout.set_alignment(alignment)
        return layout

    def draw_text(
        self,
        cr: cairo.Context,
        text: str,
        x: float,
        y: float,
        font_family: str,
        font_size_pt: float,
        color_rgba: Tuple[float, float, float, float],
        align: str = "center",
        weight: Pango.Weight = Pango.Weight.NORMAL,
        glow: bool = False,
    ) -> Tuple[float, float]:
        """Render text with Pango with optional subtle glow."""
        pango_align = Pango.Alignment.CENTER
        if align == "left":
            pango_align = Pango.Alignment.LEFT
        elif align == "right":
            pango_align = Pango.Alignment.RIGHT

        layout = self.create_pango_layout(cr, text, font_family, font_size_pt, weight, pango_align)
        ink, logical = layout.get_pixel_extents()
        w, h = logical.width, logical.height

        render_x = x
        if align == "center":
            render_x = x - w * 0.5
        elif align == "right":
            render_x = x - w

        render_y = y - h * 0.5

        if glow:
            glow_rgba = with_alpha(color_rgba, color_rgba[3] * 0.25)
            cr.set_source_rgba(*glow_rgba)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
                cr.move_to(render_x + dx, render_y + dy)
                PangoCairo.show_layout(cr, layout)

        cr.set_source_rgba(*color_rgba)
        cr.move_to(render_x, render_y)
        PangoCairo.show_layout(cr, layout)

        return float(w), float(h)

    def draw_rounded_rect(self, cr: cairo.Context, x: float, y: float, w: float, h: float, r: float):
        """Draw path for rounded rectangle."""
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()
