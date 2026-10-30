"""Ink Flow: slow, layered silk filaments folded through black space."""
import math
import cairo
from .studio import AmbientMode, smooth_path


class InkFlowMode(AmbientMode):
    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        cx, cy = self.anchor(width, height)
        t = self.time * 0.12
        for layer in range(2):
            color = self.theme.accent_rgb if layer == 0 else self.theme.secondary_rgb
            for strand in range(12):
                v = strand / 11
                points = []
                for i in range(29):
                    u = i / 28
                    x = (u - 0.5) * width * 1.12 + cx
                    envelope = math.sin(math.pi * u) ** 0.7
                    fold = math.sin(u * 5.2 + t + layer * 2.4)
                    ripple = math.cos(u * 10.5 - t * 0.7 + v * 2.5)
                    y = cy + height * (0.17 * fold + (v - 0.5) * 0.34 * envelope * (0.5 + 0.5 * ripple)
                                       + layer * 0.10 - 0.04)
                    points.append((x, y))
                smooth_path(cr, points)
                grad = cairo.LinearGradient(0, 0, width, 0)
                alpha = (0.14 + 0.42 * math.sin(math.pi * v) ** 2) * self.fade
                grad.add_color_stop_rgba(0, *color, 0)
                grad.add_color_stop_rgba(0.25, *color, alpha * 0.6)
                grad.add_color_stop_rgba(0.55, *color, alpha)
                grad.add_color_stop_rgba(1, *color, 0)
                cr.set_source(grad)
                cr.set_line_width((0.7 + 0.5 * math.sin(v * math.pi)) * scale)
                cr.stroke()
