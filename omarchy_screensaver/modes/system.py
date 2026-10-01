"""Mode 4: System Telemetry HUD Screensaver Mode.

A serene, borderless holographic HUD featuring floating circular tachometers,
organic Bezier telemetry curves, live GPU utilization, multi-channel power draw,
and complete OLED burn-in protection with spacious, theme-synchronized styling.
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
    """Minimalist, spacious, theme-synchronized system telemetry HUD."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.fade_in: float = 0.0
        self.target_fps: int = 30

        # Eased metric values for smooth, calming visual transitions
        self.eased_cpu: float = 0.0
        self.eased_gpu: float = 0.0
        self.eased_mem: float = 0.0
        self.eased_soc_power: float = 0.0
        self.eased_cpu_power: float = 0.0
        self.eased_gpu_power: float = 0.0

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.8)

        if metrics:
            self.eased_cpu += (metrics.cpu_percent - self.eased_cpu) * min(1.0, dt * 5.0)
            self.eased_gpu += (metrics.gpu_percent - self.eased_gpu) * min(1.0, dt * 5.0)
            self.eased_mem += (metrics.mem_percent - self.eased_mem) * min(1.0, dt * 4.0)
            self.eased_soc_power += (metrics.soc_power_w - self.eased_soc_power) * min(1.0, dt * 4.5)
            self.eased_cpu_power += (metrics.cpu_power_w - self.eased_cpu_power) * min(1.0, dt * 4.5)
            self.eased_gpu_power += (metrics.gpu_power_w - self.eased_gpu_power) * min(1.0, dt * 4.5)

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
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.surface, 0.40 * fade)))
        cr.set_line_width(5.5)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(cx, cy, radius, start_angle, start_angle + total_angle)
        cr.stroke()

        # Active glowing arc
        if norm > 0.01:
            # Soft aura glow pass
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.22 * fade)))
            cr.set_line_width(12.0)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Crisp main arc
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.95 * fade)))
            cr.set_line_width(4.5)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Luminous tip node
            tip_x = cx + math.cos(active_end) * radius
            tip_y = cy + math.sin(active_end) * radius
            cr.new_path()
            cr.arc(tip_x, tip_y, 3.0, 0, 2 * math.pi)
            cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.bright_foreground, 0.95 * fade)))
            cr.fill()

        # Center typography with generous breathing space
        self.draw_text(
            cr,
            label,
            cx,
            cy - 26.0,
            self.FONT_MONO,
            11.0,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.85)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            value_str,
            cx,
            cy + 2.0,
            self.FONT_MONO,
            23.0,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        if sub_str:
            self.draw_text(
                cr,
                sub_str,
                cx,
                cy + 28.0,
                self.FONT_MONO,
                10.5,
                self.oled_color(with_alpha(gauge_color, fade * 0.90)),
                align="center",
                weight=Pango.Weight.NORMAL,
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

        # Build smooth fill path down to baseline
        cr.new_path()
        cr.move_to(x, base_y)
        cr.line_to(coords[0][0], coords[0][1])

        for i in range(len(coords) - 1):
            p0 = coords[i]
            p1 = coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])

        cr.line_to(x + w, base_y)
        cr.close_path()

        fill_grad = cairo.LinearGradient(x, y, x, base_y)
        fill_grad.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(color, 0.22 * fade)))
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

        cr.set_source_rgba(*self.oled_color(with_alpha(color, 0.95 * fade)))
        cr.set_line_width(1.8)
        cr.stroke()

        # Current live point node
        last_pt = coords[-1]
        cr.new_path()
        cr.arc(last_pt[0], last_pt[1], 3.0, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.bright_foreground, fade)))
        cr.fill()

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.5 + self.burn_y + self.jitter_y - 10.0

        now = time.localtime()
        time_str = time.strftime("%H:%M:%S" if self.config.clock_format_24h else "%I:%M:%S %p", now)
        date_str = time.strftime("%A · %d %B %Y", now).upper()

        top_y = cy - 250.0

        # Floating holographic header
        self.draw_text(
            cr,
            time_str,
            cx,
            top_y,
            self.FONT_MONO,
            44.0,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade)),
            align="center",
            weight=Pango.Weight.BOLD,
            glow=True,
        )
        self.draw_text(
            cr,
            f"// SYSTEM TELEMETRY HUD  —  {date_str}",
            cx,
            top_y + 46.0,
            self.FONT_SANS,
            11.5,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.85)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        if not self.metrics:
            return

        m = self.metrics

        # 1. Radial Tachometer Gauges (Left: CPU, Right: RAM)
        gauge_radius = min(80.0, width * 0.08)
        gauge_offset_x = min(350.0, width * 0.28)
        gauge_y = top_y + 185.0

        # Left Gauge: CPU
        cpu_sub = f"{m.cpu_freq_avg_ghz:.2f} GHz · {m.cpu_temp_c:.0f}°C"
        self._draw_radial_gauge(
            cr,
            cx - gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_cpu,
            "CPU LOAD",
            f"{self.eased_cpu:04.1f}%",
            cpu_sub,
            self.theme.accent,
            fade,
        )

        # Right Gauge: Memory
        mem_sub = f"{m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GB"
        ram_color = self.theme.secondary if self.theme.secondary != self.theme.accent else self.theme.primary
        self._draw_radial_gauge(
            cr,
            cx + gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_mem,
            "MEMORY",
            f"{self.eased_mem:04.1f}%",
            mem_sub,
            ram_color,
            fade,
        )

        # 2. Central Bezier CPU History Graph
        chart_w = min(420.0, width * 0.36)
        chart_h = 100.0
        chart_x = cx - chart_w * 0.5
        chart_y = gauge_y - chart_h * 0.5 + 4.0

        self.draw_text(
            cr,
            "CPU LOAD HISTORY",
            cx,
            chart_y - 14.0,
            self.FONT_MONO,
            10.0,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.8)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self._draw_flowing_sparkline(
            cr,
            chart_x,
            chart_y,
            chart_w,
            chart_h,
            list(m.cpu_history),
            100.0,
            self.theme.accent,
            fade,
        )

        # 3. Spacious Telemetry Stream Below Gauges
        stream_y = gauge_y + gauge_radius + 64.0

        # Row 1: GPU & Multi-Channel Power Telemetry
        gpu_power_str = (
            f"GPU: {self.eased_gpu:04.1f}% · {m.gpu_clock_mhz:.0f} MHz · {m.gpu_temp_c:.0f}°C   ·   "
            f"POWER: CPU {self.eased_cpu_power:.1f}W   GPU {self.eased_gpu_power:.1f}W   TOTAL {self.eased_soc_power:.1f}W"
        )
        self.draw_text(
            cr,
            gpu_power_str,
            cx,
            stream_y,
            self.FONT_MONO,
            12.0,
            self.oled_color(with_alpha(self.theme.foreground, fade * 0.90)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        # Row 2: Storage, Network, and Battery
        rx_fmt = (
            f"{m.net_rx_rate / (1024 * 1024):.1f}M"
            if m.net_rx_rate >= 1024 * 1024
            else f"{m.net_rx_rate / 1024:.0f}K"
        )
        tx_fmt = (
            f"{m.net_tx_rate / (1024 * 1024):.1f}M"
            if m.net_tx_rate >= 1024 * 1024
            else f"{m.net_tx_rate / 1024:.0f}K"
        )
        net_str = f"NET ({m.primary_net_iface}) ↓ {rx_fmt}/s ↑ {tx_fmt}/s"
        disk_str = f"DISK {m.disk_used_gib:.1f}/{m.disk_total_gib:.1f} GB ({m.disk_percent:.0f}%)"
        bat_str = f"BAT {m.battery_percent}% [{m.battery_status}]"
        row2_str = f"{disk_str}   ·   {net_str}   ·   {bat_str}"
        self.draw_text(
            cr,
            row2_str,
            cx,
            stream_y + 32.0,
            self.FONT_MONO,
            11.0,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.85)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        # Row 3: Kernel, Uptime, Hardware Thermals, and User
        row3_str = (
            f"KERNEL {m.kernel}   ·   UPTIME {m.uptime_str}   ·   "
            f"NVMe {m.nvme_temp_c:.0f}°C   ·   USER {m.user}@{m.hostname}"
        )
        self.draw_text(
            cr,
            row3_str,
            cx,
            stream_y + 60.0,
            self.FONT_MONO,
            10.0,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.65)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )
