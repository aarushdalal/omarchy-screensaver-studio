"""Mode 2: Generative Particles.

Simulates a living digital atmosphere with floating ambient particles, proximity
connection lines via spatial grid partitioning, and gentle harmonic opacity breathing.
Optimized for low CPU utilization on integrated graphics.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class Particle:
    """Represents a single particle in digital space."""

    def __init__(self, x: float, y: float, vx: float, vy: float, radius: float, alpha: float, color_idx: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.base_alpha = alpha
        self.phase = random.uniform(0.0, math.pi * 2)
        self.color_idx = color_idx  # 0: primary, 1: accent, 2: secondary


class ParticlesMode(BaseMode):
    """Living digital atmosphere screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.particles: List[Particle] = []
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.is_battery = False
        self.target_fps = 45  # Locked, smooth 45 FPS for negligible CPU overhead
        self._init_particles()

    def _init_particles(self):
        random.seed(42 + self.monitor_index * 1337)
        # Moderate particle count for clean cyber aesthetic and optimal performance
        base_count = min(110, self.config.particles_count)
        if self.is_battery and self.config.battery_reduce_fps:
            base_count = int(base_count * self.config.particle_multiplier)

        speed_scale = self.config.particles_speed * 50.0

        self.particles = []
        for _ in range(base_count):
            angle = random.uniform(0.0, math.pi * 2)
            speed = random.uniform(0.3, 0.9) * speed_scale
            p = Particle(
                x=random.uniform(0.0, self.width),
                y=random.uniform(0.0, self.height),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                radius=random.uniform(1.2, 2.2) * (self.config.particles_size / 1.8),
                alpha=random.uniform(0.4, 0.85),
                color_idx=random.choices([0, 1, 2], weights=[0.60, 0.25, 0.15])[0],
            )
            self.particles.append(p)

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_particles()

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)

        # Check battery state change
        if metrics and self.config.battery_auto_detect:
            on_bat = not metrics.ac_online
            if on_bat != self.is_battery:
                self.is_battery = on_bat
                self.target_fps = self.config.battery_fps if on_bat else 45
                self._init_particles()

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.2)

        w, h = float(self.width), float(self.height)

        for p in self.particles:
            wander_angle = math.sin(self.time * 0.4 + p.phase) * 0.08
            ca = math.cos(wander_angle)
            sa = math.sin(wander_angle)
            vx = p.vx * ca - p.vy * sa
            vy = p.vx * sa + p.vy * ca

            p.x += vx * dt
            p.y += vy * dt

            # Wrap around boundaries
            margin = 15.0
            if p.x < -margin:
                p.x = w + margin
            elif p.x > w + margin:
                p.x = -margin

            if p.y < -margin:
                p.y = h + margin
            elif p.y > h + margin:
                p.y = -margin

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        if width != self.width or height != self.height:
            self.on_resize(width, height)

        self.clear_background(cr, width, height)

        conn_dist = min(90.0, float(self.config.particles_connection_distance))
        conn_dist_sq = conn_dist * conn_dist
        fade = self.fade_in

        # Spatial Grid Partitioning
        cell_size = conn_dist
        grid: Dict[Tuple[int, int], List[Particle]] = {}
        for p in self.particles:
            cx = int(p.x // cell_size)
            cy = int(p.y // cell_size)
            key = (cx, cy)
            if key not in grid:
                grid[key] = []
            grid[key].append(p)

        # 1. Collect Proximity Lines (Cap at 2 connections per particle for performance)
        cr.set_line_width(0.8)
        line_color_base = self.theme.primary

        conns_per_particle = {id(p): 0 for p in self.particles}

        for (cx, cy), cell_particles in grid.items():
            for i, p1 in enumerate(cell_particles):
                if conns_per_particle[id(p1)] >= 2:
                    continue

                # Same cell
                for j in range(i + 1, len(cell_particles)):
                    p2 = cell_particles[j]
                    if conns_per_particle[id(p2)] >= 2:
                        continue
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    d_sq = dx * dx + dy * dy
                    if d_sq < conn_dist_sq:
                        d = math.sqrt(d_sq)
                        alpha = (1.0 - d / conn_dist) ** 1.5 * 0.40 * fade
                        cr.set_source_rgba(*with_alpha(line_color_base, alpha))
                        cr.move_to(p1.x, p1.y)
                        cr.line_to(p2.x, p2.y)
                        cr.stroke()
                        conns_per_particle[id(p1)] += 1
                        conns_per_particle[id(p2)] += 1
                        if conns_per_particle[id(p1)] >= 2:
                            break

                # Neighboring cells
                if conns_per_particle[id(p1)] >= 2:
                    continue
                for ox, oy in [(1, 0), (-1, 1), (0, 1), (1, 1)]:
                    neighbor_key = (cx + ox, cy + oy)
                    if neighbor_key in grid:
                        for p2 in grid[neighbor_key]:
                            if conns_per_particle[id(p2)] >= 2:
                                continue
                            dx = p2.x - p1.x
                            dy = p2.y - p1.y
                            d_sq = dx * dx + dy * dy
                            if d_sq < conn_dist_sq:
                                d = math.sqrt(d_sq)
                                alpha = (1.0 - d / conn_dist) ** 1.5 * 0.40 * fade
                                cr.set_source_rgba(*with_alpha(line_color_base, alpha))
                                cr.move_to(p1.x, p1.y)
                                cr.line_to(p2.x, p2.y)
                                cr.stroke()
                                conns_per_particle[id(p1)] += 1
                                conns_per_particle[id(p2)] += 1
                                if conns_per_particle[id(p1)] >= 2:
                                    break
                    if conns_per_particle[id(p1)] >= 2:
                        break

        # 2. Render Particles (Batched by color index for speed)
        color_groups: Dict[int, List[Particle]] = {0: [], 1: [], 2: []}
        for p in self.particles:
            color_groups[p.color_idx].append(p)

        color_palettes = [self.theme.primary, self.theme.accent, self.theme.secondary]

        for color_idx, group in color_groups.items():
            if not group:
                continue
            base_col = color_palettes[color_idx]

            # Batch circles
            cr.set_source_rgba(*with_alpha(base_col, 0.75 * fade))
            cr.new_path()
            for p in group:
                pulse = 0.8 + 0.2 * math.sin(self.time * 1.5 + p.phase)
                r = p.radius * pulse
                cr.move_to(p.x + r, p.y)
                cr.arc(p.x, p.y, r, 0, math.pi * 2)
            cr.fill()
