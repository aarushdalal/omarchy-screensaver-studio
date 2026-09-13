"""Mode 2: Deep Volumetric Generative Particles.

Simulates a living cosmic atmosphere with 3D parallax layers, proximity
filaments via spatial grid partitioning, wandering gravitational singularity vortex,
and pure OLED true black background.
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
    """Represents a particle in 3D-projected space."""

    def __init__(self, x: float, y: float, vx: float, vy: float, depth: float, color_idx: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.depth = depth  # 0.2 (deep distant) to 1.0 (foreground)
        self.base_radius = (0.8 + 1.6 * depth)
        self.base_alpha = (0.25 + 0.65 * depth)
        self.phase = random.uniform(0.0, math.pi * 2)
        self.color_idx = color_idx  # 0: primary, 1: accent, 2: secondary


class ParticlesMode(BaseMode):
    """Deep volumetric cosmic atmosphere screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.particles: List[Particle] = []
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.is_battery = False
        self.target_fps = 50
        self._init_particles()

    def _init_particles(self):
        random.seed(42 + self.monitor_index * 1337)
        base_count = min(140, self.config.particles_count)
        if self.is_battery and self.config.battery_reduce_fps:
            base_count = int(base_count * self.config.particle_multiplier)

        speed_scale = self.config.particles_speed * 45.0

        self.particles = []
        for _ in range(base_count):
            depth = random.uniform(0.2, 1.0)
            angle = random.uniform(0.0, math.pi * 2)
            speed = random.uniform(0.2, 0.8) * speed_scale * (0.4 + 0.6 * depth)
            p = Particle(
                x=random.uniform(0.0, self.width),
                y=random.uniform(0.0, self.height),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                depth=depth,
                color_idx=random.choices([0, 1, 2], weights=[0.55, 0.30, 0.15])[0],
            )
            self.particles.append(p)

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_particles()

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)

        if metrics and self.config.battery_auto_detect:
            on_bat = not metrics.ac_online
            if on_bat != self.is_battery:
                self.is_battery = on_bat
                self.target_fps = self.config.battery_fps if on_bat else 50
                self._init_particles()

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.2)

        w, h = float(self.width), float(self.height)

        # Wandering gravitational attractor singularity
        attractor_x = w * 0.5 + math.sin(self.time * 0.18) * (w * 0.32)
        attractor_y = h * 0.5 + math.cos(self.time * 0.14) * (h * 0.28)
        gravity_strength = 2800.0

        for p in self.particles:
            # Gravitational pull + gentle tangential swirl
            dx = attractor_x - p.x
            dy = attractor_y - p.y
            dist_sq = dx * dx + dy * dy + 8000.0
            force = (gravity_strength / dist_sq) * p.depth

            # Orthogonal swirl vector
            swirl_x = -dy / math.sqrt(dist_sq) * force * 1.5
            swirl_y = dx / math.sqrt(dist_sq) * force * 1.5

            p.vx += ((dx / math.sqrt(dist_sq)) * force + swirl_x) * dt
            p.vy += ((dy / math.sqrt(dist_sq)) * force + swirl_y) * dt

            # Drag/damping to maintain balanced speeds
            speed_sq = p.vx * p.vx + p.vy * p.vy
            max_speed = 90.0 * p.depth
            if speed_sq > max_speed * max_speed:
                damping = max_speed / math.sqrt(speed_sq)
                p.vx *= damping
                p.vy *= damping

            p.x += p.vx * dt
            p.y += p.vy * dt

            # Soft boundary wrap
            margin = 25.0
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

        conn_dist = min(95.0, float(self.config.particles_connection_distance))
        conn_dist_sq = conn_dist * conn_dist
        fade = self.fade_in * self.luminance_factor

        # 1. Proximity Filaments via Spatial Grid (Only foreground/midground connect)
        cell_size = conn_dist
        grid: Dict[Tuple[int, int], List[Particle]] = {}
        for p in self.particles:
            if p.depth < 0.4:
                continue
            cx = int(p.x // cell_size)
            cy = int(p.y // cell_size)
            key = (cx, cy)
            if key not in grid:
                grid[key] = []
            grid[key].append(p)

        cr.set_line_width(0.7)
        line_base = self.theme.primary
        conns = {id(p): 0 for p in self.particles}

        for (cx, cy), cell_particles in grid.items():
            for i, p1 in enumerate(cell_particles):
                if conns[id(p1)] >= 2:
                    continue
                # Intra-cell
                for j in range(i + 1, len(cell_particles)):
                    p2 = cell_particles[j]
                    if conns[id(p2)] >= 2:
                        continue
                    dx, dy = p2.x - p1.x, p2.y - p1.y
                    d_sq = dx * dx + dy * dy
                    if d_sq < conn_dist_sq:
                        d = math.sqrt(d_sq)
                        alpha = (1.0 - d / conn_dist) ** 1.8 * 0.35 * min(p1.depth, p2.depth) * fade
                        cr.set_source_rgba(*self.oled_color(with_alpha(line_base, alpha)))
                        cr.move_to(p1.x, p1.y)
                        cr.line_to(p2.x, p2.y)
                        cr.stroke()
                        conns[id(p1)] += 1
                        conns[id(p2)] += 1
                        if conns[id(p1)] >= 2:
                            break

                # Neighboring cells
                if conns[id(p1)] >= 2:
                    continue
                for ox, oy in [(1, 0), (-1, 1), (0, 1), (1, 1)]:
                    neighbor = (cx + ox, cy + oy)
                    if neighbor in grid:
                        for p2 in grid[neighbor]:
                            if conns[id(p2)] >= 2:
                                continue
                            dx, dy = p2.x - p1.x, p2.y - p1.y
                            d_sq = dx * dx + dy * dy
                            if d_sq < conn_dist_sq:
                                d = math.sqrt(d_sq)
                                alpha = (1.0 - d / conn_dist) ** 1.8 * 0.35 * min(p1.depth, p2.depth) * fade
                                cr.set_source_rgba(*self.oled_color(with_alpha(line_base, alpha)))
                                cr.move_to(p1.x, p1.y)
                                cr.line_to(p2.x, p2.y)
                                cr.stroke()
                                conns[id(p1)] += 1
                                conns[id(p2)] += 1
                                if conns[id(p1)] >= 2:
                                    break
                    if conns[id(p1)] >= 2:
                        break

        # 2. Render Particles by Depth Layers (Distant -> Midground -> Foreground)
        color_palettes = [self.theme.primary, self.theme.accent, self.theme.secondary]

        # Sort slightly or bucket by depth for proper volumetric rendering
        for p in self.particles:
            pulse = 0.85 + 0.15 * math.sin(self.time * 2.0 + p.phase)
            r = p.base_radius * pulse
            base_col = color_palettes[p.color_idx]
            alpha = p.base_alpha * fade

            # Foreground subtle glow halo
            if p.depth > 0.75:
                cr.set_source_rgba(*self.oled_color(with_alpha(base_col, alpha * 0.20)))
                cr.arc(p.x, p.y, r * 2.2, 0, math.pi * 2)
                cr.fill()

            cr.set_source_rgba(*self.oled_color(with_alpha(base_col, alpha)))
            cr.arc(p.x, p.y, r, 0, math.pi * 2)
            cr.fill()
