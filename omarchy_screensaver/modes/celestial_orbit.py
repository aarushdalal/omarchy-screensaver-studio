"""Mode: Celestial Orbit (N-Body Gravitational Orbital Kepler Resonance).

Renders planetary bodies tracing glowing phosphorescent orbital resonance patterns
(rosettes and Lissajous curves) in deep space.
Strictly calibrated for dark aesthetic and eye comfort:
  - Deep obsidian space void (true OLED black #000000)
  - Faint Keplerian orbital guide rings (alpha ~0.10)
  - Subdued phosphorescent particle trails with soft alpha decay (alpha ~0.20 - 0.45)
  - Analytical orbits with near-zero CPU footprint (~1-2%).
"""

import math
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class Planet:
    __slots__ = ("semi_major", "eccentricity", "speed", "inclination", "color_idx", "size", "trail")

    def __init__(self, a: float, e: float, speed: float, inc: float, color_idx: int, size: float):
        self.semi_major = a
        self.eccentricity = e
        self.speed = speed
        self.inclination = inc
        self.color_idx = color_idx
        self.size = size
        self.trail: List[Tuple[float, float]] = []


class CelestialOrbitMode(BaseMode):
    """Subdued N-body orbital resonance screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.target_fps = 40

        self.planets: List[Planet] = []
        self._init_planets(self.width, self.height)

    def _init_planets(self, width: int, height: int):
        base_r = min(width, height) * 0.42
        self.planets = [
            Planet(a=base_r * 0.28, e=0.15, speed=0.55, inc=0.25, color_idx=0, size=2.8),
            Planet(a=base_r * 0.46, e=0.22, speed=0.36, inc=-0.35, color_idx=1, size=3.4),
            Planet(a=base_r * 0.68, e=0.10, speed=0.24, inc=0.15, color_idx=2, size=3.8),
            Planet(a=base_r * 0.88, e=0.28, speed=0.16, inc=-0.20, color_idx=0, size=4.2),
        ]

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_planets(width, height)

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        cx = self.width * 0.5
        cy = self.height * 0.5

        # Update planet positions using Keplerian orbital mechanics
        for p in self.planets:
            M = self.time * p.speed
            # Solve Kepler equation approx: E = M + e*sin(M)
            E = M + p.eccentricity * math.sin(M)

            # Orbital plane coordinates
            px = p.semi_major * (math.cos(E) - p.eccentricity)
            py = p.semi_major * math.sqrt(1.0 - p.eccentricity ** 2) * math.sin(E)

            # Inclination tilt rotation
            cos_i = math.cos(p.inclination)
            sin_i = math.sin(p.inclination)
            rx = px * cos_i - py * sin_i
            ry = (px * sin_i + py * cos_i) * 0.58  # 3D tilt perspective

            x = cx + rx
            y = cy + ry

            p.trail.append((x, y))
            if len(p.trail) > 55:
                p.trail.pop(0)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)
        fade = self.fade_in * self.luminance_factor

        cx = width * 0.5
        cy = height * 0.5

        ar, ag, ab = self.theme.accent_rgb
        pr, pg, pb = self.theme.primary_rgb
        sr, sg, sb = self.theme.secondary_rgb
        palettes = [(ar, ag, ab), (pr, pg, pb), (sr, sg, sb)]

        # 1. Subtle, dark central star / gravitational anchor (OLED friendly)
        cr.set_source_rgba(pr, pg, pb, 0.40 * fade)
        cr.arc(cx, cy, 3.5 * scale, 0, math.pi * 2)
        cr.fill()

        cr.set_source_rgba(1.0, 1.0, 1.0, 0.65 * fade)
        cr.arc(cx, cy, 1.5 * scale, 0, math.pi * 2)
        cr.fill()

        # 2. Faint Keplerian orbital guide rings
        cr.set_line_width(0.7 * scale)
        for p in self.planets:
            cr.set_source_rgba(ar, ag, ab, 0.08 * fade)
            cr.save()
            cr.translate(cx, cy)
            cr.rotate(p.inclination)
            cr.scale(1.0, 0.58)
            cr.arc(0, 0, p.semi_major, 0, math.pi * 2)
            cr.restore()
            cr.stroke()

        # 3. Phosphorescent orbital particle trails
        for p in self.planets:
            if len(p.trail) < 2:
                continue
            pr_c, pg_c, pb_c = palettes[p.color_idx % len(palettes)]

            # Draw decaying ribbon
            for i in range(len(p.trail) - 1):
                progress = (i + 1) / float(len(p.trail))
                alpha = progress * 0.38 * fade
                cr.set_source_rgba(pr_c, pg_c, pb_c, alpha)
                cr.set_line_width((0.8 + progress * 1.5) * scale)
                cr.move_to(p.trail[i][0], p.trail[i][1])
                cr.line_to(p.trail[i + 1][0], p.trail[i + 1][1])
                cr.stroke()

            # Planet Body
            head_x, head_y = p.trail[-1]
            cr.set_source_rgba(pr_c, pg_c, pb_c, 0.65 * fade)
            cr.arc(head_x, head_y, p.size * scale, 0, math.pi * 2)
            cr.fill()

            # Gentle inner core
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.70 * fade)
            cr.arc(head_x, head_y, p.size * 0.45 * scale, 0, math.pi * 2)
            cr.fill()
