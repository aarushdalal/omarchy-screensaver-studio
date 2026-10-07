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
        self.eased_cpu_volt: float = 0.88
        self.eased_cpu_current: float = 5.0
        self.eased_gpu_volt: float = 0.90
        self.eased_gpu_current: float = 2.0
        self.eased_soc_volt: float = 0.83
        self.eased_soc_current: float = 8.0
        self.eased_bat_volt: float = 12.0
        self.eased_bat_current: float = 0.0

        # Cached clock strings to eliminate redundant per-frame strftime allocations
        self._cached_sec: int = -1
        self._cached_time_str: str = ""
        self._cached_date_str: str = ""

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
            self.eased_cpu_volt += (metrics.cpu_volt_v - self.eased_cpu_volt) * min(1.0, dt * 4.5)
            self.eased_cpu_current += (metrics.cpu_current_a - self.eased_cpu_current) * min(1.0, dt * 4.5)
            self.eased_gpu_volt += (metrics.gpu_volt_v - self.eased_gpu_volt) * min(1.0, dt * 4.5)
            self.eased_gpu_current += (metrics.gpu_current_a - self.eased_gpu_current) * min(1.0, dt * 4.5)
            self.eased_soc_volt += (metrics.soc_volt_v - self.eased_soc_volt) * min(1.0, dt * 4.5)
            self.eased_soc_current += (metrics.soc_current_a - self.eased_soc_current) * min(1.0, dt * 4.5)
            self.eased_bat_volt += (metrics.bat_volt_v - self.eased_bat_volt) * min(1.0, dt * 4.5)
            self.eased_bat_current += (metrics.bat_current_a - self.eased_bat_current) * min(1.0, dt * 4.5)

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
    ):
        """Render a relaxing, borderless speedometer tachometer strictly in theme colors."""
        start_angle = 0.75 * math.pi
        total_angle = 1.5 * math.pi
        norm = max(0.0, min(100.0, percent)) / 100.0
        active_end = start_angle + total_angle * norm

        # 1. Subtle inner dial accent ring (minimalist instrument depth)
        inner_r = radius * 0.74
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(self.theme.track_arc_color(fade * 0.45)))
        cr.set_line_width(1.0)
        cr.arc(cx, cy, inner_r, start_angle, start_angle + total_angle)
        cr.stroke()

        # 2. Main background track arc
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(self.theme.track_arc_color(fade)))
        cr.set_line_width(4.5)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(cx, cy, radius, start_angle, start_angle + total_angle)
        cr.stroke()

        # 3. Clean, calm radial tick marks (10 automotive tachometer divisions, batched)
        num_ticks = 10
        inactive_tick_col = self.theme.track_tick_inactive_color(fade)
        active_tick_col = with_alpha(gauge_color, 0.88 * fade)

        inactive_ticks = []
        active_ticks = []
        for i in range(num_ticks + 1):
            frac = i / num_ticks
            ang = start_angle + total_angle * frac

            r_out = radius + 2.5
            r_in = r_out - 6.5
            x1 = cx + math.cos(ang) * r_in
            y1 = cy + math.sin(ang) * r_in
            x2 = cx + math.cos(ang) * r_out
            y2 = cy + math.sin(ang) * r_out
            if frac <= norm:
                active_ticks.append((x1, y1, x2, y2))
            else:
                inactive_ticks.append((x1, y1, x2, y2))

        cr.set_line_width(1.5)
        if inactive_ticks:
            cr.new_path()
            for x1, y1, x2, y2 in inactive_ticks:
                cr.move_to(x1, y1)
                cr.line_to(x2, y2)
            cr.set_source_rgba(*self.oled_color(inactive_tick_col))
            cr.stroke()

        if active_ticks:
            cr.new_path()
            for x1, y1, x2, y2 in active_ticks:
                cr.move_to(x1, y1)
                cr.line_to(x2, y2)
            cr.set_source_rgba(*self.oled_color(active_tick_col))
            cr.stroke()

        # 4. Active glowing speed arc
        if norm > 0.005:
            # Soft aura glow pass
            cr.new_path()
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.22 * fade)))
            cr.set_line_width(11.0)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Crisp main arc ribbon
            cr.new_path()
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.95 * fade)))
            cr.set_line_width(4.0)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.arc(cx, cy, radius, start_angle, active_end)
            cr.stroke()

            # Glowing tip node with soft halo
            tip_x = cx + math.cos(active_end) * radius
            tip_y = cy + math.sin(active_end) * radius
            cr.new_path()
            cr.arc(tip_x, tip_y, 4.5, 0, 2 * math.pi)
            cr.set_source_rgba(*self.oled_color(with_alpha(gauge_color, 0.40 * fade)))
            cr.fill()
            cr.new_path()
            cr.arc(tip_x, tip_y, 2.6, 0, 2 * math.pi)
            cr.set_source_rgba(*self.oled_color(self.theme.text_primary_color(fade)))
            cr.fill()

        # 5. Center typography with calm, spacious breathing room
        self.draw_text(
            cr,
            label,
            cx,
            cy - 27.0,
            self.FONT_MONO,
            10.5,
            self.oled_color(self.theme.text_muted_color(fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            value_str,
            cx,
            cy + 4.0,
            self.FONT_MONO,
            24.0,
            self.oled_color(self.theme.text_primary_color(fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        if sub_str:
            self.draw_text(
                cr,
                sub_str,
                cx,
                cy + 31.0,
                self.FONT_MONO,
                10.5,
                self.oled_color(with_alpha(gauge_color, fade * 0.95)),
                align="center",
                weight=Pango.Weight.NORMAL,
            )

        # 6. Bottom sub-badge under gauge (calm, spacious, borderless)
        if bottom_badge:
            self.draw_text(
                cr,
                bottom_badge,
                cx,
                cy + radius + 22.0,
                self.FONT_MONO,
                9.0,
                self.oled_color(self.theme.text_muted_color(fade * 0.85)),
                align="center",
                weight=Pango.Weight.NORMAL,
            )

    def _draw_dual_sparkline(
        self,
        cr: cairo.Context,
        x: float,
        y: float,
        w: float,
        h: float,
        cpu_history: List[float],
        gpu_history: List[float],
        max_val: float,
        cpu_color: Tuple[float, float, float, float],
        gpu_color: Tuple[float, float, float, float],
        fade: float,
    ):
        """Draw dual flowing Bezier telemetry graphs for CPU and GPU with subtle time grid."""
        max_history = 60

        def _prepare_points(hist: List[float]) -> List[float]:
            hl = list(hist) if hist else [0.0]
            if len(hl) < max_history:
                init_val = hl[0] if hl else 0.0
                return [init_val] * (max_history - len(hl)) + hl
            return hl[-max_history:]

        cpu_pts = _prepare_points(cpu_history)
        gpu_pts = _prepare_points(gpu_history)

        base_y = y + h
        safe_max = max(1.0, max_val)

        # 1. Subtle, minimalist reference grid (50% dashed line and solid baseline)
        # Baseline
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(self.theme.track_arc_color(fade * 0.50)))
        cr.set_line_width(1.0)
        cr.move_to(x, base_y)
        cr.line_to(x + w, base_y)
        cr.stroke()

        # Midline (50% utilization guide)
        mid_y = y + h * 0.5
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(self.theme.track_arc_color(fade * 0.22)))
        cr.set_line_width(0.8)
        cr.set_dash([4.0, 6.0])
        cr.move_to(x, mid_y)
        cr.line_to(x + w, mid_y)
        cr.stroke()
        cr.set_dash([])  # reset dash pattern

        # Subtle vertical division tick marks on baseline (batched)
        cr.new_path()
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            tx = x + w * frac
            cr.move_to(tx, base_y)
            cr.line_to(tx, base_y + 4.0)
        cr.set_source_rgba(*self.oled_color(self.theme.track_arc_color(fade * 0.35)))
        cr.set_line_width(1.0)
        cr.stroke()

        # Subtle timeline labels
        self.draw_text(
            cr,
            "-60s",
            x,
            base_y + 11.0,
            self.FONT_MONO,
            8.0,
            self.oled_color(self.theme.text_muted_color(fade * 0.65)),
            align="left",
        )
        self.draw_text(
            cr,
            "NOW",
            x + w,
            base_y + 11.0,
            self.FONT_MONO,
            8.0,
            self.oled_color(self.theme.text_muted_color(fade * 0.65)),
            align="right",
        )

        def _calc_coords(pts: List[float]) -> List[Tuple[float, float]]:
            n = len(pts)
            dx = w / max(1, n - 1)
            coords = []
            for i, val in enumerate(pts):
                norm = max(0.0, min(1.0, val / safe_max))
                px = x + i * dx
                py = base_y - norm * (h - 6.0)
                coords.append((px, py))
            return coords

        gpu_coords = _calc_coords(gpu_pts)
        cpu_coords = _calc_coords(cpu_pts)

        # 2. Draw GPU Activity Curve (first pass)
        fill_grad_gpu = cairo.LinearGradient(x, y, x, base_y)
        gpu_fill_a = 0.14 if getattr(self.theme, "is_dark", True) else 0.12
        fill_grad_gpu.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(gpu_color, gpu_fill_a * fade)))
        fill_grad_gpu.add_color_stop_rgba(1.0, *self.oled_color(with_alpha(gpu_color, 0.0)))

        cr.new_path()
        cr.move_to(x, base_y)
        cr.line_to(gpu_coords[0][0], gpu_coords[0][1])
        for i in range(len(gpu_coords) - 1):
            p0 = gpu_coords[i]
            p1 = gpu_coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])
        cr.line_to(x + w, base_y)
        cr.close_path()
        cr.set_source(fill_grad_gpu)
        cr.fill()

        # Stroke GPU glowing curve
        cr.new_path()
        cr.move_to(gpu_coords[0][0], gpu_coords[0][1])
        for i in range(len(gpu_coords) - 1):
            p0 = gpu_coords[i]
            p1 = gpu_coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])
        cr.set_source_rgba(*self.oled_color(with_alpha(gpu_color, 0.85 * fade)))
        cr.set_line_width(1.8)
        cr.stroke()

        # GPU live node
        last_gpu = gpu_coords[-1]
        cr.new_path()
        cr.arc(last_gpu[0], last_gpu[1], 4.5, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha(gpu_color, 0.35 * fade)))
        cr.fill()
        cr.new_path()
        cr.arc(last_gpu[0], last_gpu[1], 2.4, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha(gpu_color, 0.95 * fade)))
        cr.fill()

        # 3. Draw CPU Activity Curve (second pass, harmonic overlay)
        fill_grad_cpu = cairo.LinearGradient(x, y, x, base_y)
        cpu_fill_a = 0.18 if getattr(self.theme, "is_dark", True) else 0.15
        fill_grad_cpu.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(cpu_color, cpu_fill_a * fade)))
        fill_grad_cpu.add_color_stop_rgba(1.0, *self.oled_color(with_alpha(cpu_color, 0.0)))

        cr.new_path()
        cr.move_to(x, base_y)
        cr.line_to(cpu_coords[0][0], cpu_coords[0][1])
        for i in range(len(cpu_coords) - 1):
            p0 = cpu_coords[i]
            p1 = cpu_coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])
        cr.line_to(x + w, base_y)
        cr.close_path()
        cr.set_source(fill_grad_cpu)
        cr.fill()

        # Stroke CPU glowing curve
        cr.new_path()
        cr.move_to(cpu_coords[0][0], cpu_coords[0][1])
        for i in range(len(cpu_coords) - 1):
            p0 = cpu_coords[i]
            p1 = cpu_coords[i + 1]
            cx_mid = (p0[0] + p1[0]) * 0.5
            cr.curve_to(cx_mid, p0[1], cx_mid, p1[1], p1[0], p1[1])
        cr.set_source_rgba(*self.oled_color(with_alpha(cpu_color, 0.95 * fade)))
        cr.set_line_width(2.0)
        cr.stroke()

        # CPU live node
        last_cpu = cpu_coords[-1]
        cr.new_path()
        cr.arc(last_cpu[0], last_cpu[1], 5.0, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha(cpu_color, 0.40 * fade)))
        cr.fill()
        cr.new_path()
        cr.arc(last_cpu[0], last_cpu[1], 2.6, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(self.theme.text_primary_color(fade)))
        cr.fill()

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.5 + self.burn_y + self.jitter_y - 10.0

        # Normal, prominent sizing. GTK4 handles display DPI; do not downscale on normal desktop resolutions.
        # Only gently scale on sub-720p screens or up-scale on 4K.
        if height < 700.0 or width < 1200.0:
            ui_scale = max(0.75, min(1.0, min(width / 1280.0, height / 720.0)))
        elif width >= 2560.0 and height >= 1440.0:
            ui_scale = min(1.5, min(width / 1920.0, height / 1080.0))
        else:
            ui_scale = 1.0

        sec_now = int(time.time())
        if sec_now != self._cached_sec:
            self._cached_sec = sec_now
            now = time.localtime(sec_now)
            self._cached_time_str = time.strftime("%H:%M:%S" if self.config.clock_format_24h else "%I:%M:%S %p", now)
            self._cached_date_str = time.strftime("%A · %d %B %Y", now).upper()
        time_str = self._cached_time_str
        date_str = self._cached_date_str

        top_y = cy - 252.0 * ui_scale

        # Floating holographic header
        self.draw_text(
            cr,
            time_str,
            cx,
            top_y,
            self.FONT_MONO,
            48.0 * ui_scale,
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
            11.0 * ui_scale,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        if not self.metrics:
            return

        m = self.metrics

        # 1. Tri-Gauge Instrument Cluster (CPU, GPU, RAM) with Speedometer Tachometer Styling
        gauge_radius = min(88.0 * ui_scale, width * 0.088)
        gauge_offset_x = min(380.0 * ui_scale, width * 0.28)
        gauge_y = top_y + 195.0 * ui_scale

        # Unified theme palette: all instrument dials share the active theme's signature accent
        gauge_color = self.theme.accent

        # Left: CPU Speedometer Gauge
        cpu_sub = (
            f"{m.cpu_freq_avg_ghz:4.2f} GHz · {m.cpu_temp_c:2.0f}°C"
            if m.cpu_temp_c > 0
            else f"{m.cpu_freq_avg_ghz:4.2f} GHz"
        )
        cpu_short = m.cpu_model.replace(" with Radeon Graphics", "").strip()
        cpu_badge = f"{cpu_short}  ·  {self.eased_cpu_volt:4.2f}V · {self.eased_cpu_current:4.1f}A"
        self._draw_speedometer_gauge(
            cr,
            cx - gauge_offset_x,
            gauge_y,
            gauge_radius,
            self.eased_cpu,
            "CPU LOAD",
            f"{self.eased_cpu:5.1f}%",
            cpu_sub,
            cpu_badge,
            gauge_color,
            fade,
        )

        # Center: GPU Speedometer Gauge
        gpu_sub = (
            f"{m.gpu_clock_mhz:4.0f} MHz · {m.gpu_temp_c:2.0f}°C"
            if m.gpu_temp_c > 0
            else f"{m.gpu_clock_mhz:4.0f} MHz"
        )
        gpu_badge = f"VRAM {m.gpu_vram_used_mib:3.0f}/{m.gpu_vram_total_mib:3.0f} MB  ·  {self.eased_gpu_volt:4.2f}V · {self.eased_gpu_current:4.1f}A"
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
            gauge_color,
            fade,
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
            gauge_color,
            fade,
        )

        # 2. Central Live Dual-Trace Bezier Telemetry Sparkline (Theme-Synchronized)
        # Width matches exactly the distance from left dial center to right dial center
        chart_w = gauge_offset_x * 2.0
        chart_h = 74.0 * ui_scale
        chart_x = cx - chart_w * 0.5
        chart_y = gauge_y + gauge_radius + 85.0 * ui_scale

        # Sparkline colors strictly from active theme palette
        cpu_curve_color = self.theme.accent
        gpu_curve_color = (
            self.theme.dark_foreground
            if getattr(self.theme, "is_dark", True)
            else self.theme.foreground
        )

        # Sparkline Header with distinct CPU and GPU legends in theme palette
        self.draw_text(
            cr,
            "SYSTEM ACTIVITY (60s)",
            chart_x,
            chart_y - 14.0 * ui_scale,
            self.FONT_MONO,
            9.5 * ui_scale,
            self.oled_color(self.theme.text_muted_color(fade * 0.85)),
            align="left",
            weight=Pango.Weight.BOLD,
        )
        # GPU legend (right aligned, in harmonic theme foreground)
        gpu_leg_w, _ = self.draw_text(
            cr,
            f"GPU {self.eased_gpu:4.1f}%",
            chart_x + chart_w,
            chart_y - 14.0 * ui_scale,
            self.FONT_MONO,
            9.5 * ui_scale,
            self.oled_color(with_alpha(gpu_curve_color, fade * 0.95)),
            align="right",
            weight=Pango.Weight.BOLD,
        )
        # CPU legend (to the left of GPU legend, in theme accent)
        self.draw_text(
            cr,
            f"CPU {self.eased_cpu:4.1f}%   ·   ",
            chart_x + chart_w - gpu_leg_w,
            chart_y - 14.0 * ui_scale,
            self.FONT_MONO,
            9.5 * ui_scale,
            self.oled_color(with_alpha(cpu_curve_color, fade * 0.95)),
            align="right",
            weight=Pango.Weight.BOLD,
        )

        self._draw_dual_sparkline(
            cr,
            chart_x,
            chart_y,
            chart_w,
            chart_h,
            list(m.cpu_history),
            list(m.gpu_history),
            100.0,
            cpu_curve_color,
            gpu_curve_color,
            fade,
        )

        # 3. Dedicated 3-Column Telemetry Bay (Spacious, Uncluttered, Relaxing)
        # Vertically aligned with each instrument dial above for intuitive glanceability
        telem_y = chart_y + chart_h + 56.0 * ui_scale
        col_left_x = cx - gauge_offset_x
        col_mid_x = cx
        col_right_x = cx + gauge_offset_x

        # Formats for network throughput
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

        # Column 1: Electrical & Power (Aligned under CPU Dial)
        self.draw_text(
            cr,
            "●  ELECTRICAL & POWER",
            col_left_x,
            telem_y,
            self.FONT_MONO,
            10.0 * ui_scale,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            f"CPU RAIL   {self.eased_cpu_power:4.1f}W · {self.eased_cpu_volt:4.2f}V · {self.eased_cpu_current:4.1f}A",
            col_left_x,
            telem_y + 24.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade)),
            align="center",
        )
        self.draw_text(
            cr,
            f"GPU RAIL   {self.eased_gpu_power:4.1f}W · {self.eased_gpu_volt:4.2f}V · {self.eased_gpu_current:4.1f}A",
            col_left_x,
            telem_y + 47.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade * 0.90)),
            align="center",
        )
        if m.has_battery:
            bat_sub = f"BATTERY    {m.battery_percent}% · {self.eased_bat_volt:4.1f}V · {self.eased_bat_current:4.1f}A [{m.battery_status.upper()}]"
        else:
            bat_sub = f"TOTAL SoC  {self.eased_soc_power:4.1f}W · {self.eased_soc_volt:4.2f}V · {self.eased_soc_current:4.1f}A"
        self.draw_text(
            cr,
            bat_sub,
            col_left_x,
            telem_y + 70.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade * 0.85)),
            align="center",
        )

        # Column 2: Storage & I/O Mesh (Aligned under GPU Dial)
        self.draw_text(
            cr,
            "●  STORAGE & I/O MESH",
            col_mid_x,
            telem_y,
            self.FONT_MONO,
            10.0 * ui_scale,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        disk_sub = (
            f"SSD NVMe   {m.disk_used_gib:3.0f}/{m.disk_total_gib:3.0f} GB · {m.nvme_temp_c:2.0f}°C"
            if m.nvme_temp_c > 0
            else f"SSD NVMe   {m.disk_used_gib:3.0f}/{m.disk_total_gib:3.0f} GB"
        )
        self.draw_text(
            cr,
            disk_sub,
            col_mid_x,
            telem_y + 24.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade)),
            align="center",
        )
        net_sub = f"NETWORK    ↓ {rx_fmt}/s  ↑ {tx_fmt}/s"
        self.draw_text(
            cr,
            net_sub,
            col_mid_x,
            telem_y + 47.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade * 0.90)),
            align="center",
        )
        mem_bus_sub = f"MEM BUS    {m.mem_used_gib:3.1f}G ACT · {m.mem_avail_gib:3.1f}G FREE"
        self.draw_text(
            cr,
            mem_bus_sub,
            col_mid_x,
            telem_y + 70.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade * 0.85)),
            align="center",
        )

        # Column 3: Kernel & System Runtime (Aligned under Memory Dial)
        self.draw_text(
            cr,
            "●  KERNEL & RUNTIME",
            col_right_x,
            telem_y,
            self.FONT_MONO,
            10.0 * ui_scale,
            self.oled_color(with_alpha(self.theme.accent, fade * 0.90)),
            align="center",
            weight=Pango.Weight.BOLD,
        )
        self.draw_text(
            cr,
            f"KERNEL     {m.kernel} · {m.user}",
            col_right_x,
            telem_y + 24.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade)),
            align="center",
        )
        self.draw_text(
            cr,
            f"LOAD AVG   {m.load_avg} ({m.cpu_cores}C)",
            col_right_x,
            telem_y + 47.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade * 0.90)),
            align="center",
        )
        gov_short = m.cpu_governor.split()[0]
        self.draw_text(
            cr,
            f"GOVERNOR   {gov_short} · UP {m.uptime_str}",
            col_right_x,
            telem_y + 70.0 * ui_scale,
            self.FONT_MONO,
            10.5 * ui_scale,
            self.oled_color(self.theme.text_secondary_color(fade * 0.85)),
            align="center",
        )
