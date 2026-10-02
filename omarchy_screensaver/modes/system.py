"""Mode 4: System Telemetry HUD Screensaver Mode.

A serene, borderless holographic HUD featuring three floating speedometer tachometers
(CPU, GPU, and Memory), an organic Bezier system load wave, multi-channel power draw,
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

    def _draw_speedometer_gauge(
        self,
        cr: cairo.Context,
        cx: float,
        cy: float,
        radius: float,
        percent: float,
        label: str,
        value_str: str,
        sub_str: str,
        bottom_badge: Optional[str],
        gauge_color: Tuple[float, float, float, float],
        fade: float,
        scale: float = 1.0,
    ):
        """Render a relaxing, borderless speedometer tachometer strictly in theme colors."""
        start_angle = 0.75 * math.pi
        total_angle = 1.5 * math.pi
        norm = max(0.0, min(100.0, percent)) / 100.0
        active_end = start_angle + total_angle * norm

        # 1. Faint background track arc
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(self.theme.track_arc_color(fade)))
        cr.set_line_width(4.5 * scale)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(cx, cy, radius, start_angle, start_angle + total_angle)
        cr.stroke()

        # 2. Delicate radial hash tick marks (speedometer ticks in theme tones)
        num_ticks = 10
        inactive_tick_col = self.theme.track_tick_inactive_color(fade)
        active_tick_col = with_alpha(gauge_color, 0.85 * fade)

        for i in range(num_ticks + 1):
            frac = i / num_ticks
            ang = start_angle + total_angle * frac

            r_out = radius + 2.0 * scale
            r_in = r_out - 6.0 * scale
            x1 = cx + math.cos(ang) * r_in
            y1 = cy + math.sin(ang) * r_in
            x2 = cx + math.cos(ang) * r_out
            y2 = cy + math.sin(ang) * r_out

            cr.new_path()
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            tick_col = active_tick_col if frac <= norm else inactive_tick_col
            cr.set_source_rgba(*self.oled_color(tick_col))
            cr.set_line_width(1.4 * scale)
            cr.stroke()

            # Intermediate minor ticks
            if i < num_ticks:
                m_frac = (i + 0.5) / num_ticks
                m_ang = start_angle + total_angle * m_frac
                mx1 = cx + math.cos(m_ang) * (radius - 1.5 * scale)
                my1 = cy + math.sin(m_ang) * (radius - 1.5 * scale)
                mx2 = cx + math.cos(m_ang) * (radius + 2.0 * scale)
                my2 = cy + math.sin(m_ang) * (radius + 2.0 * scale)
                cr.new_path()
                cr.move_to(mx1, my1)
                cr.line_to(mx2, my2)
                m_col = (
                    with_alpha(gauge_color, 0.45 * fade)
                    if m_frac <= norm
                    else with_alpha(inactive_tick_col, inactive_tick_col[3] * 0.6)
                )
                cr.set_source_rgba(*self.oled_color(m_col))
                cr.set_line_width(0.9 * scale)
                cr.stroke()

        # 3. Active glowing speed arc
        if norm > 0.005:
            # Soft aura glow pass
            cr.new_path()
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.22 * fade)))
            cr.set_line_width(11.0 * scale)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Crisp main arc ribbon
            cr.new_path()
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.95 * fade)))
            cr.set_line_width(4.0 * scale)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Glowing tip node
            tip_x = cx + math.cos(active_end) * radius
            tip_y = cy + math.sin(active_end) * radius
            cr.new_path()
            cr.arc(tip_x, tip_y, 3.2 * scale, 0, 2 * math.pi)
            cr.set_source_rgba(*self.oled_color(self.theme.text_primary_color(fade)))
            cr.fill()

        # 4. Center typography with calm, spacious breathing room
        self.draw_text(
            cr,
            label,
            cx,
            cy - 25.0 * scale,
            self.FONT_MONO,
            10.5 * scale,
            self.oled_color(self.theme.text_muted_color(fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            value_str,
            cx,
            cy + 3.0 * scale,
            self.FONT_MONO,
            22.0 * scale,
            self.oled_color(self.theme.text_primary_color(fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        if sub_str:
            self.draw_text(
                cr,
                sub_str,
                cx,
                cy + 28.0 * scale,
                self.FONT_MONO,
                10.0 * scale,
                self.oled_color(with_alpha(gauge_color, fade * 0.95)),
                align="center",
                weight=Pango.Weight.NORMAL,
            )

        # 5. Bottom sub-badge under gauge (calm, spacious, borderless)
        if bottom_badge:
            self.draw_text(
                cr,
                bottom_badge,
                cx,
                cy + radius + 20.0 * scale,
                self.FONT_MONO,
                8.5 * scale,
                self.oled_color(self.theme.text_muted_color(fade * 0.85)),
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
        scale: float = 1.0,
    ):
        """Draw an organic Bezier-curved telemetry graph."""
        history_list = list(history) if history else [0.0]
        max_history = 60
        if len(history_list) < max_history:
            initial_val = history_list[0] if history_list else 0.0
            points = [initial_val] * (max_history - len(history_list)) + history_list
        else:
            points = history_list[-max_history:]

        n = len(points)
        dx = w / max(1, n - 1)
        safe_max = max(1.0, max_val)
        base_y = y + h

        # Calculate coordinates
        coords = []
        for i, val in enumerate(points):
            norm = max(0.0, min(1.0, val / safe_max))
            px = x + i * dx
            py = base_y - norm * (h - 6.0 * scale)
            coords.append((px, py))

        # Build smooth path down to baseline
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
        fill_alpha = 0.20 if getattr(self.theme, "is_dark", True) else 0.18
        fill_grad.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(color, fill_alpha * fade)))
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
        cr.set_line_width(1.8 * scale)
        cr.stroke()

        # Current live point node
        last_pt = coords[-1]
        cr.new_path()
        cr.arc(last_pt[0], last_pt[1], 3.0 * scale, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(self.theme.text_primary_color(fade)))
        cr.fill()

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.5 + self.burn_y + self.jitter_y - 12.0

        # UI Scale factor to ensure crisp, balanced proportions across HiDPI and resolutions
        ui_scale = min(width / 1920.0, height / 1080.0)
        ui_scale = max(0.70, min(2.20, ui_scale))

        now = time.localtime()
        time_str = time.strftime("%H:%M:%S" if self.config.clock_format_24h else "%I:%M:%S %p", now)
        date_str = time.strftime("%A · %d %B %Y", now).upper()

        top_y = cy - 280.0 * ui_scale

        # Floating holographic header
        self.draw_text(
            cr,
            time_str,
            cx,
            top_y,
            self.FONT_MONO,
            44.0 * ui_scale,
            self.oled_color(self.theme.text_primary_color(fade)),
            align="center",
            weight=Pango.Weight.BOLD,
            glow=True,
        )
        self.draw_text(
            cr,
            f"// SYSTEM TELEMETRY HUD  —  {date_str}",
            cx,
            top_y + 46.0 * ui_scale,
            self.FONT_SANS,
            11.5 * ui_scale,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        if not self.metrics:
            return

        m = self.metrics

        # 1. Tri-Gauge Instrument Cluster (CPU, GPU, RAM) with Speedometer Styling
        gauge_radius = min(78.0 * ui_scale, width * 0.12)
        gauge_offset_x = min(360.0 * ui_scale, width * 0.35)
        gauge_y = top_y + 175.0 * ui_scale

        cpu_color = self.theme.accent
        gpu_color = self.theme.primary
        ram_color = self.theme.secondary if self.theme.secondary != self.theme.accent else self.theme.primary

        # Left: CPU Speedometer Gauge
        cpu_sub = (
            f"{m.cpu_freq_avg_ghz:4.2f} GHz · {m.cpu_temp_c:2.0f}°C"
            if m.cpu_temp_c > 0
            else f"{m.cpu_freq_avg_ghz:4.2f} GHz"
        )
        self._draw_speedometer_gauge(
            cr,
            cx - gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_cpu,
            "CPU LOAD",
            f"{self.eased_cpu:5.1f}%",
            cpu_sub,
            m.cpu_model,
            cpu_color,
            fade,
            scale=ui_scale,
        )

        # Center: GPU Speedometer Gauge
        gpu_sub = (
            f"{m.gpu_clock_mhz:4.0f} MHz · {m.gpu_temp_c:2.0f}°C"
            if m.gpu_temp_c > 0
            else f"{m.gpu_clock_mhz:4.0f} MHz"
        )
        gpu_badge = f"VRAM {m.gpu_vram_used_mib:3.0f}/{m.gpu_vram_total_mib:3.0f} MB  ·  GTT {m.gpu_gtt_used_gib:3.1f} GB"
        self._draw_speedometer_gauge(
            cr,
            cx,
            gauge_y,
            gauge_radius,
            self.eased_gpu,
            "GPU LOAD",
            f"{self.eased_gpu:5.1f}%",
            gpu_sub,
            gpu_badge,
            gpu_color,
            fade,
            scale=ui_scale,
        )

        # Right: RAM Speedometer Gauge
        mem_sub = f"{m.mem_used_gib:4.1f} / {m.mem_total_gib:4.1f} GB"
        mem_badge = f"FREE {m.mem_avail_gib:4.1f}G  ·  SWAP {m.swap_used_gib:3.1f}G ({m.swap_percent:2.0f}%)"
        self._draw_speedometer_gauge(
            cr,
            cx + gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_mem,
            "MEMORY",
            f"{self.eased_mem:5.1f}%",
            mem_sub,
            mem_badge,
            ram_color,
            fade,
            scale=ui_scale,
        )

        # 2. Central Live Bezier Telemetry Sparkline with generous vertical breathing room
        chart_w = min(620.0 * ui_scale, width * 0.45)
        chart_h = 75.0 * ui_scale
        chart_x = cx - chart_w * 0.5
        chart_y = gauge_y + gauge_radius + 68.0 * ui_scale

        self.draw_text(
            cr,
            "SYSTEM LOAD SPECTRUM",
            cx,
            chart_y - 16.0 * ui_scale,
            self.FONT_MONO,
            9.5 * ui_scale,
            self.oled_color(self.theme.text_muted_color(fade * 0.85)),
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
            scale=ui_scale,
        )

        # 3. Multi-Channel Power Draw HUD (Theme Colored, Relaxed & Spacious)
        power_y = chart_y + chart_h + 36.0 * ui_scale
        bat_str = (
            f"BATTERY {m.battery_percent}% [{m.battery_status}] {m.bat_power_w:4.1f}W"
            if m.has_battery
            else "AC POWERED"
        )
        power_str = (
            f"POWER DRAW:   CPU {self.eased_cpu_power:4.1f}W   ·   "
            f"GPU {self.eased_gpu_power:4.1f}W   ·   "
            f"TOTAL SoC {self.eased_soc_power:4.1f}W   ·   "
            f"{bat_str}"
        )
        self.draw_text(
            cr,
            power_str,
            cx,
            power_y,
            self.FONT_MONO,
            11.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        # 4. Storage, Network, and Thermals
        stream_y = power_y + 30.0 * ui_scale
        rx_fmt = (
            f"{m.net_rx_rate / (1024 * 1024):4.1f}M"
            if m.net_rx_rate >= 1024 * 1024
            else f"{m.net_rx_rate / 1024:4.0f}K"
        )
        tx_fmt = (
            f"{m.net_tx_rate / (1024 * 1024):4.1f}M"
            if m.net_tx_rate >= 1024 * 1024
            else f"{m.net_tx_rate / 1024:4.0f}K"
        )
        net_str = (
            f"NET ({m.primary_net_iface}) ↓ {rx_fmt}/s ↑ {tx_fmt}/s"
            if m.primary_net_iface
            else "NET OFFLINE"
        )
        nvme_str = f"   ·   NVMe SSD {m.nvme_temp_c:2.0f}°C" if m.nvme_temp_c > 0 else ""
        row2_str = (
            f"STORAGE {m.disk_used_gib:5.1f}/{m.disk_total_gib:5.1f} GB ({m.disk_percent:2.0f}%)   ·   "
            f"{net_str}{nvme_str}"
        )
        self.draw_text(
            cr,
            row2_str,
            cx,
            stream_y,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        # 5. OS Diagnostics & Identity Stream
        diag_y = stream_y + 26.0 * ui_scale
        row3_str = (
            f"KERNEL {m.kernel}   ·   UPTIME {m.uptime_str}   ·   "
            f"USER {m.user}@{m.hostname}"
        )
        self.draw_text(
            cr,
            row3_str,
            cx,
            diag_y,
            self.FONT_MONO,
            10.0 * ui_scale,
            self.oled_color(self.theme.text_muted_color(fade * 0.90)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )
