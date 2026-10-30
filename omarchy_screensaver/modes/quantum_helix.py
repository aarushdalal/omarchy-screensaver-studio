"""Quantum Helix: continuous strands, depth-sorted bonds and floating dust."""
import math
from .studio import AmbientMode, TAU, halo


class QuantumHelixMode(AmbientMode):
    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        self.starfield(cr, width, height, 0.6)
        cx, cy = self.anchor(width, height)
        radius = min(width, height) * 0.14
        length = height * 0.73
        t = self.time * 0.24
        colors = [self.theme.accent_rgb, self.theme.secondary_rgb]
        segments = []
        def point(u, strand):
            a = u * TAU * 1.65 + t + strand * math.pi
            z = math.sin(a)
            return (cx + math.cos(a) * radius, cy + (u - 0.5) * length, z)
        for strand in range(2):
            for i in range(140):
                u, v = i / 140, (i + 1) / 140
                p, q = point(u, strand), point(v, strand)
                segments.append(((p[2] + q[2]) * 0.5, 'strand', (p, q, strand, u)))
        for i in range(31):
            u = i / 30
            p, q = point(u, 0), point(u, 1)
            segments.append((0, 'bond', (p, q, i % 2, u)))
            for strand, p in enumerate((p, q)):
                segments.append((p[2], 'node', (p, p, strand, u)))
        for depth, kind, (p, q, strand, u) in sorted(segments, key=lambda item: item[0]):
            taper = min(1, min(u, 1 - u) * 12 + 0.15)
            alpha = (0.20 + 0.48 * (depth + 1) * 0.5) * self.fade * taper
            color = colors[strand]
            if kind == 'node':
                r = (1.6 + (depth + 1) * 0.9) * scale
                halo(cr, p[0], p[1], r * 3.5, color, alpha * 0.35)
                cr.new_path(); cr.arc(p[0], p[1], r, 0, TAU)
                cr.set_source_rgba(*color, alpha); cr.fill()
            else:
                cr.set_source_rgba(*color, alpha * (0.65 if kind == 'bond' else 0.85))
                cr.set_line_width((0.85 if kind == 'bond' else 1.7) * scale)
                cr.move_to(p[0], p[1]); cr.line_to(q[0], q[1]); cr.stroke()
