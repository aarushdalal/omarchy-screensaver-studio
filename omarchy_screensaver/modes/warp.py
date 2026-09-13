"""Mode 8: Relativistic Starfield Warp.

Simulates 3D perspective relativistic hyperspace travel with motion-blurred
warp speed streaks, drifting vanishing point, and pure OLED black void.
"""

import math
import random
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class WarpStar:
    """Represents a 3D star in perspective space."""

    def __init__(self, x: float, y: float, z: float, color_idx: int):
        self.x = x
        self.y = y
        self.z = z
        self.prev_z = z
        self.color_idx = color_idx


class WarpMode(BaseMode):
    """Relativistic 3D Starfield Warp screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.target_fps = 60
        self.fade_in = 0.0

        self.max_z = 1000.0
        self.fov = 420.0
        self.stars: List[WarpStar] = []
        self.warp_speed = getattr(self.config, "warp_speed", 1.2) * 380.0
        self._init_stars()

    def _init_stars(self):
        random.seed(2026 + self.monitor_index * 99)
        count = getattr(self.config, "warp_star_count", 450)
        spread = 1200.0

        self.stars = []
        for _ in range(count):
            x = random.uniform(-spread, spread)
            y = random.uniform(-spread, spread)
            z = random.uniform(10.0, self.max_z)
            color_idx = random.choices([0, 1, 2], weights=[0.60, 0.25, 0.15])[0]
            self.stars.append(WarpStar(x, y, z, color_idx))

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        # Dynamic speed oscillation (pulsing warp drive)
        pulse = 1.0 + 0.25 * math.sin(self.time * 0.4)
        eff_speed = self.warp_speed * pulse

        spread = 1200.0
        for s in self.stars:
            s.prev_z = s.z
            s.z -= eff_speed * dt

            # Recycle star when it flies past camera
            if s.z <= 4.0:
                s.z = self.max_z
                s.prev_z = self.max_z
                s.x = random.uniform(-spread, spread)
                s.y = random.uniform(-spread, spread)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        if width != self.width or height != self.height:
            self.on_resize(width, height)

        # 100% OLED pitch black clear
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor

        # Wandering perspective vanishing point (simulates subtle ship pitch and yaw)
        vp_x = width * 0.5 + math.sin(self.time * 0.22) * 50.0 + self.burn_x + self.jitter_x
        vp_y = height * 0.5 + math.cos(self.time * 0.18) * 35.0 + self.burn_y + self.jitter_y

        streak_mult = getattr(self.config, "warp_streak_length", 1.0)
        color_palette = [
            self.theme.bright_foreground,  # Primary star white/cyan
            self.theme.accent,             # Hyperdrive neon accent
            self.theme.secondary,          # Deep space magenta/violet
        ]

        cr.set_line_cap(cairo.LINE_CAP_ROUND)

        for s in self.stars:
            if s.z <= 0:
                continue

            # Current perspective projection
            factor = self.fov / s.z
            px = vp_x + s.x * factor
            py = vp_y + s.y * factor

            # Previous frame perspective projection (motion blur trail)
            prev_factor = self.fov / max(1.0, s.prev_z * streak_mult)
            prev_px = vp_x + s.x * prev_factor
            prev_py = vp_y + s.y * prev_factor

            # Skip if outside viewport margins
            if px < -50 or px > width + 50 or py < -50 or py > height + 50:
                continue

            # Distance attenuation
            norm_depth = 1.0 - (s.z / self.max_z)
            alpha = (norm_depth ** 1.5) * fade
            line_w = max(0.8, (norm_depth ** 2.0) * 3.5)

            col = color_palette[s.color_idx]
            cr.set_source_rgba(*self.oled_color(with_alpha(col, alpha)))
            cr.set_line_width(line_w)

            # Draw warp streak line
            cr.move_to(prev_px, prev_py)
            cr.line_to(px, py)
            cr.stroke()

            # Star head node when close
            if norm_depth > 0.65:
                cr.arc(px, py, line_w * 0.65, 0, math.pi * 2)
                cr.set_source_rgba(*self.oled_color(with_alpha((1.0, 1.0, 1.0, 1.0), alpha)))
                cr.fill()
