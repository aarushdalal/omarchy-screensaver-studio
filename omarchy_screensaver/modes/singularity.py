"""Mode 10: Gravitational Singularity & Relativistic Accretion Disk.

Simulates an astrophysical Kerr black hole with Einstein photon ring lensing,
relativistic Doppler-beamed accretion disk, orbiting plasma filaments, and
pitch-black OLED event horizon subpixel shutoff.
"""

import math
import random
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class PlasmaParticle:
    """Represents a matter filament parcel in the accretion disk."""

    def __init__(self, r: float, theta: float, size: float, color_idx: int):
        self.r = r                  # Orbital radius from singularity center
        self.theta = theta          # Current orbital angle in radians
        self.size = size
        self.color_idx = color_idx
        # Keplerian orbital velocity: v ~ 1 / sqrt(r)
        self.angular_velocity = 2.8 / math.sqrt(r * 0.015)


class SingularityMode(BaseMode):
    """Black hole gravitational lensing & accretion disk screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.fade_in = 0.0
        self.target_fps = 60

        self.particles: List[PlasmaParticle] = []
        self._init_disk()

    def _init_disk(self):
        random.seed(4242 + self.monitor_index * 13)
        count = getattr(self.config, "singularity_particle_count", 350)
        self.particles = []

        for _ in range(count):
            r = random.uniform(65.0, 320.0)
            theta = random.uniform(0.0, math.pi * 2)
            size = random.uniform(1.2, 2.8)
            color_idx = random.choices([0, 1, 2], weights=[0.55, 0.35, 0.10])[0]
            self.particles.append(PlasmaParticle(r, theta, size, color_idx))

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        speed_scale = getattr(self.config, "singularity_swirl_speed", 1.0)
        for p in self.particles:
            p.theta += p.angular_velocity * speed_scale * dt
            # Subtle radial drift (matter spiraling towards event horizon)
            p.r -= 2.0 * dt
            if p.r < 62.0:
                p.r = random.uniform(300.0, 340.0)
                p.theta = random.uniform(0.0, math.pi * 2)
                p.angular_velocity = 2.8 / math.sqrt(p.r * 0.015)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        # 100% OLED pitch black clear
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.5 + self.burn_y + self.jitter_y

        event_horizon_r = 52.0
        tilt_sin = getattr(self.config, "singularity_disk_tilt", 0.45)  # 3D inclination angle

        color_palette = [
            self.theme.accent,      # Hot plasma neon
            self.theme.primary,     # Accretion primary hue
            self.theme.secondary,   # Doppler red-shift hue
        ]

        # 1. Background Gravitational Lensing Halo (Light bent around event horizon)
        lensing_pat = cairo.RadialGradient(cx, cy, event_horizon_r * 0.9, cx, cy, event_horizon_r * 2.2)
        lensing_pat.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(self.theme.accent, 0.55 * fade)))
        lensing_pat.add_color_stop_rgba(0.4, *self.oled_color(with_alpha(self.theme.primary, 0.25 * fade)))
        lensing_pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(lensing_pat)
        cr.arc(cx, cy, event_horizon_r * 2.2, 0, math.pi * 2)
        cr.fill()

        # 2. Accretion Disk Particles (Split into back and front halves for gravitational lensing)
        # Particles behind the black hole (y < 0) are warped upward by gravitational lensing
        for p in self.particles:
            raw_x = p.r * math.cos(p.theta)
            raw_y = p.r * math.sin(p.theta)

            # Relativistic Doppler Beaming:
            # Approaching side (cos(theta) < 0) is blue-shifted & brighter
            # Receding side (cos(theta) > 0) is red-shifted & dimmer
            doppler = 0.5 + 0.5 * (-math.cos(p.theta))
            brightness = (0.35 + 0.85 * doppler) * fade

            # Apply 3D disk tilt
            proj_x = cx + raw_x
            proj_y = cy + raw_y * tilt_sin

            # Gravitational Lensing Distortion:
            # Matter behind the singularity wraps over the top and bottom
            if raw_y < 0 and abs(raw_x) < event_horizon_r * 2.5:
                # Lens curvature upward
                lens_dist = math.sqrt(raw_x * raw_x + raw_y * raw_y)
                proj_y -= (event_horizon_r * 1.4) * (1.0 - min(1.0, lens_dist / (event_horizon_r * 3.0)))

            # Particle radius with Doppler scaling
            p_r = p.size * (0.8 + 0.4 * doppler)

            # Color selection with relativistic Doppler shift
            col = color_palette[0 if doppler > 0.6 else (1 if doppler > 0.3 else 2)]

            # Core particle
            cr.set_source_rgba(*self.oled_color(with_alpha(col, brightness)))
            cr.arc(proj_x, proj_y, p_r, 0, math.pi * 2)
            cr.fill()

            # Luminous plasma wake tail
            wake_dx = math.sin(p.theta) * p_r * 2.2
            wake_dy = -math.cos(p.theta) * p_r * 2.2 * tilt_sin
            cr.set_source_rgba(*self.oled_color(with_alpha(col, brightness * 0.35)))
            cr.set_line_width(p_r * 0.9)
            cr.move_to(proj_x, proj_y)
            cr.line_to(proj_x + wake_dx, proj_y + wake_dy)
            cr.stroke()

        # 3. Einstein Photon Sphere Ring (Sharp razor-edge relativistic photon orbit)
        cr.arc(cx, cy, event_horizon_r * 1.12, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha((1.0, 1.0, 1.0, 1.0), 0.85 * fade)))
        cr.set_line_width(2.2)
        cr.stroke()

        # Secondary outer diffraction ring
        cr.arc(cx, cy, event_horizon_r * 1.28, 0, math.pi * 2)
        cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.accent, 0.40 * fade)))
        cr.set_line_width(1.2)
        cr.stroke()

        # 4. Central Event Horizon (Absolute 100% pitch black void, 0 nits, subpixels OFF)
        cr.arc(cx, cy, event_horizon_r, 0, math.pi * 2)
        cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        cr.fill()
