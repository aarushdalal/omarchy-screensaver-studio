"""Rain on Glass: quiet night bokeh, drifting droplets and long reflections."""
import math
import cairo
from .studio import AmbientMode, TAU, halo


class RainMode(AmbientMode):
    def __init__(self, theme, config, monitor_index=0):
        super().__init__(theme, config, monitor_index)
        self.lights = [(self.rng.random(), self.rng.uniform(0.38, 0.70), self.rng.uniform(10, 32),
                        self.rng.randrange(3), self.rng.random() * TAU) for _ in range(16)]
        self.drops = [(self.rng.random(), self.rng.random(), self.rng.uniform(0.012, 0.055),
                       self.rng.uniform(0.55, 1.5), self.rng.random() * TAU) for _ in range(90)]

    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        colors = [self.theme.accent_rgb, self.theme.secondary_rgb, self.theme.foreground[:3]]
        for u, v, radius, c, phase in self.lights:
            x = u * width + math.sin(self.time * 0.035 + phase) * width * 0.008
            y = v * height
            r = radius * min(width, height) / 864
            alpha = (0.20 + 0.04 * math.sin(self.time * 0.18 + phase)) * self.fade
            halo(cr, x, y, r * 2.2, colors[c], alpha)
            cr.save()
            cr.translate(x, height * 0.83)
            cr.scale(0.28, 2.3)
            halo(cr, 0, 0, r * 1.5, colors[c], alpha * 0.25)
            cr.restore()
        for u, v, speed, size, phase in self.drops:
            y = ((v + self.time * speed) % 1.15 - 0.075) * height
            x = u * width + math.sin(self.time * 0.12 + phase) * 2 * scale
            length = (5 + speed * 400) * scale
            grad = cairo.LinearGradient(x, y - length, x, y)
            grad.add_color_stop_rgba(0, *self.theme.accent_rgb, 0)
            grad.add_color_stop_rgba(1, *self.theme.foreground[:3], 0.26 * self.fade)
            cr.set_source(grad)
            cr.set_line_width(size * scale)
            cr.move_to(x + length * 0.06, y - length)
            cr.line_to(x, y)
            cr.stroke()
            cr.new_path()
            cr.arc(x, y, size * scale, 0, TAU)
            cr.set_source_rgba(*self.theme.foreground[:3], 0.25 * self.fade)
            cr.fill()
