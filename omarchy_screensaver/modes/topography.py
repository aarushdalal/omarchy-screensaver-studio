"""Topography: nested, smoothly evolving cartographic island contours."""
import math
import cairo
from .studio import AmbientMode, TAU, smooth_path


class TopographyMode(AmbientMode):
    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        cx, cy = self.anchor(width, height)
        t = self.time * 0.075
        # Elliptical islands, with shared harmonics so neighbouring levels never cross.
        for island, (ox, oy, size) in enumerate([(-0.21, 0.05, 0.90), (0.28, -0.11, 0.52)]):
            center_x, center_y = cx + width * ox, cy + height * oy
            for contour in range(20 if island == 0 else 12):
                level = (contour + 2) / (22 if island == 0 else 14)
                points = []
                for i in range(64):
                    a = TAU * i / 64
                    relief = (1 + 0.14 * math.sin(a * 3 + t + island)
                              + 0.09 * math.cos(a * 5 - t * 0.6) + 0.05 * math.sin(a * 2 + t * 0.4))
                    rx = min(width * 0.28, height * 0.38) * size * level * relief
                    points.append((center_x + math.cos(a) * rx * 1.15,
                                   center_y + math.sin(a) * rx * 0.81))
                smooth_path(cr, points, closed=True)
                color = self.theme.secondary_rgb if contour % 5 == 0 else self.theme.accent_rgb
                edge_fade = math.sin(math.pi * level) ** 0.6
                cr.set_source_rgba(*color, (0.65 if contour % 5 == 0 else 0.32) * edge_fade * self.fade)
                cr.set_line_width((1.4 if contour % 5 == 0 else 0.75) * scale)
                cr.stroke()
