"""Mode 6: Aurora / Ambient.

Renders serene, slowly undulating digital aurora light curtains with multi-stop
gradients and drifting ambient dust particles. Minimalist, dark, and hypnotic.
"""

import math
import random
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class DustParticle:
    def __init__(self, x: float, y: float, r: float, alpha: float, speed_y: float):
        self.x = x
        self.y = y
        self.r = r
        self.base_alpha = alpha
        self.speed_y = speed_y
        self.phase = random.uniform(0.0, math.pi * 2)


class AuroraMode(BaseMode):
    """Ambient digital aurora screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.dust: List[DustParticle] = []
        self.fade_in = 0.0
        self.target_fps = 20
        self._init_dust()

    def _init_dust(self):
        random.seed(99 + self.monitor_index * 777)
        self.dust = []
        for _ in range(self.config.aurora_dust_count):
            self.dust.append(
                DustParticle(
                    x=random.uniform(0.0, self.width),
                    y=random.uniform(0.0, self.height),
                    r=random.uniform(1.0, 2.2),
                    alpha=random.uniform(0.2, 0.6),
                    speed_y=random.uniform(3.0, 10.0),
                )
            )

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_dust()

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.2)

        w, h = float(self.width), float(self.height)
        for d in self.dust:
            d.y -= d.speed_y * dt
            d.x += math.sin(self.time * 0.4 + d.phase) * 6.0 * dt
            if d.y < -10.0:
                d.y = h + 10.0
                d.x = random.uniform(0.0, w)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        if width != self.width or height != self.height:
            self.on_resize(width, height)

        # Deepest dark background
        bg_dark = self.theme.background
        cr.set_source_rgba(*bg_dark)
        cr.paint()

        fade = self.fade_in
        t = self.time * self.config.aurora_speed
        w, h = float(width), float(height)

        # 1. Render Undulating Aurora Ribbons
        # Each ribbon is defined by a cubic spline curve
        wave_configs = [
            (self.theme.primary, 0.18, 0.7, 0.0, 0.40),
            (self.theme.secondary, 0.14, 0.9, 1.4, 0.50),
            (self.theme.accent, 0.12, 0.6, 2.8, 0.35),
            (self.theme.primary, 0.10, 0.8, 4.2, 0.60),
        ][: self.config.aurora_wave_count]

        for color, alpha, freq, phase, y_ratio in wave_configs:
            cr.new_path()
            base_y = h * y_ratio

            # Sample points along the width
            num_steps = 14
            step_w = w / (num_steps - 1)

            pts = []
            for i in range(num_steps):
                x = i * step_w
                norm_x = x / w
                # Harmonic wave displacement
                disp = (
                    math.sin(t * 1.2 + norm_x * freq * 4.0 + phase) * (h * 0.12)
                    + math.cos(t * 0.7 - norm_x * 2.5) * (h * 0.06)
                )
                y = base_y + disp
                pts.append((x, y))

            # Build smooth curve through points
            cr.move_to(0, h)
            cr.line_to(pts[0][0], pts[0][1])

            for i in range(len(pts) - 1):
                p0 = pts[i]
                p1 = pts[i + 1]
                mid_x = (p0[0] + p1[0]) * 0.5
                mid_y = (p0[1] + p1[1]) * 0.5
                cr.curve_to(p0[0], p0[1], mid_x, mid_y, p1[0], p1[1])

            cr.line_to(w, h)
            cr.close_path()

            # Vertical soft gradient
            grad = cairo.LinearGradient(0, base_y - h * 0.2, 0, base_y + h * 0.25)
            grad.add_color_stop_rgba(0.0, *with_alpha(color, 0.0))
            grad.add_color_stop_rgba(0.4, *with_alpha(color, alpha * fade))
            grad.add_color_stop_rgba(0.7, *with_alpha(color, alpha * 0.6 * fade))
            grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(grad)
            cr.fill()

        # 2. Render Ambient Dust Particles
        for d in self.dust:
            pulse = 0.7 + 0.3 * math.sin(self.time * 2.0 + d.phase)
            cur_alpha = d.base_alpha * pulse * fade
            cr.set_source_rgba(*with_alpha(self.theme.bright_foreground, cur_alpha))
            cr.arc(d.x, d.y, d.r, 0, math.pi * 2)
            cr.fill()

        # 3. Minimal Ambient Time Watermark in Bottom-Right Corner
        import time as pytime
        now = pytime.localtime()
        time_str = pytime.strftime("%H:%M", now)
        self.draw_text(
            cr, time_str, width - 48.0, height - 36.0,
            self.FONT_MONO, 14.0, with_alpha(self.theme.muted, 0.5 * fade),
            align="right"
        )
