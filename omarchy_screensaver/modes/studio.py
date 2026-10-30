"""Shared, bounded drawing primitives for the ambient collection."""
import math
import random
import cairo
from .base import BaseMode

TAU = math.tau


def smooth_path(cr, points, closed=False):
    """Interpolating Catmull-Rom spline, converted to Cairo cubic segments."""
    if len(points) < 2:
        return
    cr.new_path()
    cr.move_to(*points[0])
    n = len(points)
    for i in range(n if closed else n - 1):
        p0 = points[(i - 1) % n] if closed else points[max(0, i - 1)]
        p1, p2 = points[i % n], points[(i + 1) % n]
        p3 = points[(i + 2) % n] if closed else points[min(n - 1, i + 2)]
        cr.curve_to(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                    p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, *p2)
    if closed:
        cr.close_path()


def halo(cr, x, y, radius, color, alpha):
    cr.new_path()
    grad = cairo.RadialGradient(x, y, 0, x, y, max(0.1, radius))
    grad.add_color_stop_rgba(0, *color[:3], alpha)
    grad.add_color_stop_rgba(0.35, *color[:3], alpha * 0.25)
    grad.add_color_stop_rgba(1, *color[:3], 0)
    cr.set_source(grad)
    cr.arc(x, y, radius, 0, TAU)
    cr.fill()


class AmbientMode(BaseMode):
    target_fps = 30

    def __init__(self, theme, config, monitor_index=0):
        super().__init__(theme, config, monitor_index)
        self.rng = random.Random(7301 + monitor_index * 1337)
        self.width, self.height = 1920, 1080
        self.fade_in = 0.0
        self.stars = [(self.rng.random(), self.rng.random(), self.rng.uniform(0.5, 1.5),
                       self.rng.random() * TAU) for _ in range(52)]

    def on_resize(self, width, height):
        if width > 0 and height > 0:
            self.width, self.height = width, height

    def update(self, dt, metrics, media_info):
        super().update(dt, metrics, media_info)
        self.fade_in = min(1, self.fade_in + max(0, dt) * 0.65)

    @property
    def fade(self):
        return self.fade_in * (self.luminance_factor if self.theme.is_dark else 1)

    def anchor(self, width, height):
        # A small orbit, scaled to the canvas; enough empty margin remains.
        return (width * 0.5 + (self.burn_x + self.jitter_x) * 0.22,
                height * 0.5 + (self.burn_y + self.jitter_y) * 0.22)

    def starfield(self, cr, width, height, strength=1):
        color = self.theme.foreground[:3]
        for u, v, r, phase in self.stars:
            cr.new_sub_path()
            cr.arc(u * width, v * height, r * min(width, height) / 1080, 0, TAU)
            cr.set_source_rgba(*color, strength * self.fade * (0.12 + 0.10 * math.sin(self.time * 0.15 + phase)))
            cr.fill()
