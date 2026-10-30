"""Celestial Orbit: eccentric Kepler paths with time-based orbital trails."""
import math
from .studio import AmbientMode, TAU, halo, smooth_path


class CelestialOrbitMode(AmbientMode):
    # Semi-major axis, eccentricity, angular speed, orbital orientation.
    ORBITS = [(0.29, 0.12, 0.36, 0.25), (0.48, 0.18, 0.22, -0.3),
              (0.70, 0.14, 0.13, 0.42), (0.94, 0.23, 0.08, -0.12)]

    @staticmethod
    def position(a, eccentricity, orientation, mean):
        E = mean
        for _ in range(5):
            E -= (E - eccentricity * math.sin(E) - mean) / (1 - eccentricity * math.cos(E))
        x = a * (math.cos(E) - eccentricity)
        y = a * math.sqrt(1 - eccentricity ** 2) * math.sin(E)
        # Apply orientation in the orbital plane, then project the whole plane.
        return (x * math.cos(orientation) - y * math.sin(orientation),
                (x * math.sin(orientation) + y * math.cos(orientation)) * 0.55)

    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        self.starfield(cr, width, height, 0.6)
        cx, cy = self.anchor(width, height)
        base = min(width * 0.39, height * 0.57)
        colors = [self.theme.accent_rgb, self.theme.secondary_rgb, self.theme.foreground[:3]]
        halo(cr, cx, cy, 36 * scale, colors[0], 0.32 * self.fade)
        cr.arc(cx, cy, 4.2 * scale, 0, TAU)
        cr.set_source_rgba(*colors[2], 0.75 * self.fade); cr.fill()
        for index, (size, e, speed, orientation) in enumerate(self.ORBITS):
            color = colors[index % 3]
            def at(mean):
                x, y = self.position(base * size, e, orientation, mean)
                return cx + x, cy + y
            guide = [at(TAU * i / 128) for i in range(128)]
            smooth_path(cr, guide, closed=True)
            cr.set_source_rgba(*color, 0.17 * self.fade)
            cr.set_line_width(0.8 * scale); cr.stroke()
            mean = self.time * speed + index * 1.6
            # Trail duration is measured in seconds, independent of FPS or resize.
            for i in range(48):
                p = at(mean - (48 - i) * 0.11)
                q = at(mean - (47 - i) * 0.11)
                f = (i + 1) / 48
                cr.move_to(*p); cr.line_to(*q)
                cr.set_source_rgba(*color, f * f * 0.58 * self.fade)
                cr.set_line_width((0.8 + f * 1.8) * scale); cr.stroke()
            x, y = at(mean)
            halo(cr, x, y, (12 + index * 2) * scale, color, 0.36 * self.fade)
            cr.arc(x, y, (3.2 + index * 0.5) * scale, 0, TAU)
            cr.set_source_rgba(*color, 0.8 * self.fade); cr.fill()
