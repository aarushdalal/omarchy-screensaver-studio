"""Mode: Synthwave (3D Perspective Infinite Wireframe Grid & Subdued Retro Sun).

Renders a classic 3D perspective grid moving towards a distant horizon.
Strictly calibrated for dark aesthetic and eye comfort:
  - Deep obsidian space void (true OLED black #000000)
  - Subdued, non-glaring retro segmented sun in deep amber/violet
  - Faint wireframe mountains along the horizon
  - Low-luminance perspective grid lines that dissolve into darkness
"""

import math
import random
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class Star:
    __slots__ = ("x", "y", "size", "alpha", "twinkle_speed")

    def __init__(self, x: float, y: float, size: float, alpha: float, twinkle_speed: float):
        self.x = x
        self.y = y
        self.size = size
        self.alpha = alpha
        self.twinkle_speed = twinkle_speed


class SynthwaveMode(BaseMode):
    """Subdued dark synthwave perspective screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.target_fps = 45

        self.grid_scroll = 0.0
        self.scroll_speed = 0.45
        self.stars: List[Star] = []
        self.mountains: List[Tuple[float, float]] = []

        self._init_environment(self.width, self.height)

    def _init_environment(self, width: int, height: int):
        random.seed(88 + self.monitor_index * 999)
        self.stars = []
        horizon_y = height * 0.54

        # Stars in upper sky
        for _ in range(70):
            self.stars.append(
                Star(
                    x=random.uniform(0, width),
                    y=random.uniform(0, horizon_y - 20),
                    size=random.uniform(0.8, 1.8),
                    alpha=random.uniform(0.15, 0.45),
                    twinkle_speed=random.uniform(1.2, 3.0),
                )
            )

        # Mountain silhouette vertices
        self.mountains = []
        pts = 24
        dx = width / (pts - 1)
        for i in range(pts):
            mx = i * dx
            # Mountain ridge elevation
            peak = math.sin(i * 0.7) * 35.0 + math.cos(i * 1.3) * 20.0
            my = horizon_y - 10.0 - abs(peak)
            self.mountains.append((mx, my))

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_environment(width, height)

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        self.grid_scroll = (self.grid_scroll + dt * self.scroll_speed) % 1.0

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)
        fade = self.fade_in * self.luminance_factor

        horizon_y = height * 0.54
        center_x = width * 0.5

        # 1. Subtle, dark distant stars
        for s in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(self.time * s.twinkle_speed + s.x)
            cr.set_source_rgba(1.0, 1.0, 1.0, s.alpha * twinkle * fade)
            cr.arc(s.x, s.y, s.size * scale, 0, math.pi * 2)
            cr.fill()

        # 2. Subdued Segmented Retro Sun (Warm dark amber / muted crimson gradient, NOT bright)
        sun_radius = min(width, height) * 0.16
        sun_y = horizon_y - sun_radius * 0.45

        # Sun gradient
        ar, ag, ab = self.theme.accent_rgb
        pr, pg, pb = self.theme.primary_rgb

        cr.save()
        # Clip to circle
        cr.arc(center_x, sun_y, sun_radius, 0, math.pi * 2)
        cr.clip()

        # Draw sun gradient
        grad = cairo.LinearGradient(center_x, sun_y - sun_radius, center_x, sun_y + sun_radius)
        # Deep amber/crimson top, muted violet/magenta bottom
        grad.add_color_stop_rgba(0.0, pr, pg, pb, 0.65 * fade)
        grad.add_color_stop_rgba(1.0, ar, ag, ab, 0.40 * fade)
        cr.set_source(grad)
        cr.paint()

        # Horizontal blinds blinds cutouts (widening towards horizon)
        cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        blind_count = 9
        for b in range(blind_count):
            rel_y = b / float(blind_count)
            blind_h = (1.5 + rel_y * 7.0) * scale
            by = sun_y + (rel_y * sun_radius * 1.1) - (sun_radius * 0.1)
            cr.rectangle(center_x - sun_radius - 10, by, (sun_radius + 10) * 2, blind_h)
            cr.fill()

        cr.restore()

        # 3. Mountain Silhouettes (Dark muted backdrop)
        mr, mg, mb = self.theme.muted_rgb
        cr.set_source_rgba(mr, mg, mb, 0.28 * fade)
        cr.set_line_width(1.2 * scale)
        if self.mountains:
            cr.move_to(0, horizon_y)
            for mx, my in self.mountains:
                cr.line_to(mx, my)
            cr.line_to(width, horizon_y)
            cr.close_path()
            cr.fill()

        # 4. Perspective Wireframe Grid (Deep dark grid lines)
        cr.set_line_width(1.0 * scale)

        # Perspective rays emanating from horizon
        num_rays = 22
        ray_spread = width * 1.4
        for r_idx in range(num_rays + 1):
            fraction = r_idx / float(num_rays)
            bottom_x = (center_x - ray_spread * 0.5) + fraction * ray_spread

            # Gradient line fading into darkness near horizon
            line_grad = cairo.LinearGradient(center_x, horizon_y, bottom_x, height)
            line_grad.add_color_stop_rgba(0.0, ar, ag, ab, 0.05 * fade)
            line_grad.add_color_stop_rgba(0.7, ar, ag, ab, 0.32 * fade)
            line_grad.add_color_stop_rgba(1.0, pr, pg, pb, 0.45 * fade)

            cr.set_source(line_grad)
            cr.move_to(center_x, horizon_y)
            cr.line_to(bottom_x, height)
            cr.stroke()

        # Horizontal perspective rungs (scrolling exponentially in depth)
        num_rungs = 18
        grid_height = height - horizon_y
        for r_idx in range(num_rungs):
            progress = (r_idx + self.grid_scroll) / float(num_rungs)
            # Quadratic exponential depth spacing
            depth_pos = progress ** 2.2
            ry = horizon_y + depth_pos * grid_height

            alpha = (0.05 + 0.38 * depth_pos) * fade
            cr.set_source_rgba(ar, ag, ab, alpha)
            cr.move_to(0, ry)
            cr.line_to(width, ry)
            cr.stroke()

        # 5. Horizon subtle dividing line
        cr.set_source_rgba(ar, ag, ab, 0.35 * fade)
        cr.set_line_width(1.2 * scale)
        cr.move_to(0, horizon_y)
        cr.line_to(width, horizon_y)
        cr.stroke()
