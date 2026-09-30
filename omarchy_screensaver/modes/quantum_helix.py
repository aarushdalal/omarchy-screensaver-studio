"""Mode: Quantum Helix (3D Bioluminescent Dual DNA Helix & Gentle Stardust).

Renders a 3D-projected rotating double helix of molecular base pairs with connecting
energy rungs and trailing ambient stardust motes.
Strictly calibrated for dark aesthetic and eye comfort:
  - Deep obsidian space void (true OLED black #000000)
  - Subdued, non-glaring bioluminescent tones (soft cyan, lavender, muted emerald)
  - Smooth 3D depth projection with depth-cueing alpha falloff
"""

import math
import random
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class Mote:
    __slots__ = ("x", "y", "size", "alpha", "speed_y", "phase")

    def __init__(self, x: float, y: float, size: float, alpha: float, speed_y: float, phase: float):
        self.x = x
        self.y = y
        self.size = size
        self.alpha = alpha
        self.speed_y = speed_y
        self.phase = phase


class QuantumHelixMode(BaseMode):
    """Subdued 3D rotating dual helix screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.target_fps = 40

        self.rotation_angle = 0.0
        self.rotation_speed = 0.42
        self.motes: List[Mote] = []

        self._init_motes(self.width, self.height)

    def _init_motes(self, width: int, height: int):
        random.seed(55 + self.monitor_index * 444)
        self.motes = []
        for _ in range(50):
            self.motes.append(
                Mote(
                    x=random.uniform(0, width),
                    y=random.uniform(0, height),
                    size=random.uniform(0.8, 2.0),
                    alpha=random.uniform(0.15, 0.40),
                    speed_y=random.uniform(4.0, 12.0),
                    phase=random.uniform(0, math.pi * 2),
                )
            )

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_motes(width, height)

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        self.rotation_angle += dt * self.rotation_speed

        # Float motes upwards
        for m in self.motes:
            m.y -= m.speed_y * dt
            if m.y < -10:
                m.y = self.height + 10
                m.x = random.uniform(0, self.width)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)
        fade = self.fade_in * self.luminance_factor

        # 1. Background motes
        for m in self.motes:
            twinkle = 0.7 + 0.3 * math.sin(self.time * 2.0 + m.phase)
            cr.set_source_rgba(1.0, 1.0, 1.0, m.alpha * twinkle * fade)
            cr.arc(m.x, m.y, m.size * scale, 0, math.pi * 2)
            cr.fill()

        # 2. 3D Projected Dual Helix
        center_x = width * 0.5
        helix_radius = min(width, height) * 0.18
        num_pairs = 42
        helix_len = height * 1.15
        start_y = -height * 0.08
        dy = helix_len / num_pairs

        ar, ag, ab = self.theme.accent_rgb
        pr, pg, pb = self.theme.primary_rgb
        sr, sg, sb = self.theme.secondary_rgb

        # Store node 3D coordinates for depth-sorting
        elements = []  # tuple of (z_avg, type, data)

        for i in range(num_pairs):
            y = start_y + i * dy
            phase = self.rotation_angle + (i * 0.22)

            # Strand 1
            x1 = center_x + math.cos(phase) * helix_radius
            z1 = math.sin(phase)  # -1.0 to 1.0 depth

            # Strand 2 (pi offset)
            x2 = center_x + math.cos(phase + math.pi) * helix_radius
            z2 = math.sin(phase + math.pi)

            # Base pair rung connecting the two strands
            z_avg = (z1 + z2) * 0.5
            elements.append((z_avg, "rung", (x1, y, z1, x2, y, z2, i)))
            elements.append((z1, "node1", (x1, y, z1)))
            elements.append((z2, "node2", (x2, y, z2)))

        # Sort elements by Z depth (back-to-front rendering for accurate 3D occlusions)
        elements.sort(key=lambda item: item[0])

        for z, el_type, data in elements:
            # Depth cueing: z ranges -1.0 (distant) to 1.0 (near)
            depth_factor = 0.5 + 0.5 * z  # 0.0 to 1.0
            node_r = (2.0 + 2.5 * depth_factor) * scale
            base_alpha = (0.20 + 0.45 * depth_factor) * fade

            if el_type == "rung":
                x1, y1, z1, x2, y2, z2, rung_idx = data
                # Low-alpha subtle connecting bridge
                rung_color = pr, pg, pb if (rung_idx % 2 == 0) else sr, sg, sb
                cr.set_source_rgba(rung_color[0], rung_color[1], rung_color[2], base_alpha * 0.65)
                cr.set_line_width((0.8 + 1.2 * depth_factor) * scale)
                cr.move_to(x1, y1)
                cr.line_to(x2, y2)
                cr.stroke()

                # Middle hydrogen bond glowing spark
                mid_x = (x1 + x2) * 0.5
                cr.set_source_rgba(1.0, 1.0, 1.0, base_alpha * 0.8)
                cr.arc(mid_x, y1, 1.2 * scale, 0, math.pi * 2)
                cr.fill()

            elif el_type == "node1":
                x, y, z_val = data
                # Strand 1 node (Accent color, subdued)
                cr.set_source_rgba(ar, ag, ab, base_alpha)
                cr.arc(x, y, node_r, 0, math.pi * 2)
                cr.fill()

                # Inner gentle core
                cr.set_source_rgba(1.0, 1.0, 1.0, base_alpha * 0.7)
                cr.arc(x, y, node_r * 0.45, 0, math.pi * 2)
                cr.fill()

            elif el_type == "node2":
                x, y, z_val = data
                # Strand 2 node (Primary color, subdued)
                cr.set_source_rgba(pr, pg, pb, base_alpha)
                cr.arc(x, y, node_r, 0, math.pi * 2)
                cr.fill()

                # Inner gentle core
                cr.set_source_rgba(1.0, 1.0, 1.0, base_alpha * 0.7)
                cr.arc(x, y, node_r * 0.45, 0, math.pi * 2)
                cr.fill()
