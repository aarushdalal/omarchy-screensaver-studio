"""Mode 4: Digital Speedometer Telemetry HUD screensaver mode.

Combines the classic borderless holographic HUD aesthetic with precision
automotive speedometer mechanics: delicate radial ticks, redline warning zones,
sweeping glowing needles, peak-hold indicators, central Bezier telemetry sparkline,
dedicated GPU telemetry strip, multi-channel power draw (CPU, GPU, SoC, Battery),
and complete OLED burn-in defense.
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
    """Futuristic automotive digital speedometer telemetry screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.fade_in: float = 0.0
        self.target_fps: int = 30

        # Eased metric values for organic speedometer needle motion
        self.eased_cpu: float = 0.0
        self.eased_gpu: float = 0.0
        self.eased_mem: float = 0.0
        self.eased_soc_power: float = 0.0
        self.eased_cpu_power: float = 0.0
        self.eased_gpu_power: float = 0.0

        # Peak hold indicators (with 3-second hold and smooth decay)
        self.peak_cpu: float = 0.0
        self.peak_cpu_timer: float = 0.0
        self.peak_mem: float = 0.0
        self.peak_mem_timer: float = 0.0

        # Micro needle engine vibration timer at high load
        self.vibe_phase: float = 0.0

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.metrics = metrics

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.8)

        if metrics:
            # Needle easing (smooth spring-damped acceleration and soft stop)
            self.eased_cpu += (metrics.cpu_percent - self.eased_cpu) * min(1.0, dt * 6.5)
            self.eased_gpu += (metrics.gpu_percent - self.eased_gpu) * min(1.0, dt * 6.5)
            self.eased_mem += (metrics.mem_percent - self.eased_mem) * min(1.0, dt * 4.5)
            self.eased_soc_power += (metrics.soc_power_w - self.eased_soc_power) * min(1.0, dt * 5.0)
            self.eased_cpu_power += (metrics.cpu_power_w - self.eased_cpu_power) * min(1.0, dt * 5.0)
            self.eased_gpu_power += (metrics.gpu_power_w - self.eased_gpu_power) * min(1.0, dt * 5.0)

            # Peak hold tracking
            if metrics.cpu_percent > self.peak_cpu:
                self.peak_cpu = metrics.cpu_percent
                self.peak_cpu_timer = 3.0
            else:
                self.peak_cpu_timer -= dt
                if self.peak_cpu_timer <= 0:
                    self.peak_cpu = max(self.eased_cpu, self.peak_cpu - dt * 18.0)

            if metrics.mem_percent > self.peak_mem:
                self.peak_mem = metrics.mem_percent
                self.peak_mem_timer = 3.0
            else:
                self.peak_mem_timer -= dt
                if self.peak_mem_timer <= 0:
                    self.peak_mem = max(self.eased_mem, self.peak_mem - dt * 12.0)

            self.vibe_phase += dt * 36.0

    def _draw_minimal_speedometer_gauge(
        self,
        cr: cairo.Context,
        cx: float,
        cy: float,
        radius: float,
        percent: float,
        peak_percent: float,
        label: str,
        unit: str,
        primary_color: Tuple[float, float, float, float],
        sub_text: str,
        extra_badge: Optional[str],
        fade: float,
    ):
        """Render a minimalist automotive speedometer / tachometer instrument dial."""
        start_ang = 0.75 * math.pi
        total_ang = 1.5 * math.pi

        # Subtle engine mechanical micro-vibration when load > 75%
        vibe = 0.0
        if percent > 75.0:
            vibe = (math.sin(self.vibe_phase) * 0.20) * ((percent - 75.0) / 25.0)
        norm = max(0.0, min(100.0, percent + vibe)) / 100.0
        cur_ang = start_ang + total_ang * norm

        # 1. Faint Background Track Arc (Borderless, zero solid card fill)
        cr.new_path()
        cr.arc(cx, cy, radius, start_ang, start_ang + total_ang)
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.surface, 0.35 * fade)))
        cr.set_line_width(2.5)
        cr.stroke()

        # 2. Redline Zone Background Warning Glow (80% - 100%)
        redline_start = start_ang + total_ang * 0.80
        cr.new_path()
        cr.arc(cx, cy, radius, redline_start, start_ang + total_ang)
        cr.set_source_rgba(*self.oled_color((1.0, 0.22, 0.32, 0.22 * fade)))
        cr.set_line_width(4.5)
        cr.stroke()

        # 3. Delicate Radial Speedometer Hash Ticks & Numbers
        num_steps = 10
        for i in range(num_steps + 1):
            frac = i / num_steps
            ang = start_ang + total_ang * frac
            is_redline = frac >= 0.8

            r_outer = radius + 1.0
            r_inner = r_outer - 7.5
            x1 = cx + math.cos(ang) * r_inner
            y1 = cy + math.sin(ang) * r_inner
            x2 = cx + math.cos(ang) * r_outer
            y2 = cy + math.sin(ang) * r_outer

            cr.new_path()
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            tick_col = (1.0, 0.25, 0.35, 0.90 * fade) if is_redline else with_alpha(self.theme.foreground, 0.70 * fade)
            cr.set_source_rgba(*self.oled_color(tick_col))
            cr.set_line_width(1.5)
            cr.stroke()

            # Speedometer numbers at even marks (0, 20, 40, 60, 80, 100)
            if i % 2 == 0:
                r_text = radius - 17.0
                tx = cx + math.cos(ang) * r_text
                ty = cy + math.sin(ang) * r_text
                num_col = (1.0, 0.30, 0.40, 0.85 * fade) if is_redline else with_alpha(self.theme.muted, 0.80 * fade)
                self.draw_text(
                    cr,
                    f"{i * 10}",
                    tx,
                    ty,
                    self.FONT_MONO,
                    7.5,
                    self.oled_color(num_col),
                    align="center",
                    weight=Pango.Weight.BOLD,
                )

            # Intermediate minor ticks
            if i < num_steps:
                m_frac = (i + 0.5) / num_steps
                m_ang = start_ang + total_ang * m_frac
                m_redline = m_frac >= 0.8
                mx1 = cx + math.cos(m_ang) * (radius - 3.5)
                my1 = cy + math.sin(m_ang) * (radius - 3.5)
                mx2 = cx + math.cos(m_ang) * (radius + 1.0)
                my2 = cy + math.sin(m_ang) * (radius + 1.0)
                cr.new_path()
                cr.move_to(mx1, my1)
                cr.line_to(mx2, my2)
                m_col = (1.0, 0.25, 0.35, 0.45 * fade) if m_redline else with_alpha(self.theme.muted, 0.35 * fade)
                cr.set_source_rgba(*self.oled_color(m_col))
                cr.set_line_width(1.0)
                cr.stroke()

        # 4. Active Dynamic Glowing Speed Arc
        if norm > 0.005:
            if norm >= 0.80:
                arc_col = (1.0, 0.25, 0.35, 1.0)
            elif norm >= 0.60:
                arc_col = (1.0, 0.65, 0.15, 1.0)
            else:
                arc_col = primary_color

            # Outer soft neon aura
            cr.new_path()
            cr.arc(cx, cy, radius, start_ang, cur_ang)
            cr.set_source_rgba(*self.oled_color(with_alpha(arc_col, 0.22 * fade)))
            cr.set_line_width(8.0)
            cr.stroke()

            # Crisp luminous main ribbon
            cr.new_path()
            cr.arc(cx, cy, radius, start_ang, cur_ang)
            cr.set_source_rgba(*self.oled_color(with_alpha(arc_col, 0.95 * fade)))
            cr.set_line_width(2.8)
            cr.stroke()

        # 5. Peak-Hold Indicator Pip
        if peak_percent > 1.0:
            peak_norm = max(0.0, min(100.0, peak_percent)) / 100.0
            peak_ang = start_ang + total_ang * peak_norm
            px1 = cx + math.cos(peak_ang) * (radius - 8.0)
            py1 = cy + math.sin(peak_ang) * (radius - 8.0)
            px2 = cx + math.cos(peak_ang) * (radius + 1.0)
            py2 = cy + math.sin(peak_ang) * (radius + 1.0)
            cr.new_path()
            cr.move_to(px1, py1)
            cr.line_to(px2, py2)
            cr.set_source_rgba(*self.oled_color((1.0, 0.88, 0.35, 0.95 * fade)))
            cr.set_line_width(2.0)
            cr.stroke()

        # 6. Precision Sweeping Speedometer Needle
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(cur_ang)

        needle_col = (1.0, 0.28, 0.25) if norm >= 0.8 else (1.0, 0.45, 0.18)

        # Needle tapered silhouette
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(with_alpha(needle_col, 0.96 * fade)))
        cr.move_to(-10.0, 0.0)
        cr.line_to(-2.0, -1.8)
        cr.line_to(radius - 5.0, -0.4)
        cr.line_to(radius - 5.0, 0.4)
        cr.line_to(-2.0, 1.8)
        cr.close_path()
        cr.fill()

        # Needle white core reflection
        cr.new_path()
        cr.set_source_rgba(*self.oled_color((1.0, 1.0, 1.0, 0.85 * fade)))
        cr.set_line_width(0.8)
        cr.move_to(0, 0)
        cr.line_to(radius - 8.0, 0)
        cr.stroke()
        cr.restore()

        # 7. Metallic Needle Boss Hub Cap
        cr.new_path()
        cr.arc(cx, cy, 4.5, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color((0.10, 0.12, 0.16, 1.0 * fade)))
        cr.fill()
        cr.new_path()
        cr.arc(cx, cy, 4.5, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color((0.50, 0.58, 0.70, 0.9 * fade)))
        cr.set_line_width(1.2)
        cr.stroke()

        # Center Jewel Pin
        cr.new_path()
        cr.arc(cx, cy, 2.0, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color(with_alpha(needle_col, 0.98 * fade)))
        cr.fill()

        # 8. Center Digital Readouts
        self.draw_text(
            cr,
            label,
            cx,
            cy - 28.0,
            self.FONT_MONO,
            10.0,
            self.oled_color(with_alpha(primary_color, 0.95 * fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            f"{percent:04.1f}%",
            cx,
            cy + 8.0,
            self.FONT_MONO,
            21.0,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            sub_text,
            cx,
            cy + 30.0,
            self.FONT_MONO,
            9.5,
            self.oled_color(with_alpha(self.theme.foreground, 0.90 * fade)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        # 9. Hardware Chip / Sub-info below dial
        if extra_badge:
            self.draw_text(
                cr,
                extra_badge,
                cx,
                cy + radius + 18.0,
                self.FONT_MONO,
                8.5,
                self.oled_color(with_alpha(self.theme.muted, 0.80 * fade)),
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
        title: str,
        fade: float,
    ):
        """Draw an organic Bezier-curved telemetry graph with gradient illumination."""
        if not history or len(history) < 2:
            return

        # Title cleanly placed above oscilloscope
        self.draw_text(
            cr,
            title,
            x + w * 0.5,
            y - 10.0,
            self.FONT_MONO,
            9.5,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.85)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # Minimalist baseline (borderless, zero heavy box)
        base_y = y + h
        cr.new_path()
        cr.move_to(x, base_y)
        cr.line_to(x + w, base_y)
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.surface, 0.45 * fade)))
        cr.set_line_width(1.0)
        cr.stroke()

        points = list(history)
        n = len(points)
        dx = w / max(1, n - 1)
        safe_max = max(1.0, max_val)

        # Calculate coordinates
        coords = []
        for i, val in enumerate(points):
            norm = max(0.0, min(1.0, val / safe_max))
            px = x + i * dx
            py = base_y - norm * (h - 6.0)
            coords.append((px, py))

        # Fill gradient down to baseline
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

        # Live point pulse node
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

        top_y = cy - 280.0

        # 1. Floating Holographic Header
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
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        if not self.metrics:
            return

        m = self.metrics

        # 2. Main 2-Gauge Automotive Speedometer Cluster (Left: CPU, Right: RAM)
        gauge_offset_x = min(380.0, width * 0.28)
        gauge_y = top_y + 190.0
        gauge_radius = min(88.0, width * 0.082)

        # Left Instrument: CPU Speedometer / Tachometer
        cpu_sub = f"⚡ {m.cpu_freq_avg_ghz:.2f} GHz  🌡 {m.cpu_temp_c:.0f}°C"
        self._draw_minimal_speedometer_gauge(
            cr,
            cx - gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_cpu,
            self.peak_cpu,
            "CPU LOAD",
            "%",
            self.theme.accent,
            cpu_sub,
            m.cpu_model,
            fade,
        )

        # Right Instrument: Memory & Storage Cluster
        mem_sub = f"USED {m.mem_used_gib:.1f}/{m.mem_total_gib:.1f} GB"
        mem_badge = f"FREE {m.mem_avail_gib:.1f}G  ·  SWAP {m.swap_used_gib:.1f}G ({m.swap_percent:.0f}%)"
        self._draw_minimal_speedometer_gauge(
            cr,
            cx + gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_mem,
            self.peak_mem,
            "MEMORY",
            "%",
            (0.72, 0.45, 1.0, 1.0),
            mem_sub,
            mem_badge,
            fade,
        )

        # 3. Center Column: Live Bezier Sparkline + Integrated GPU Telemetry Strip
        chart_w = min(440.0, width * 0.34)
        chart_h = 80.0
        chart_x = cx - chart_w * 0.5
        chart_y = gauge_y - chart_h * 0.5 - 28.0

        # CPU Load History Bezier Wave
        self._draw_flowing_sparkline(
            cr,
            chart_x,
            chart_y,
            chart_w,
            chart_h,
            list(m.cpu_history),
            100.0,
            self.theme.accent,
            "CPU LOAD SPECTRUM",
            fade,
        )

        # Integrated GPU Telemetry HUD directly below Bezier graph
        gpu_y = chart_y + chart_h + 20.0
        gpu_str1 = (
            f"󰢮 GPU: {self.eased_gpu:04.1f}%   ·   "
            f"⚡ {m.gpu_clock_mhz:.0f} MHz   ·   "
            f"🌡 {m.gpu_temp_c:.0f}°C   ·   "
            f"🔥 {self.eased_gpu_power:.1f}W"
        )
        self.draw_text(
            cr,
            gpu_str1,
            cx,
            gpu_y,
            self.FONT_MONO,
            11.5,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade * 0.95)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # Mini horizontal GPU load indicator bar
        bar_w = min(320.0, width * 0.25)
        bar_h = 4.0
        bar_x = cx - bar_w * 0.5
        bar_y = gpu_y + 16.0

        # Bar background track
        cr.new_path()
        cr.arc(bar_x + 2, bar_y + 2, 2, math.pi * 0.5, math.pi * 1.5)
        cr.arc(bar_x + bar_w - 2, bar_y + 2, 2, -math.pi * 0.5, math.pi * 0.5)
        cr.close_path()
        cr.set_source_rgba(0.12, 0.15, 0.22, 0.45 * fade)
        cr.fill()

        # Bar active fill
        gpu_fill_w = max(4.0, bar_w * (self.eased_gpu / 100.0))
        cr.new_path()
        cr.arc(bar_x + 2, bar_y + 2, 2, math.pi * 0.5, math.pi * 1.5)
        cr.arc(bar_x + gpu_fill_w - 2, bar_y + 2, 2, -math.pi * 0.5, math.pi * 0.5)
        cr.close_path()
        bar_col = (1.0, 0.25, 0.35, 1.0) if self.eased_gpu >= 80.0 else self.theme.primary
        cr.set_source_rgba(*self.oled_color(with_alpha(bar_col, 0.92 * fade)))
        cr.fill()

        # GPU VRAM & GTT Memory Text
        vram_pct = (m.gpu_vram_used_mib / max(1.0, m.gpu_vram_total_mib)) * 100.0
        gpu_str2 = (
            f"VRAM {m.gpu_vram_used_mib:.0f}/{m.gpu_vram_total_mib:.0f} MB ({vram_pct:.0f}%)   ·   "
            f"GTT {m.gpu_gtt_used_gib:.1f} GB"
        )
        self.draw_text(
            cr,
            gpu_str2,
            cx,
            bar_y + 16.0,
            self.FONT_MONO,
            9.5,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.85)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        # 4. Multi-Channel Power Draw HUD Row
        power_y = gauge_y + gauge_radius + 56.0
        power_str = (
            f"⚡ CPU {self.eased_cpu_power:.1f}W   ·   "
            f"🔥 GPU {self.eased_gpu_power:.1f}W   ·   "
            f"🏎 SoC TOTAL {self.eased_soc_power:.1f}W   ·   "
            f"🔋 {m.power_source_str} [{m.battery_percent}%] {m.bat_power_w:.1f}W"
        )
        self.draw_text(
            cr,
            power_str,
            cx,
            power_y,
            self.FONT_MONO,
            12.0,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade * 0.92)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # 5. Bottom System Diagnostics Stream
        bottom_y = power_y + 44.0
        rx_fmt = (
            f"{m.net_rx_rate / (1024 * 1024):.1f} MB"
            if m.net_rx_rate >= 1024 * 1024
            else f"{m.net_rx_rate / 1024:.0f} KB"
        )
        tx_fmt = (
            f"{m.net_tx_rate / (1024 * 1024):.1f} MB"
            if m.net_tx_rate >= 1024 * 1024
            else f"{m.net_tx_rate / 1024:.0f} KB"
        )

        row1_text = (
            f"NVMe SSD: {m.nvme_temp_c:.1f}°C   ·   "
            f"STORAGE: {m.disk_used_gib:.1f}/{m.disk_total_gib:.1f} GB ({m.disk_percent:.0f}%)   ·   "
            f"NET ({m.primary_net_iface}): ↓ {rx_fmt}/s  ↑ {tx_fmt}/s"
        )
        self.draw_text(
            cr,
            row1_text,
            cx,
            bottom_y,
            self.FONT_MONO,
            11.5,
            self.oled_color(with_alpha(self.theme.foreground, fade * 0.85)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )

        row2_text = f"KERNEL: {m.kernel}   ·   UPTIME: {m.uptime_str}   ·   USER: {m.user}@{m.hostname}"
        self.draw_text(
            cr,
            row2_text,
            cx,
            bottom_y + 24.0,
            self.FONT_MONO,
            10.5,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.70)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )
