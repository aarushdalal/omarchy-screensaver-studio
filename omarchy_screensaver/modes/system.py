"""Mode 4: Borderless Holographic Telemetry HUD.

Presents a futuristic holographic system telemetry interface with floating radial
arc tachometers, smooth flowing Bezier sparklines, and complete OLED burn-in defense.
Zero static rectangular card borders.
"""

import math
import time
from typing import List, Optional, Tuple

import cairo
from gi.repository import Pango, PangoCairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class SystemDashboardMode(BaseMode):
    """Futuristic borderless holographic telemetry HUD screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.fade_in: float = 0.0
        self.target_fps: int = 30

        # Eased metric values for organic motion
        self.eased_cpu = 0.0
        self.eased_mem = 0.0
        self.eased_bat = 0.0

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        if metrics:
            self.eased_cpu += (metrics.cpu_percent - self.eased_cpu) * min(1.0, dt * 5.0)
            self.eased_mem += (metrics.mem_percent - self.eased_mem) * min(1.0, dt * 5.0)
            self.eased_bat += (metrics.battery_percent - self.eased_bat) * min(1.0, dt * 3.0)

    def _draw_radial_gauge(
        self,
        cr: cairo.Context,
        cx: float,
        cy: float,
        radius: float,
        percent: float,
        label: str,
        value_str: str,
        sub_str: str,
        gauge_color: Tuple[float, float, float, float],
        fade: float,
    ):
        """Render a floating circular arc tachometer without background cards."""
        start_angle = 0.75 * math.pi
        total_angle = 1.5 * math.pi
        norm = max(0.0, min(100.0, percent)) / 100.0
        active_end = start_angle + total_angle * norm

        # Faint background track arc
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.surface, 0.35 * fade)))
        cr.set_line_width(6.0)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(cx, cy, radius, start_angle, start_angle + total_angle)
        cr.stroke()

        # Active glowing arc
        if norm > 0.01:
            # Subtle glow pass
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.25 * fade)))
            cr.set_line_width(12.0)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Crisp main arc
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.95 * fade)))
            cr.set_line_width(5.0)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

        # Center typography
        self.draw_text(
            cr, label, cx, cy - 26.0,
            self.FONT_MONO, 11.0,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.85)),
            align="center", weight=Pango.Weight.BOLD
        )
        self.draw_text(
            cr, value_str, cx, cy + 2.0,
            self.FONT_MONO, 22.0,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade)),
            align="center", weight=Pango.Weight.BOLD
        )
        if sub_str:
            self.draw_text(
                cr, sub_str, cx, cy + 26.0,
                self.FONT_MONO, 10.5,
                self.oled_color(with_alpha(self.theme.accent, fade * 0.8)),
                align="center", weight=Pango.Weight.NORMAL
            )

    def _draw_flowing_sparkline(
        self,
        cr: cairo.Context,
        x: float,
        y: float,
        w: float,
        h: float,
        history: List[float],
        max_val: float,
        color: Tuple[float, float, float, float],
        fade: float,
    ):
        """Draw an organic Bezier-curved telemetry graph."""
        if not history or len(history) < 2:
            return

        points = list(history)
        n = len(points)
        dx = w / max(1, n - 1)
        safe_max = max(1.0, max_val)
        base_y = y + h

        # Calculate coordinates
        coords = []
        for i, val in enumerate(points):
            norm = max(0.0, min(1.0, val / safe_max))
            px = x + i * dx
            py = base_y - norm * (h - 6.0)
            coords.append((px, py))

        # Build smooth path
        cr.new_path()
        cr.move_to(x, base_y)
        cr.line_to(coords[0][0], coords[0][1])

        for i in range(len(coords) - 1):
            p0 = coords[i]
            p1 = coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])

        # Fill down to baseline
        cr.line_to(x + w, base_y)
        cr.close_path()

        fill_grad = cairo.LinearGradient(x, y, x, base_y)
        fill_grad.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(color, 0.28 * fade)))
        fill_grad.add_color_stop_rgba(1.0, *self.oled_color(with_alpha(color, 0.0)))
        cr.set_source(fill_grad)
        cr.fill()

        # Stroke glowing curve
        cr.new_path()
        cr.move_to(coords[0][0], coords[0][1])
        for i in range(len(coords) - 1):
            p0 = coords[i]
            p1 = coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])

        cr.set_source_rgba(*self.oled_color(with_alpha(color, 0.92 * fade)))
        cr.set_line_width(1.8)
        cr.stroke()

        # Current live point node
        last_pt = coords[-1]
        cr.arc(last_pt[0], last_pt[1], 3.0, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.bright_foreground, fade)))
        cr.fill()

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.5 + self.burn_y + self.jitter_y

        now = time.localtime()
        time_str = time.strftime("%H:%M" if self.config.clock_format_24h else "%I:%M %p", now)
        date_str = time.strftime("%A · %d %B %Y", now).upper()

        top_y = cy - 250.0

        # Floating holographic header
        self.draw_text(
            cr, time_str, cx, top_y,
            self.FONT_MONO, 44.0,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade)),
            align="center", weight=Pango.Weight.BOLD, glow=True
        )
        self.draw_text(
            cr, f"// TELEMETRY HUD  —  {date_str}", cx, top_y + 46.0,
            self.FONT_SANS, 12.0,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.85)),
            align="center", weight=Pango.Weight.BOLD
        )

        if not self.metrics:
            return

        m = self.metrics

        # 1. Radial Tachometer Gauges (Left: CPU, Right: RAM)
        gauge_radius = min(78.0, width * 0.08)
        gauge_offset_x = min(300.0, width * 0.28)
        gauge_y = top_y + 175.0

        temp_str = f"{m.cpu_temp_c:.0f}°C" if m.cpu_temp_c > 0 else "NOMINAL"
        self._draw_radial_gauge(
            cr, cx - gauge_offset_x, gauge_y, gauge_radius,
            self.eased_cpu, "CPU LOAD", f"{self.eased_cpu:04.1f}%", temp_str,
            self.theme.accent, fade
        )

        mem_sub = f"{m.mem_used_gib:.1f}/{m.mem_total_gib:.1f} GB"
        self._draw_radial_gauge(
            cr, cx + gauge_offset_x, gauge_y, gauge_radius,
            self.eased_mem, "MEMORY", f"{self.eased_mem:04.1f}%", mem_sub,
            self.theme.primary, fade
        )

        # 2. Central Bezier CPU History Graph
        chart_w = min(420.0, width * 0.38)
        chart_h = 110.0
        chart_x = cx - chart_w * 0.5
        chart_y = gauge_y - chart_h * 0.5 + 8.0

        self.draw_text(
            cr, "CPU HISTORY", cx, chart_y - 12.0,
            self.FONT_MONO, 10.0,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.8)),
            align="center", weight=Pango.Weight.BOLD
        )
        self._draw_flowing_sparkline(
            cr, chart_x, chart_y, chart_w, chart_h,
            list(m.cpu_history), 100.0, self.theme.accent, fade
        )

        # 3. Bottom Telemetry Flow (Network, Battery, Storage)
        bottom_y = gauge_y + gauge_radius + 60.0
        rx_fmt = f"{m.net_rx_rate / (1024 * 1024):.1f}M" if m.net_rx_rate >= 1024 * 1024 else f"{m.net_rx_rate / 1024:.0f}K"
        tx_fmt = f"{m.net_tx_rate / (1024 * 1024):.1f}M" if m.net_tx_rate >= 1024 * 1024 else f"{m.net_tx_rate / 1024:.0f}K"

        row1_text = (
            f"NET ({m.primary_net_iface})  RX {rx_fmt}/s  TX {tx_fmt}/s   ·   "
            f"BAT {m.battery_percent}% [{m.battery_status}]   ·   "
            f"DISK {m.disk_used_gib:.1f}/{m.disk_total_gib:.1f} GB ({m.disk_percent:.0f}%)"
        )
        self.draw_text(
            cr, row1_text, cx, bottom_y,
            self.FONT_MONO, 12.0,
            self.oled_color(with_alpha(self.theme.foreground, fade * 0.85)),
            align="center", weight=Pango.Weight.NORMAL
        )

        row2_text = f"KERNEL {m.kernel}   ·   UPTIME {m.uptime_str}"
        self.draw_text(
            cr, row2_text, cx, bottom_y + 24.0,
            self.FONT_MONO, 10.5,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.65)),
            align="center", weight=Pango.Weight.NORMAL
        )
