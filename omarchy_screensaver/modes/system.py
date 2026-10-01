"""Mode 4: Digital Cockpit Speedometer Telemetry Cluster.

Presents a high-performance sports car instrument cluster with precision sweeping
needles, radial hash tachometers, glowing redline zones, multi-channel power draw
telemetry (CPU, GPU, SoC, Battery), live Bezier telemetry sparklines, and complete
OLED burn-in defense.
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
    """Futuristic automotive digital cockpit instrument cluster screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.metrics: Optional[SystemMetrics] = None
        self.fade_in: float = 0.0
        self.target_fps: int = 30

        # Eased metric values for organic automotive needle motion
        self.eased_cpu: float = 0.0
        self.eased_gpu: float = 0.0
        self.eased_mem: float = 0.0
        self.eased_soc_power: float = 0.0
        self.eased_cpu_power: float = 0.0
        self.eased_gpu_power: float = 0.0

        # Peak hold indicators (with 3-second hold and slow decay)
        self.peak_cpu: float = 0.0
        self.peak_cpu_timer: float = 0.0
        self.peak_gpu: float = 0.0
        self.peak_gpu_timer: float = 0.0
        self.peak_mem: float = 0.0
        self.peak_mem_timer: float = 0.0

        # Micro needle engine vibration timer at high RPM
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

            if metrics.gpu_percent > self.peak_gpu:
                self.peak_gpu = metrics.gpu_percent
                self.peak_gpu_timer = 3.0
            else:
                self.peak_gpu_timer -= dt
                if self.peak_gpu_timer <= 0:
                    self.peak_gpu = max(self.eased_gpu, self.peak_gpu - dt * 18.0)

            if metrics.mem_percent > self.peak_mem:
                self.peak_mem = metrics.mem_percent
                self.peak_mem_timer = 3.0
            else:
                self.peak_mem_timer -= dt
                if self.peak_mem_timer <= 0:
                    self.peak_mem = max(self.eased_mem, self.peak_mem - dt * 12.0)

            self.vibe_phase += dt * 36.0

    def _draw_speedometer_gauge(
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
        is_hero: bool = False,
    ):
        """Render an automotive supercar speedometer / tachometer instrument dial."""
        start_ang = 0.75 * math.pi
        total_ang = 1.5 * math.pi

        # Subtle engine mechanical micro-vibration when engine load > 75%
        vibe = 0.0
        if percent > 75.0:
            vibe = (math.sin(self.vibe_phase) * 0.22) * ((percent - 75.0) / 25.0)
        norm = max(0.0, min(100.0, percent + vibe)) / 100.0
        cur_ang = start_ang + total_ang * norm

        # 1. Outer Metallic Bezel Ring & Dark Dial Face
        bezel_padding = 22.0 if is_hero else 18.0
        cr.new_path()
        cr.arc(cx, cy, radius + bezel_padding, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color((0.035, 0.05, 0.075, 0.95 * fade)))
        cr.fill()

        # Bezel rim accent
        cr.new_path()
        cr.arc(cx, cy, radius + bezel_padding, 0, 2 * math.pi)
        rim_color = (
            primary_color[0] * 0.35 + 0.15,
            primary_color[1] * 0.35 + 0.15,
            primary_color[2] * 0.35 + 0.15,
            0.45 * fade,
        )
        cr.set_source_rgba(*self.oled_color(rim_color))
        cr.set_line_width(2.0 if is_hero else 1.5)
        cr.stroke()

        # 2. Redline Zone Background Warning Glow (80% - 100%)
        redline_start = start_ang + total_ang * 0.8
        cr.new_path()
        cr.arc(cx, cy, radius, redline_start, start_ang + total_ang)
        cr.set_source_rgba(*self.oled_color((1.0, 0.14, 0.24, 0.22 * fade)))
        cr.set_line_width(14.0 if is_hero else 10.0)
        cr.stroke()

        # 3. Faint Background Track Arc
        cr.new_path()
        cr.arc(cx, cy, radius, start_ang, start_ang + total_ang)
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.surface, 0.45 * fade)))
        cr.set_line_width(4.0)
        cr.stroke()

        # 4. Speedometer Hash Ticks & Numerical Dial Markings
        num_steps = 10
        for i in range(num_steps + 1):
            frac = i / num_steps
            ang = start_ang + total_ang * frac
            is_redline = frac >= 0.8

            r_outer = radius - 2.0
            r_inner = r_outer - (12.0 if is_hero else 9.0)
            x1 = cx + math.cos(ang) * r_inner
            y1 = cy + math.sin(ang) * r_inner
            x2 = cx + math.cos(ang) * r_outer
            y2 = cy + math.sin(ang) * r_outer

            tick_color = (1.0, 0.22, 0.32) if is_redline else (0.85, 0.90, 0.98)
            cr.new_path()
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.set_source_rgba(*self.oled_color(with_alpha(tick_color, 0.92 * fade)))
            cr.set_line_width(2.2 if is_hero else 1.8)
            cr.stroke()

            # Number label (0, 10, 20, ..., 100)
            lbl_val = f"{i * 10}"
            r_text = radius - (24.0 if is_hero else 19.0)
            tx = cx + math.cos(ang) * r_text
            ty = cy + math.sin(ang) * r_text
            self.draw_text(
                cr,
                lbl_val,
                tx,
                ty - 5.0,
                self.FONT_MONO,
                9.0 if is_hero else 8.0,
                self.oled_color(with_alpha(tick_color, 0.82 * fade)),
                align="center",
                weight=Pango.Weight.BOLD,
            )

            # Intermediate minor ticks
            if i < num_steps:
                for m in (0.33, 0.67):
                    m_frac = (i + m) / num_steps
                    m_ang = start_ang + total_ang * m_frac
                    m_redline = m_frac >= 0.8
                    mx1 = cx + math.cos(m_ang) * (radius - (7.0 if is_hero else 5.5))
                    my1 = cy + math.sin(m_ang) * (radius - (7.0 if is_hero else 5.5))
                    mx2 = cx + math.cos(m_ang) * (radius - 2.0)
                    my2 = cy + math.sin(m_ang) * (radius - 2.0)

                    m_col = (1.0, 0.25, 0.35) if m_redline else (0.6, 0.7, 0.85)
                    cr.new_path()
                    cr.move_to(mx1, my1)
                    cr.line_to(mx2, my2)
                    cr.set_source_rgba(*self.oled_color(with_alpha(m_col, 0.42 * fade)))
                    cr.set_line_width(1.0)
                    cr.stroke()

        # 5. Active Dynamic Glowing Speed Arc
        if norm > 0.005:
            if norm >= 0.80:
                arc_col = (1.0, 0.22, 0.32, 1.0)
            elif norm >= 0.60:
                arc_col = (1.0, 0.65, 0.15, 1.0)
            else:
                arc_col = primary_color

            # Outer soft neon aura
            cr.new_path()
            cr.arc(cx, cy, radius, start_ang, cur_ang)
            cr.set_source_rgba(*self.oled_color(with_alpha(arc_col, 0.28 * fade)))
            cr.set_line_width(14.0 if is_hero else 10.0)
            cr.stroke()

            # Crisp luminous main ribbon
            cr.new_path()
            cr.arc(cx, cy, radius, start_ang, cur_ang)
            cr.set_source_rgba(*self.oled_color(with_alpha(arc_col, 0.95 * fade)))
            cr.set_line_width(4.5 if is_hero else 3.5)
            cr.stroke()

        # 6. Peak-Hold Indicator Pip
        if peak_percent > 1.0:
            peak_norm = max(0.0, min(100.0, peak_percent)) / 100.0
            peak_ang = start_ang + total_ang * peak_norm
            px1 = cx + math.cos(peak_ang) * (radius - 12.0)
            py1 = cy + math.sin(peak_ang) * (radius - 12.0)
            px2 = cx + math.cos(peak_ang) * (radius - 2.0)
            py2 = cy + math.sin(peak_ang) * (radius - 2.0)

            cr.new_path()
            cr.move_to(px1, py1)
            cr.line_to(px2, py2)
            cr.set_source_rgba(*self.oled_color((1.0, 0.95, 0.4, 0.95 * fade)))
            cr.set_line_width(2.5)
            cr.stroke()

        # 7. Precision Automotive Sweeping Needle
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(cur_ang)

        # Drop shadow beneath needle
        cr.new_path()
        cr.set_source_rgba(0, 0, 0, 0.45 * fade)
        cr.move_to(-16.0, 0)
        cr.line_to(0, -3.5)
        cr.line_to(radius - 10.0, -0.6)
        cr.line_to(radius - 10.0, 0.6)
        cr.line_to(0, 3.5)
        cr.close_path()
        cr.fill()

        # Needle body (tapered sports car needle with counter-balance tail)
        needle_col = (1.0, 0.22, 0.20) if norm >= 0.8 else (1.0, 0.45, 0.15)
        cr.new_path()
        cr.set_source_rgba(*self.oled_color(with_alpha(needle_col, 0.96 * fade)))
        cr.move_to(-14.0, 0)
        cr.line_to(0, -3.0)
        cr.line_to(radius - 8.0, -0.6)
        cr.line_to(radius - 8.0, 0.6)
        cr.line_to(0, 3.0)
        cr.close_path()
        cr.fill()

        # White core reflection line
        cr.new_path()
        cr.set_source_rgba(*self.oled_color((1.0, 1.0, 1.0, 0.90 * fade)))
        cr.set_line_width(1.0)
        cr.move_to(0, 0)
        cr.line_to(radius - 12.0, 0)
        cr.stroke()
        cr.restore()

        # 8. Metallic Needle Boss Hub Cap
        hub_r = 16.0 if is_hero else 13.0
        cr.new_path()
        cr.arc(cx, cy, hub_r, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color((0.07, 0.09, 0.12, 1.0 * fade)))
        cr.fill()

        cr.new_path()
        cr.arc(cx, cy, hub_r, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color((0.40, 0.48, 0.60, 0.85 * fade)))
        cr.set_line_width(2.0)
        cr.stroke()

        # Hub Center Jewel Pin
        cr.new_path()
        cr.arc(cx, cy, 5.0 if is_hero else 4.0, 0, 2 * math.pi)
        cr.set_source_rgba(*self.oled_color(with_alpha(needle_col, 0.95 * fade)))
        cr.fill()

        # 9. Center Digital Readouts
        # Instrument title
        self.draw_text(
            cr,
            label,
            cx,
            cy - (48.0 if is_hero else 40.0),
            self.FONT_MONO,
            11.0 if is_hero else 10.0,
            self.oled_color(with_alpha(primary_color, 0.95 * fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # Big Hero Digits
        val_str = f"{percent:04.1f}"
        val_size = 28.0 if is_hero else 23.0
        self.draw_text(
            cr,
            val_str,
            cx,
            cy + (22.0 if is_hero else 18.0),
            self.FONT_MONO,
            val_size,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # Unit tag
        self.draw_text(
            cr,
            unit,
            cx + (50.0 if is_hero else 40.0),
            cy + (28.0 if is_hero else 23.0),
            self.FONT_MONO,
            9.5,
            self.oled_color(with_alpha(self.theme.muted, 0.85 * fade)),
            align="left",
            weight=Pango.Weight.NORMAL,
        )

        # Primary sub-telemetry row (Clock, Temp, Power)
        self.draw_text(
            cr,
            sub_text,
            cx,
            cy + (54.0 if is_hero else 46.0),
            self.FONT_MONO,
            10.0 if is_hero else 9.0,
            self.oled_color(with_alpha(self.theme.foreground, 0.92 * fade)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # 10. Dedicated Hardware Badge Pill Outside Gauge Bezel
        if extra_badge:
            badge_y = cy + radius + bezel_padding + 16.0

            layout = PangoCairo.create_layout(cr)
            layout.set_text(extra_badge, -1)
            layout.set_font_description(Pango.FontDescription("JetBrainsMono Nerd Font 9.5"))
            _, log_rect = layout.get_pixel_extents()
            pw = log_rect.width + 20.0
            ph = log_rect.height + 6.0
            px = cx - pw * 0.5
            py = badge_y - 2.0

            cr.new_path()
            cr.arc(px + 4, py + 4, 4, math.pi, 1.5 * math.pi)
            cr.arc(px + pw - 4, py + 4, 4, 1.5 * math.pi, 2 * math.pi)
            cr.arc(px + pw - 4, py + ph - 4, 4, 0, 0.5 * math.pi)
            cr.arc(px + 4, py + ph - 4, 4, 0.5 * math.pi, math.pi)
            cr.close_path()
            cr.set_source_rgba(0.06, 0.09, 0.13, 0.7 * fade)
            cr.fill()

            self.draw_text(
                cr,
                extra_badge,
                cx,
                badge_y,
                self.FONT_MONO,
                9.5,
                self.oled_color(with_alpha(self.theme.accent, 0.9 * fade)),
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

        # Title cleanly placed above oscilloscope container
        self.draw_text(
            cr,
            title,
            x + w * 0.5,
            y - 14.0,
            self.FONT_MONO,
            9.5,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.85)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # Oscilloscope display container
        cr.new_path()
        cr.rectangle(x, y, w, h)
        cr.set_source_rgba(0.035, 0.05, 0.075, 0.75 * fade)
        cr.fill()
        cr.new_path()
        cr.rectangle(x, y, w, h)
        cr.set_source_rgba(0.14, 0.18, 0.25, 0.40 * fade)
        cr.set_line_width(1.0)
        cr.stroke()

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

        # Build smooth fill path
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

        top_y = cy - 315.0

        # 1. Floating Holographic Cockpit Header
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
            f"// SYSTEM TELEMETRY CLUSTER  —  {date_str}",
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

        # 2. Main 3-Gauge Automotive Instrument Cluster
        gauge_offset_x = min(440.0, width * 0.28)
        gauge_y = top_y + 245.0

        side_radius = min(125.0, width * 0.082)
        hero_radius = min(150.0, width * 0.098)

        # Left Instrument: CPU Tachometer
        cpu_sub = f"⚡ {m.cpu_freq_avg_ghz:.2f} GHz  🌡 {m.cpu_temp_c:.0f}°C  🔥 {self.eased_cpu_power:.1f}W"
        self._draw_speedometer_gauge(
            cr,
            cx - gauge_offset_x,
            gauge_y + 16.0,
            side_radius,
            self.eased_cpu,
            self.peak_cpu,
            "CPU TACHOMETER",
            "%",
            self.theme.accent,
            cpu_sub,
            m.cpu_model,
            fade,
            is_hero=False,
        )

        # Center Hero Instrument: GPU Speedometer
        gpu_sub = f"⚡ {m.gpu_clock_mhz:.0f} MHz  🌡 {m.gpu_temp_c:.0f}°C  🔥 {self.eased_gpu_power:.1f}W"
        gpu_badge = f"VRAM {m.gpu_vram_used_mib:.0f}/{m.gpu_vram_total_mib:.0f} MB  ·  GTT {m.gpu_gtt_used_gib:.1f} GB"
        self._draw_speedometer_gauge(
            cr,
            cx,
            gauge_y,
            hero_radius,
            self.eased_gpu,
            self.peak_gpu,
            "GPU SPEEDOMETER",
            "%",
            self.theme.primary,
            gpu_sub,
            gpu_badge,
            fade,
            is_hero=True,
        )

        # Right Instrument: Memory & Storage Cluster
        mem_sub = f"USED {m.mem_used_gib:.1f}/{m.mem_total_gib:.1f} GB  ·  FREE {m.mem_avail_gib:.1f}G"
        mem_badge = f"SWAP {m.swap_used_gib:.1f}/{m.swap_total_gib:.1f} GB ({m.swap_percent:.0f}%)"
        self._draw_speedometer_gauge(
            cr,
            cx + gauge_offset_x,
            gauge_y + 16.0,
            side_radius,
            self.eased_mem,
            self.peak_mem,
            "RAM CLUSTER",
            "%",
            (0.82, 0.48, 1.0, 1.0),
            mem_sub,
            mem_badge,
            fade,
            is_hero=False,
        )

        # 3. Mid Power Draw Telemetry Console (Multi-Channel Energy HUD)
        power_y = gauge_y + hero_radius + 68.0
        power_str = (
            f"⚡ CPU: {self.eased_cpu_power:.1f} W   ·   "
            f"🔥 GPU: {self.eased_gpu_power:.1f} W   ·   "
            f"🏎 SoC TOTAL: {self.eased_soc_power:.1f} W   ·   "
            f"🔋 {m.power_source_str} [{m.battery_percent}%]  DRAW: {m.bat_power_w:.1f} W"
        )
        self.draw_text(
            cr,
            power_str,
            cx,
            power_y,
            self.FONT_MONO,
            12.5,
            self.oled_color(with_alpha(self.theme.bright_foreground, fade * 0.95)),
            align="center",
            weight=Pango.Weight.BOLD,
        )

        # 4. Dual Live Bezier Telemetry Sparklines (Left: CPU History, Right: GPU History)
        chart_w = min(360.0, width * 0.22)
        chart_h = 65.0
        chart_y = power_y + 54.0

        # CPU History (Left)
        self._draw_flowing_sparkline(
            cr,
            cx - gauge_offset_x + side_radius - chart_w * 0.5,
            chart_y,
            chart_w,
            chart_h,
            list(m.cpu_history),
            100.0,
            self.theme.accent,
            "CPU LOAD HISTORY",
            fade,
        )

        # GPU History (Right)
        self._draw_flowing_sparkline(
            cr,
            cx + gauge_offset_x - side_radius - chart_w * 0.5,
            chart_y,
            chart_w,
            chart_h,
            list(m.gpu_history),
            100.0,
            self.theme.primary,
            "GPU LOAD HISTORY",
            fade,
        )

        # 5. Bottom System Diagnostics Stream
        bottom_y = chart_y + chart_h + 30.0
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
            bottom_y + 22.0,
            self.FONT_MONO,
            10.5,
            self.oled_color(with_alpha(self.theme.muted, fade * 0.70)),
            align="center",
            weight=Pango.Weight.NORMAL,
        )
