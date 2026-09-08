"""Mode 1: Minimal Clock.

Presents a futuristic, high-typography minimalist clock with adaptive scaling,
gentle pulsing separator, date, and live system telemetry.
"""

import math
import time
from typing import Optional

import cairo
from gi.repository import Pango

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class ClockMode(BaseMode):
    """Futuristic minimal clock screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.fade_in: float = 0.0
        self.metrics: Optional[SystemMetrics] = None
        if self.config.clock_show_seconds:
            self.target_fps: int = 15
        elif self.config.clock_colon_blink:
            self.target_fps: int = 6
        else:
            self.target_fps: int = 2

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)

        cx = width * 0.5 + self.burn_x
        cy = height * 0.46 + self.burn_y

        now = time.localtime()

        # Format time string
        if self.config.clock_format_24h:
            hours_str = f"{now.tm_hour:02d}"
        else:
            h = now.tm_hour % 12
            hours_str = f"{12 if h == 0 else h:02d}"
        mins_str = f"{now.tm_min:02d}"
        secs_str = f"{now.tm_sec:02d}"

        # Adaptive typography sizing
        base_size = min(width, height)
        clock_font_size = max(56.0, base_size * 0.12)
        date_font_size = max(13.0, clock_font_size * 0.18)
        sys_font_size = max(11.0, clock_font_size * 0.14)

        alpha = self.fade_in

        # Colon pulse
        colon_alpha = 1.0
        if self.config.clock_colon_blink:
            colon_alpha = 0.35 + 0.65 * (math.sin(self.time * 3.14159) * 0.5 + 0.5)

        # Draw Hours, Colon, Mins
        # Measure parts
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

        spacing = clock_font_size * 0.15
        total_clock_w = w_h + w_c + w_m + spacing * 2

        if self.config.clock_show_seconds:
            layout_s = self.create_pango_layout(
                cr, f" {secs_str}", self.FONT_MONO, clock_font_size * 0.45, Pango.Weight.NORMAL
            )
            _, ext_s = layout_s.get_pixel_extents()
            total_clock_w += ext_s.width + spacing

        start_x = cx - total_clock_w * 0.5
        clock_y = cy - h_h * 0.5

        # Render Hours
        primary_c = with_alpha(self.theme.bright_foreground, alpha)
        cr.set_source_rgba(*primary_c)
        cr.move_to(start_x, clock_y)
        from gi.repository import PangoCairo
        PangoCairo.show_layout(cr, layout_h)

        # Render Colon with pulsation
        colon_x = start_x + w_h + spacing
        colon_c = with_alpha(self.theme.accent, alpha * colon_alpha)
        cr.set_source_rgba(*colon_c)
        cr.move_to(colon_x, clock_y)
        PangoCairo.show_layout(cr, layout_c)

        # Render Minutes
        mins_x = colon_x + w_c + spacing
        cr.set_source_rgba(*primary_c)
        cr.move_to(mins_x, clock_y)
        PangoCairo.show_layout(cr, layout_m)

        # Render Seconds if enabled
        if self.config.clock_show_seconds:
            secs_x = mins_x + w_m + spacing
            secs_y = clock_y + h_h * 0.45
            secs_c = with_alpha(self.theme.muted, alpha)
            cr.set_source_rgba(*secs_c)
            cr.move_to(secs_x, secs_y)
            PangoCairo.show_layout(cr, layout_s)

        # Divider line
        div_y = cy + h_h * 0.55 + 18.0
        div_w = min(total_clock_w * 1.15, width * 0.5)
        div_pat = cairo.LinearGradient(cx - div_w * 0.5, div_y, cx + div_w * 0.5, div_y)
        div_pat.add_color_stop_rgba(0.0, *with_alpha(self.theme.accent, 0.0))
        div_pat.add_color_stop_rgba(0.5, *with_alpha(self.theme.accent, 0.5 * alpha))
        div_pat.add_color_stop_rgba(1.0, *with_alpha(self.theme.accent, 0.0))
        cr.set_source(div_pat)
        cr.set_line_width(1.2)
        cr.move_to(cx - div_w * 0.5, div_y)
        cr.line_to(cx + div_w * 0.5, div_y)
        cr.stroke()

        # Date Display
        if self.config.clock_show_date:
            weekday_str = time.strftime("%A", now).upper()
            date_str = time.strftime("%d %B %Y", now).upper()

            date_y1 = div_y + 24.0
            self.draw_text(
                cr, weekday_str, cx, date_y1,
                self.FONT_SANS, date_font_size * 1.15,
                with_alpha(self.theme.primary, alpha * 0.95),
                align="center", weight=Pango.Weight.BOLD
            )

            date_y2 = date_y1 + date_font_size * 1.5 + 4.0
            self.draw_text(
                cr, date_str, cx, date_y2,
                self.FONT_SANS, date_font_size * 0.95,
                with_alpha(self.theme.foreground, alpha * 0.8),
                align="center", weight=Pango.Weight.NORMAL
            )

        # System Metrics Pill
        if self.config.clock_show_system_info and self.metrics:
            m = self.metrics
            info_text = (
                f"CPU  {m.cpu_percent:04.1f}%    •    "
                f"RAM  {m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GB    •    "
                f"BAT  {m.battery_percent}%    •    "
                f"UPTIME  {m.uptime_str}"
            )

            pill_y = cy + h_h * 0.55 + 110.0
            layout_pill = self.create_pango_layout(
                cr, info_text, self.FONT_MONO, sys_font_size, Pango.Weight.NORMAL
            )
            _, ext_pill = layout_pill.get_pixel_extents()
            pw, ph = ext_pill.width + 36.0, ext_pill.height + 14.0

            # Rounded capsule pill
            px = cx - pw * 0.5
            py = pill_y - ph * 0.5

            self.draw_rounded_rect(cr, px, py, pw, ph, ph * 0.5)
            cr.set_source_rgba(*with_alpha(self.theme.surface, 0.65 * alpha))
            cr.fill_preserve()
            cr.set_source_rgba(*with_alpha(self.theme.primary, 0.25 * alpha))
            cr.set_line_width(1.0)
            cr.stroke()

            # Render pill text
            cr.set_source_rgba(*with_alpha(self.theme.foreground, 0.85 * alpha))
            cr.move_to(cx - ext_pill.width * 0.5, pill_y - ext_pill.height * 0.5)
            PangoCairo.show_layout(cr, layout_pill)
