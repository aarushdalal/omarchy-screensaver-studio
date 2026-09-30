"""Mode: Topography (Generative Fluid Topographic Depth Contours).

Renders living, undulating elevation contour lines (like luxury cartographic depth charts)
flowing across the screen with gentle multi-harmonic turbulence.
Strictly calibrated for dark aesthetic and eye comfort:
  - Deep obsidian space void (true OLED black #000000)
  - Faint, non-glaring contour elevation lines in muted theme palettes (alpha 0.15 - 0.38)
  - Ultra-low system usage (~1-2% CPU) and peaceful meditative flow for study sprints.
"""

import math
from typing import List, Optional, Tuple

import cairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class TopographyMode(BaseMode):
    """Subdued generative topographic contour screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.fade_in = 0.0
        self.target_fps = 30
        self.flow_time = 0.0

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        self.flow_time += dt * 0.18

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        self.clear_background(cr, width, height)
        fade = self.fade_in * self.luminance_factor

        num_contours = 18
        step_x = 24.0 * scale
        steps = int(width // step_x) + 2

        t = self.flow_time
        ar, ag, ab = self.theme.accent_rgb
        pr, pg, pb = self.theme.primary_rgb
        mr, mg, mb = self.theme.muted_rgb

        cr.set_line_width(1.0 * scale)

        # Draw series of elevation contour curves
        for c_idx in range(num_contours):
            # Base vertical elevation band
            base_y = (height * 0.08) + (c_idx / float(num_contours)) * (height * 0.84)
            c_factor = c_idx / float(num_contours)

            # Palette blending: from muted slate to primary and accent
            if c_idx % 3 == 0:
                cr_r, cr_g, cr_b = ar, ag, ab
            elif c_idx % 3 == 1:
                cr_r, cr_g, cr_b = pr, pg, pb
            else:
                cr_r, cr_g, cr_b = mr, mg, mb

            # Very low alpha: 0.15 to 0.35, gentle on eyes, never harsh
            alpha = (0.14 + 0.22 * math.sin(c_factor * math.pi)) * fade
            cr.set_source_rgba(cr_r, cr_g, cr_b, alpha)

            # Build smooth wave contour
            cr.move_to(0, base_y)
            for s in range(steps):
                x = s * step_x
                nx = x * 0.003
                # Harmonic superposition: large gentle wave + small subtle ripple
                w1 = math.sin(nx * 2.4 + t * 0.8 + c_factor * 2.0) * 38.0
                w2 = math.cos(nx * 4.8 - t * 0.5 + c_factor * 1.5) * 18.0
                w3 = math.sin(nx * 1.2 + t * 0.3) * 22.0
                y = base_y + w1 + w2 + w3

                if s == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)

            cr.stroke()

            # Subtle elevation index markers (tiny faint dots every 4th contour)
            if c_idx % 4 == 0:
                cr.set_source_rgba(cr_r, cr_g, cr_b, alpha * 0.8)
                for dot_idx in range(2, steps - 2, 8):
                    dx = dot_idx * step_x
                    dnx = dx * 0.003
                    dy = base_y + (
                        math.sin(dnx * 2.4 + t * 0.8 + c_factor * 2.0) * 38.0
                        + math.cos(dnx * 4.8 - t * 0.5 + c_factor * 1.5) * 18.0
                        + math.sin(dnx * 1.2 + t * 0.3) * 22.0
                    )
                    cr.arc(dx, dy, 1.8 * scale, 0, math.pi * 2)
                    cr.fill()
