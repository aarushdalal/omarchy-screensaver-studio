"""Mode 9: Sacred Geometry & 4D Rotating Tesseract.

Simulates a 4-dimensional hypercube (tesseract) projected into 3D and 2D space
under dual orthogonal 4D rotational planes (XW and YZ), with depth-cued glowing edges,
luminous vertex nodes, and complete OLED black background.
"""

import math
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class GeometryMode(BaseMode):
    """4D Hypercube / Sacred Geometry screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.fade_in = 0.0
        self.target_fps = 60

        # Angles for 4D and 3D rotations
        self.angle_xw = 0.0
        self.angle_yz = 0.0
        self.angle_xy = 0.0

        # Generate 16 vertices of a 4D hypercube: (+-1, +-1, +-1, +-1)
        self.vertices_4d: List[List[float]] = []
        for x in (-1.0, 1.0):
            for y in (-1.0, 1.0):
                for z in (-1.0, 1.0):
                    for w in (-1.0, 1.0):
                        self.vertices_4d.append([x, y, z, w])

        # Generate 32 edges connecting vertices that differ by exactly 1 coordinate
        self.edges: List[Tuple[int, int]] = []
        for i in range(16):
            for j in range(i + 1, 16):
                diff = sum(1 for k in range(4) if self.vertices_4d[i][k] != self.vertices_4d[j][k])
                if diff == 1:
                    self.edges.append((i, j))

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        rot_speed = getattr(self.config, "geometry_rotation_speed", 0.6)
        self.angle_xw += dt * rot_speed * 0.75
        self.angle_yz += dt * rot_speed * 0.55
        self.angle_xy += dt * rot_speed * 0.35

    def _rotate_4d(self, v: List[float]) -> List[float]:
        """Apply dual 4D rotations (X-W plane and Y-Z plane)."""
        x, y, z, w = v

        # Rotate around X-W plane
        cos_xw, sin_xw = math.cos(self.angle_xw), math.sin(self.angle_xw)
        x1 = x * cos_xw - w * sin_xw
        w1 = x * sin_xw + w * cos_xw

        # Rotate around Y-Z plane
        cos_yz, sin_yz = math.cos(self.angle_yz), math.sin(self.angle_yz)
        y1 = y * cos_yz - z * sin_yz
        z1 = y * sin_yz + z * cos_yz

        # Rotate around X-Y plane (3D tilt)
        cos_xy, sin_xy = math.cos(self.angle_xy), math.sin(self.angle_xy)
        x2 = x1 * cos_xy - y1 * sin_xy
        y2 = x1 * sin_xy + y1 * cos_xy

        return [x2, y2, z1, w1]

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        # 100% OLED pitch black void
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        cx = width * 0.5 + self.burn_x + self.jitter_x
        cy = height * 0.5 + self.burn_y + self.jitter_y

        base_scale = min(width, height) * 0.28
        distance_4d = 2.4
        distance_3d = 3.2

        projected_2d: List[Tuple[float, float, float]] = []

        # Project 4D vertices -> 3D -> 2D
        for v in self.vertices_4d:
            x, y, z, w = self._rotate_4d(v)

            # 4D to 3D perspective projection
            w_factor = 1.0 / (distance_4d - w)
            x3d = x * w_factor
            y3d = y * w_factor
            z3d = z * w_factor

            # 3D to 2D perspective projection
            z_factor = 1.0 / (distance_3d - z3d)
            px = cx + x3d * z_factor * base_scale * 3.5
            py = cy + y3d * z_factor * base_scale * 3.5

            # Combined depth for lighting and cueing
            depth = (w + 1.0) * 0.5 * 0.5 + (z + 1.0) * 0.5 * 0.5
            projected_2d.append((px, py, depth))

        # Sort edges by average depth so distant edges draw behind near edges
        sorted_edges = []
        for i, j in self.edges:
            avg_depth = (projected_2d[i][2] + projected_2d[j][2]) * 0.5
            sorted_edges.append((avg_depth, i, j))
        sorted_edges.sort(key=lambda item: item[0])

        # 1. Render Edges with depth cueing & chromatic gradient
        line_w_base = getattr(self.config, "geometry_line_width", 1.6)

        for depth, i, j in sorted_edges:
            p1 = projected_2d[i]
            p2 = projected_2d[j]

            # Depth cueing: near is bright neon, far is deep translucent
            edge_alpha = (0.25 + 0.75 * depth) * fade
            edge_width = line_w_base * (0.65 + 0.95 * depth)

            pat = cairo.LinearGradient(p1[0], p1[1], p2[0], p2[1])
            pat.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(self.theme.primary, edge_alpha)))
            pat.add_color_stop_rgba(1.0, *self.oled_color(with_alpha(self.theme.accent, edge_alpha)))

            # Optional subtle neon glow pass for foreground edges
            if depth > 0.60 and getattr(self.config, "geometry_glow", True):
                cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.accent, edge_alpha * 0.25)))
                cr.set_line_width(edge_width * 2.8)
                cr.move_to(p1[0], p1[1])
                cr.line_to(p2[0], p2[1])
                cr.stroke()

            cr.set_source(pat)
            cr.set_line_width(edge_width)
            cr.move_to(p1[0], p1[1])
            cr.line_to(p2[0], p2[1])
            cr.stroke()

        # 2. Render Vertex Nodes with Glowing Halos
        for px, py, depth in projected_2d:
            node_r = 2.5 + 3.0 * depth
            node_alpha = (0.35 + 0.65 * depth) * fade

            # Halo
            cr.set_source_rgba(*self.oled_color(with_alpha(self.theme.bright_foreground, node_alpha * 0.35)))
            cr.arc(px, py, node_r * 2.0, 0, math.pi * 2)
            cr.fill()

            # Core
            cr.set_source_rgba(*self.oled_color(with_alpha((1.0, 1.0, 1.0, 1.0), node_alpha * 0.95)))
            cr.arc(px, py, node_r, 0, math.pi * 2)
            cr.fill()
