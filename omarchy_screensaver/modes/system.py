"""Mode 4: Futuristic System Monitor Dashboard.

Presents a cybernetic dashboard with live animated sparkline history charts,
meter bars for CPU, RAM, Battery, Network, and Storage.
"""

import math
import time
from typing import List, Optional, Tuple

import cairo
from gi.repository import Pango

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class SystemDashboardMode(BaseMode):
    """Futuristic system telemetry dashboard screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.fade_in: float = 0.0
        self.target_fps: int = 20

        # Eased metric display values for silky smooth transitions
        self.eased_cpu = 0.0
        self.eased_mem = 0.0
        self.eased_bat = 0.0

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        if metrics:
            # Smooth lerp
            self.eased_cpu += (metrics.cpu_percent - self.eased_cpu) * min(1.0, dt * 6.0)
            self.eased_mem += (metrics.mem_percent - self.eased_mem) * min(1.0, dt * 6.0)
            self.eased_bat += (metrics.battery_percent - self.eased_bat) * min(1.0, dt * 4.0)

    def _draw_meter_bar(
        self,
        cr: cairo.Context,
        x: float,
        y: float,
        w: float,
        h: float,
        percent: float,
        fill_color: Tuple[float, float, float, float],
        fade: float,
    ):
        """Draw a futuristic segmented meter bar."""
        # Background track
        self.draw_rounded_rect(cr, x, y, w, h, h * 0.4)
        cr.set_source_rgba(*with_alpha(self.theme.surface, 0.7 * fade))
        cr.fill_preserve()
        cr.set_source_rgba(*with_alpha(self.theme.primary, 0.15 * fade))
        cr.set_line_width(1.0)
        cr.stroke()

        # Filled portion
        fill_w = max(h, w * (max(0.0, min(100.0, percent)) / 100.0))
        self.draw_rounded_rect(cr, x, y, fill_w, h, h * 0.4)
        grad = cairo.LinearGradient(x, y, x + fill_w, y)
        grad.add_color_stop_rgba(0.0, *with_alpha(fill_color, 0.85 * fade))
        grad.add_color_stop_rgba(1.0, *with_alpha(fill_color, 1.0 * fade))
        cr.set_source(grad)
        cr.fill()

    def _draw_sparkline(
        self,
        cr: cairo.Context,
        x: float,
        y: float,
        w: float,
        h: float,
        history: List[float],
        max_val: float,
        line_color: Tuple[float, float, float, float],
        fade: float,
    ):
        """Draw an area sparkline graph with gradient fill."""
        if not history or len(history) < 2:
            return

        points = list(history)
        n = len(points)
        dx = w / max(1, n - 1)
        safe_max = max(1.0, max_val)

        # Baseline
        base_y = y + h

        # Build path
        cr.new_path()
        cr.move_to(x, base_y)

        path_points = []
        for i, val in enumerate(points):
            norm = max(0.0, min(1.0, val / safe_max))
            px = x + i * dx
            py = base_y - norm * (h - 4.0)
            path_points.append((px, py))

        cr.line_to(path_points[0][0], path_points[0][1])
        for px, py in path_points[1:]:
            cr.line_to(px, py)

        # Fill under curve
        cr.line_to(x + w, base_y)
        cr.close_path()

        fill_pat = cairo.LinearGradient(x, y, x, base_y)
        fill_pat.add_color_stop_rgba(0.0, *with_alpha(line_color, 0.25 * fade))
        fill_pat.add_color_stop_rgba(1.0, *with_alpha(line_color, 0.02 * fade))
        cr.set_source(fill_pat)
        cr.fill()

        # Stroke line on top
        cr.new_path()
        cr.move_to(path_points[0][0], path_points[0][1])
        for px, py in path_points[1:]:
            cr.line_to(px, py)
        cr.set_source_rgba(*with_alpha(line_color, 0.9 * fade))
        cr.set_line_width(1.4)
        cr.stroke()

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)

        fade = self.fade_in
        cx = width * 0.5 + self.burn_x
        cy = height * 0.5 + self.burn_y

        # Header Clock & Status
        now = time.localtime()
        time_str = time.strftime("%H:%M" if self.config.clock_format_24h else "%I:%M %p", now)
        date_str = time.strftime("%A, %d %B %Y", now).upper()

        top_y = cy - 290.0

        # Clock
        self.draw_text(
            cr, time_str, cx, top_y,
            self.FONT_MONO, 38.0, with_alpha(self.theme.bright_foreground, fade),
            align="center", weight=Pango.Weight.BOLD, glow=True
        )

        # Subtitle
        self.draw_text(
            cr, f"SYSTEM MONITOR  •  {date_str}", cx, top_y + 42.0,
            self.FONT_SANS, 12.0, with_alpha(self.theme.accent, fade * 0.9),
            align="center", weight=Pango.Weight.BOLD
        )

        if not self.metrics:
            return

        m = self.metrics

        # Cards Layout (2 columns of cards)
        card_w = min(480.0, width * 0.44)
        card_h = 135.0
        gap_x = 24.0
        gap_y = 20.0

        col1_x = cx - card_w - gap_x * 0.5
        col2_x = cx + gap_x * 0.5
        row1_y = top_y + 80.0
        row2_y = row1_y + card_h + gap_y
        row3_y = row2_y + card_h + gap_y

        # Card 1: CPU
        self._render_card(cr, col1_x, row1_y, card_w, card_h, fade)
        self.draw_text(
            cr, "CPU UTILIZATION", col1_x + 18.0, row1_y + 22.0,
            self.FONT_MONO, 11.0, with_alpha(self.theme.primary, fade), align="left", weight=Pango.Weight.BOLD
        )
        temp_str = f"{m.cpu_temp_c:.0f}°C  •  " if m.cpu_temp_c > 0 else ""
        self.draw_text(
            cr, f"{temp_str}{self.eased_cpu:04.1f}%", col1_x + card_w - 18.0, row1_y + 22.0,
            self.FONT_MONO, 12.0, with_alpha(self.theme.bright_foreground, fade), align="right", weight=Pango.Weight.BOLD
        )
        self._draw_meter_bar(cr, col1_x + 18.0, row1_y + 36.0, card_w - 36.0, 8.0, self.eased_cpu, self.theme.accent, fade)
        self._draw_sparkline(
            cr, col1_x + 18.0, row1_y + 54.0, card_w - 36.0, card_h - 68.0,
            list(m.cpu_history), 100.0, self.theme.accent, fade
        )

        # Card 2: MEMORY
        self._render_card(cr, col2_x, row1_y, card_w, card_h, fade)
        self.draw_text(
            cr, "SYSTEM MEMORY", col2_x + 18.0, row1_y + 22.0,
            self.FONT_MONO, 11.0, with_alpha(self.theme.primary, fade), align="left", weight=Pango.Weight.BOLD
        )
        self.draw_text(
            cr, f"{m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GiB ({self.eased_mem:04.1f}%)",
            col2_x + card_w - 18.0, row1_y + 22.0,
            self.FONT_MONO, 12.0, with_alpha(self.theme.bright_foreground, fade), align="right", weight=Pango.Weight.BOLD
        )
        self._draw_meter_bar(cr, col2_x + 18.0, row1_y + 36.0, card_w - 36.0, 8.0, self.eased_mem, self.theme.secondary, fade)
        self._draw_sparkline(
            cr, col2_x + 18.0, row1_y + 54.0, card_w - 36.0, card_h - 68.0,
            list(m.mem_history), 100.0, self.theme.secondary, fade
        )

        # Card 3: POWER & BATTERY
        self._render_card(cr, col1_x, row2_y, card_w, card_h, fade)
        self.draw_text(
            cr, "BATTERY & POWER", col1_x + 18.0, row2_y + 22.0,
            self.FONT_MONO, 11.0, with_alpha(self.theme.primary, fade), align="left", weight=Pango.Weight.BOLD
        )
        ac_badge = " [AC CONNECTED]" if m.ac_online else " [DISCHARGING]"
        self.draw_text(
            cr, f"{m.battery_percent}%{ac_badge}", col1_x + card_w - 18.0, row2_y + 22.0,
            self.FONT_MONO, 11.5, with_alpha(self.theme.bright_foreground, fade), align="right", weight=Pango.Weight.BOLD
        )
        bat_color = self.theme.success if m.battery_percent > 30 else self.theme.danger
        self._draw_meter_bar(cr, col1_x + 18.0, row2_y + 38.0, card_w - 36.0, 10.0, float(m.battery_percent), bat_color, fade)
        self.draw_text(
            cr, f"Status: {m.battery_status}   •   Uptime: {m.uptime_str}", col1_x + 18.0, row2_y + 70.0,
            self.FONT_MONO, 11.0, with_alpha(self.theme.muted, fade), align="left"
        )
        self.draw_text(
            cr, f"Host: {m.hostname}   •   User: {m.user}", col1_x + 18.0, row2_y + 92.0,
            self.FONT_MONO, 11.0, with_alpha(self.theme.muted, fade), align="left"
        )

        # Card 4: NETWORK TRAFFIC
        self._render_card(cr, col2_x, row2_y, card_w, card_h, fade)
        rx_fmt = f"{m.net_rx_rate / (1024*1024):.1f} MB/s" if m.net_rx_rate >= 1024*1024 else f"{m.net_rx_rate / 1024:.0f} KB/s"
        tx_fmt = f"{m.net_tx_rate / (1024*1024):.1f} MB/s" if m.net_tx_rate >= 1024*1024 else f"{m.net_tx_rate / 1024:.0f} KB/s"
        self.draw_text(
            cr, f"NETWORK ({m.primary_net_iface})", col2_x + 18.0, row2_y + 22.0,
            self.FONT_MONO, 11.0, with_alpha(self.theme.primary, fade), align="left", weight=Pango.Weight.BOLD
        )
        self.draw_text(
            cr, f"RX {rx_fmt}  │  TX {tx_fmt}", col2_x + card_w - 18.0, row2_y + 22.0,
            self.FONT_MONO, 11.5, with_alpha(self.theme.bright_foreground, fade), align="right", weight=Pango.Weight.BOLD
        )
        max_net = max(100000.0, max(m.net_rx_history) if m.net_rx_history else 100000.0)
        self._draw_sparkline(
            cr, col2_x + 18.0, row2_y + 44.0, card_w - 36.0, card_h - 58.0,
            list(m.net_rx_history), max_net, self.theme.info, fade
        )

        # Footer Disk Summary
        disk_w = card_w * 2.0 + gap_x
        disk_x = cx - disk_w * 0.5
        self._render_card(cr, disk_x, row3_y, disk_w, 65.0, fade)
        self.draw_text(
            cr, f"ROOT STORAGE (/) : {m.disk_used_gib:.1f} / {m.disk_total_gib:.1f} GiB ({m.disk_percent:.1f}% ALLOCATED)",
            disk_x + 18.0, row3_y + 22.0, self.FONT_MONO, 11.0,
            with_alpha(self.theme.primary, fade), align="left", weight=Pango.Weight.BOLD
        )
        self._draw_meter_bar(cr, disk_x + 18.0, row3_y + 36.0, disk_w - 36.0, 8.0, m.disk_percent, self.theme.primary, fade)

    def _render_card(self, cr: cairo.Context, x: float, y: float, w: float, h: float, fade: float):
        """Render a rounded glass card container."""
        self.draw_rounded_rect(cr, x, y, w, h, 8.0)
        cr.set_source_rgba(*with_alpha(self.theme.card_bg, 0.75 * fade))
        cr.fill_preserve()
        cr.set_source_rgba(*with_alpha(self.theme.primary, 0.20 * fade))
        cr.set_line_width(1.0)
        cr.stroke()
