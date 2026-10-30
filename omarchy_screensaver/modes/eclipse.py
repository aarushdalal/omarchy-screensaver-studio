"""Eclipse: a dark lunar disc inside a slowly breathing solar corona."""
import math
import cairo
from .studio import AmbientMode, TAU, halo, smooth_path


class EclipseMode(AmbientMode):
    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        self.starfield(cr, width, height, 0.8)
        cx, cy = self.anchor(width, height)
        radius = min(width, height) * 0.205
        color, second = self.theme.accent_rgb, self.theme.secondary_rgb
        t, fade = self.time * 0.065, self.fade
        halo(cr, cx, cy, radius * 2.3, color, 0.18 * fade)
        for ring in range(11, -1, -1):
            points = []
            for i in range(80):
                a = TAU * i / 80
                flare = (0.5 + 0.5 * math.sin(a * 7 + t)) ** 3
                ripple = math.sin(a * 3 - t) * 0.035 + math.sin(a * 11 + t * 1.4) * 0.008
                rr = radius * (1.02 + ring * 0.025 + ripple * ring / 11 + flare * 0.08 * ring / 11)
                points.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            smooth_path(cr, points, closed=True)
            cr.set_source_rgba(*(color if ring % 3 else second), (0.045 + 0.36 * (1 - ring / 12) ** 3) * fade)
            cr.set_line_width((1 + ring * 0.08) * scale)
            cr.stroke()
        cr.new_path()
        cr.arc(cx, cy, radius, 0, TAU)
        cr.set_source_rgba(*( (0, 0, 0) if self.config.oled_mode and self.theme.is_dark else self.theme.background[:3]), 1)
        cr.fill()
        rim = cairo.LinearGradient(cx - radius, cy - radius, cx + radius, cy + radius)
        rim.add_color_stop_rgba(0, *second, 0.62 * fade)
        rim.add_color_stop_rgba(0.45, *color, 0.18 * fade)
        rim.add_color_stop_rgba(1, *color, 0.48 * fade)
        cr.arc(cx, cy, radius * 1.003, 0, TAU)
        cr.set_line_width(1.8 * scale)
        cr.set_source(rim)
        cr.stroke()
        a = -0.7 + math.sin(t * 0.6) * 0.5
        halo(cr, cx + math.cos(a) * radius, cy + math.sin(a) * radius, radius * 0.12, second, 0.6 * fade)
