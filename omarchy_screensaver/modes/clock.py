"""Mode 1: Minimal Floating Typographic Clock.

Presents a futuristic, high-typography minimalist clock with adaptive scaling,
planetary orbital ring, floating date, live telemetry, and complete OLED burn-in defense.
"""

import math
import time
from typing import Optional

import cairo
from gi.repository import Pango, PangoCairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class ClockMode(BaseMode):
    """Futuristic minimal floating clock with celestial orbital aura."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.fade_in: float = 0.0
        self.metrics: Optional[SystemMetrics] = None
        self.orbit_angle: float = 0.0

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics
        self.orbit_angle += dt * 0.08
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        # 100% OLED pitch black clear
        self.clear_background(cr, width, height)

        # Dynamic wandering anchor (Lissajous + micro-jitter)
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.48 + self.burn_y + self.jitter_y

        now = time.localtime()
        alpha = self.fade_in * self.luminance_factor

        # Sizing
        base_size = min(width, height)
        clock_font_size = max(64.0, base_size * 0.13)
        date_font_size = max(13.0, clock_font_size * 0.17)
        sys_font_size = max(11.0, clock_font_size * 0.13)

        # 1. Subtle Planetary Celestial Ring (ambient, non-static, slow rotation)
        halo_radius = clock_font_size * 1.8
        cr.save()
        cr.translate(cx, cy - 10.0)
        cr.rotate(self.orbit_angle)
        ring_pat = cairo.LinearGradient(-halo_radius, -halo_radius, halo_radius, halo_radius)
        ring_pat.add_color_stop_rgba(0.0, *with_alpha(self.theme.accent, 0.16 * alpha))
        ring_pat.add_color_stop_rgba(0.5, *with_alpha(self.theme.primary, 0.04 * alpha))
        ring_pat.add_color_stop_rgba(1.0, *with_alpha(self.theme.background, 0.0))
        cr.set_source(ring_pat)
        cr.set_line_width(1.8)
        cr.arc(0, 0, halo_radius, 0, 2 * math.pi)
        cr.stroke()

        # Orbiting faint celestial beacon node
        node_x = halo_radius * math.cos(self.orbit_angle * 1.5)
        node_y = halo_radius * math.sin(self.orbit_angle * 1.5)
        cr.arc(node_x, node_y, 2.5, 0, 2 * math.pi)
        cr.set_source_rgba(*with_alpha(self.theme.accent, 0.45 * alpha))
        cr.fill()
        cr.restore()

        # 2. Time Strings
        if self.config.clock_format_24h:
            hours_str = f"{now.tm_hour:02d}"
        else:
            h = now.tm_hour % 12
            hours_str = f"{12 if h == 0 else h:02d}"
        mins_str = f"{now.tm_min:02d}"
        secs_str = f"{now.tm_sec:02d}"

        colon_alpha = 1.0
        if self.config.clock_colon_blink:
            colon_alpha = 0.3 + 0.7 * (math.sin(self.time * 3.14159) * 0.5 + 0.5)

        layout_h = self.create_pango_layout(
            cr, hours_str, self.FONT_MONO, clock_font_size, Pango.Weight.BOLD
        )
        layout_m = self.create_pango_layout(
            cr, mins_str, self.FONT_MONO, clock_font_size, Pango.Weight.BOLD
        )
        layout_c = self.create_pango_layout(
            cr, ":", self.FONT_MONO, clock_font_size, Pango.Weight.LIGHT
        )

        _, ext_h = layout_h.get_pixel_extents()
        _, ext_m = layout_m.get_pixel_extents()
        _, ext_c = layout_c.get_pixel_extents()

        w_h, h_h = ext_h.width, ext_h.height
        w_m, h_m = ext_m.width, ext_m.height
        w_c, h_c = ext_c.width, ext_c.height

        spacing = clock_font_size * 0.14
        total_clock_w = w_h + w_c + w_m + spacing * 2

        if self.config.clock_show_seconds:
            layout_s = self.create_pango_layout(
                cr, f" {secs_str}", self.FONT_MONO, clock_font_size * 0.42, Pango.Weight.NORMAL
            )
            _, ext_s = layout_s.get_pixel_extents()
            total_clock_w += ext_s.width + spacing

        start_x = cx - total_clock_w * 0.5
        clock_y = cy - h_h * 0.5 - 20.0

        # Draw Hours with subtle soft ambient glow
        primary_c = self.oled_color(with_alpha(self.theme.bright_foreground, alpha))
        glow_c = with_alpha(self.theme.primary, alpha * 0.20)

        cr.set_source_rgba(*glow_c)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cr.move_to(start_x + dx, clock_y + dy)
            PangoCairo.show_layout(cr, layout_h)

        cr.set_source_rgba(*primary_c)
        cr.move_to(start_x, clock_y)
        PangoCairo.show_layout(cr, layout_h)

        # Draw Colon with smooth pulsation
        colon_x = start_x + w_h + spacing
        colon_c = self.oled_color(with_alpha(self.theme.accent, alpha * colon_alpha))
        cr.set_source_rgba(*colon_c)
        cr.move_to(colon_x, clock_y)
        PangoCairo.show_layout(cr, layout_c)

        # Draw Minutes
        mins_x = colon_x + w_c + spacing
        cr.set_source_rgba(*glow_c)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cr.move_to(mins_x + dx, clock_y + dy)
            PangoCairo.show_layout(cr, layout_m)

        cr.set_source_rgba(*primary_c)
        cr.move_to(mins_x, clock_y)
        PangoCairo.show_layout(cr, layout_m)

        # Draw Seconds if enabled
        if self.config.clock_show_seconds:
            secs_x = mins_x + w_m + spacing
            secs_y = clock_y + h_h * 0.48
            secs_c = self.oled_color(with_alpha(self.theme.muted, alpha * 0.85))
            cr.set_source_rgba(*secs_c)
            cr.move_to(secs_x, secs_y)
            PangoCairo.show_layout(cr, layout_s)

        # 3. Floating Typographic Date (Zero static divider lines)
        if self.config.clock_show_date:
            weekday_str = time.strftime("%A", now).upper()
            date_str = time.strftime("%d · %B · %Y", now).upper()

            date_y1 = clock_y + h_h + 26.0
            self.draw_text(
                cr,
                f"{weekday_str}  —  {date_str}",
                cx,
                date_y1,
                self.FONT_SANS,
                date_font_size,
                self.oled_color(with_alpha(self.theme.foreground, alpha * 0.75)),
                align="center",
                weight=Pango.Weight.MEDIUM,
            )

        # 4. Floating System Telemetry (Minimal holographic row with dot glyphs)
        if self.config.clock_show_system_info and self.metrics:
            m = self.metrics
            telem_y = clock_y + h_h + (62.0 if self.config.clock_show_date else 32.0)

            # Minimalist dot-separated floating row
            telem_text = (
                f"CPU {m.cpu_percent:04.1f}%   ·   "
                f"RAM {m.mem_used_gib:.1f}G   ·   "
                f"BAT {m.battery_percent}%   ·   "
                f"UP {m.uptime_str}"
            )
            self.draw_text(
                cr,
                telem_text,
                cx,
                telem_y,
                self.FONT_MONO,
                sys_font_size,
                self.oled_color(with_alpha(self.theme.muted, alpha * 0.60)),
                align="center",
                weight=Pango.Weight.NORMAL,
            )
