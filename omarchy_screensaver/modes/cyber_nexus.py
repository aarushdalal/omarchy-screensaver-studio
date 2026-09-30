"""Mode: Cyber Nexus (Cybernetic Neon Hex Grid & Circuit Energy Flow).

Renders a futuristic, dark, isometric hexagonal energy lattice with faint circuit lines.
Subdued data packets and glowing energy pulses race between junction nodes on a pure
OLED true-black background. Subdued, dark aesthetic designed for deep focus without glare.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class Packet:
    """A moving data packet traveling along hex circuit edges."""
    __slots__ = ("x", "y", "target_x", "target_y", "progress", "speed", "color_idx", "tail")

    def __init__(self, x: float, y: float, tx: float, ty: float, speed: float, color_idx: int):
        self.x = x
        self.y = y
        self.target_x = tx
        self.target_y = ty
        self.progress = 0.0
        self.speed = speed
        self.color_idx = color_idx
        self.tail: List[Tuple[float, float]] = []


class CyberNexusMode(BaseMode):
    """Subdued dark cybernetic circuit grid screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.target_fps = 40

        self.hex_radius = 56.0
        self.nodes: List[Tuple[float, float]] = []
        self.edges: List[Tuple[int, int]] = []
        self.adjacency: Dict[int, List[int]] = {}
        self.packets: List[Packet] = []
        self.node_pulses: Dict[int, float] = {}  # node_idx -> pulse intensity

        self._init_grid(self.width, self.height)

    def _init_grid(self, width: int, height: int):
        self.nodes = []
        self.edges = []
        self.adjacency = {}
        self.packets = []
        self.node_pulses = {}

        r = self.hex_radius
        w_step = r * math.sqrt(3)
        h_step = r * 1.5

        cols = int(width // w_step) + 3
        rows = int(height // h_step) + 3

        node_map: Dict[Tuple[int, int], int] = {}

        # Generate hex vertices
        for row in range(-1, rows):
            y_base = row * h_step
            offset_x = (w_step * 0.5) if (row % 2 == 1) else 0.0
            for col in range(-1, cols):
                cx = col * w_step + offset_x
                cy = y_base
                # 6 vertices of hexagon
                for i in range(6):
                    angle = math.pi / 6.0 + i * math.pi / 3.0
                    vx = round(cx + r * math.cos(angle), 1)
                    vy = round(cy + r * math.sin(angle), 1)
                    grid_key = (int(vx), int(vy))
                    if grid_key not in node_map:
                        idx = len(self.nodes)
                        self.nodes.append((vx, vy))
                        node_map[grid_key] = idx
                        self.adjacency[idx] = []

        # Connect neighboring vertices within edge distance ~r
        r_sq_max = (r * 1.05) ** 2
        r_sq_min = (r * 0.90) ** 2
        for i in range(len(self.nodes)):
            x1, y1 = self.nodes[i]
            for j in range(i + 1, len(self.nodes)):
                x2, y2 = self.nodes[j]
                d2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if r_sq_min <= d2 <= r_sq_max:
                    self.edges.append((i, j))
                    self.adjacency[i].append(j)
                    self.adjacency[j].append(i)

        # Spawn initial data packets
        random.seed(42 + self.monitor_index * 1337)
        packet_count = 24
        for _ in range(packet_count):
            self._spawn_packet()

    def _spawn_packet(self):
        if not self.edges:
            return
        u, v = random.choice(self.edges)
        if random.random() < 0.5:
            u, v = v, u
        x1, y1 = self.nodes[u]
        x2, y2 = self.nodes[v]
        speed = random.uniform(0.7, 1.4)
        c_idx = random.choice([0, 1, 2])
        p = Packet(x1, y1, x2, y2, speed, c_idx)
        p.tail = [(x1, y1)]
        self.packets.append(p)

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_grid(width, height)

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.8)

        # Decay node pulses
        for idx in list(self.node_pulses.keys()):
            self.node_pulses[idx] -= dt * 2.0
            if self.node_pulses[idx] <= 0.0:
                del self.node_pulses[idx]

        # Update packets
        surviving: List[Packet] = []
        for p in self.packets:
            p.progress += p.speed * dt
            cur_x = p.x + (p.target_x - p.x) * min(1.0, p.progress)
            cur_y = p.y + (p.target_y - p.y) * min(1.0, p.progress)
            p.tail.append((cur_x, cur_y))
            if len(p.tail) > 6:
                p.tail.pop(0)

            if p.progress >= 1.0:
                # Arrived at target: find closest node index to target
                target_pos = (p.target_x, p.target_y)
                # Find connected neighbor
                next_targets = []
                for u, v in self.edges:
                    if abs(self.nodes[u][0] - target_pos[0]) < 2 and abs(self.nodes[u][1] - target_pos[1]) < 2:
                        next_targets.append(v)
                    elif abs(self.nodes[v][0] - target_pos[0]) < 2 and abs(self.nodes[v][1] - target_pos[1]) < 2:
                        next_targets.append(u)

                if next_targets:
                    next_node = random.choice(next_targets)
                    tx, ty = self.nodes[next_node]
                    p.x, p.y = target_pos
                    p.target_x, p.target_y = tx, ty
                    p.progress = 0.0
                    p.color_idx = random.choice([0, 1, 2])
                    surviving.append(p)
                else:
                    # Reroll packet
                    pass
            else:
                surviving.append(p)

        while len(surviving) < 24:
            self._spawn_packet()
        self.packets = surviving

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)
        fade = self.fade_in * self.luminance_factor

        # 1. Subtle, muted hex wireframe (faint dark lines - non-glaring)
        cr.set_line_width(0.9 * scale)
        r, g, b = self.theme.muted_rgb
        cr.set_source_rgba(r, g, b, 0.12 * fade)
        for u, v in self.edges:
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
        cr.stroke()

        # 2. Glowing junction node points
        cr.set_source_rgba(r, g, b, 0.22 * fade)
        node_radius = 1.6 * scale
        for x, y in self.nodes:
            cr.arc(x, y, node_radius, 0, math.pi * 2)
        cr.fill()

        # 3. Moving Data Packets & Phosphorescent Trails
        palettes = [self.theme.accent_rgb, self.theme.primary_rgb, self.theme.secondary_rgb]

        for p in self.packets:
            if not p.tail:
                continue
            pr, pg, pb = palettes[p.color_idx % len(palettes)]

            # Draw tail
            if len(p.tail) >= 2:
                for i in range(len(p.tail) - 1):
                    alpha = (i + 1) / len(p.tail) * 0.40 * fade
                    cr.set_source_rgba(pr, pg, pb, alpha)
                    cr.set_line_width((1.2 + i * 0.3) * scale)
                    cr.move_to(p.tail[i][0], p.tail[i][1])
                    cr.line_to(p.tail[i + 1][0], p.tail[i + 1][1])
                    cr.stroke()

            # Packet head
            hx, hy = p.tail[-1]
            cr.set_source_rgba(pr, pg, pb, 0.65 * fade)
            cr.arc(hx, hy, 2.5 * scale, 0, math.pi * 2)
            cr.fill()
