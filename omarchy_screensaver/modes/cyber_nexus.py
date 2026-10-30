"""Cyber Nexus: clean honeycomb circuits with bounded travelling signals."""
import math
from .studio import AmbientMode, TAU, halo


class CyberNexusMode(AmbientMode):
    def __init__(self, theme, config, monitor_index=0):
        super().__init__(theme, config, monitor_index)
        self.nodes, self.edges, self.adjacency, self.packets = [], [], {}, []
        self._build_grid(1920, 1080)

    def on_resize(self, width, height):
        if width > 0 and height > 0 and (width, height) != (self.width, self.height):
            super().on_resize(width, height)
            self._build_grid(width, height)

    def _build_grid(self, width, height):
        self.nodes, self.edges, self.adjacency = [], [], {}
        vertices, edges = {}, set()
        r = max(32, min(width, height) * 0.075)
        dx, dy = math.sqrt(3) * r, 1.5 * r
        for row in range(-1, int(height / dy) + 2):
            for col in range(-1, int(width / dx) + 2):
                cx, cy = col * dx + (row % 2) * dx / 2, row * dy
                ids = []
                for i in range(6):
                    a = math.pi / 6 + i * TAU / 6
                    point = (round(cx + r * math.cos(a), 3), round(cy + r * math.sin(a), 3))
                    if point not in vertices:
                        vertices[point] = len(self.nodes)
                        self.nodes.append(point)
                        self.adjacency[vertices[point]] = []
                    ids.append(vertices[point])
                for i in range(6):
                    edges.add(tuple(sorted((ids[i], ids[(i + 1) % 6]))))
        self.edges = sorted(edges)
        for u, v in self.edges:
            self.adjacency[u].append(v); self.adjacency[v].append(u)
        self.packets = [[*self.rng.choice(self.edges), self.rng.random(), self.rng.uniform(0.25, 0.6)] for _ in range(18)]

    def update(self, dt, metrics, media_info):
        super().update(dt, metrics, media_info)
        for packet in self.packets:
            u, v, progress, speed = packet
            progress += max(0, dt) * speed
            # Bounded loop even after a long suspend; no spawning in the update loop.
            if progress >= 1:
                neighbors = [n for n in self.adjacency[v] if n != u] or [u]
                u, v, progress = v, self.rng.choice(neighbors), progress % 1
            packet[:] = u, v, progress, speed

    def render(self, cr, width, height, scale):
        self.clear_background(cr, width, height)
        cx, cy = self.anchor(width, height)
        cr.save(); cr.translate(cx - width * 0.5, cy - height * 0.5)
        color = self.theme.accent_rgb
        cr.set_line_width(0.8 * scale)
        for u, v in self.edges:
            x1, y1 = self.nodes[u]; x2, y2 = self.nodes[v]
            cr.move_to(x1, y1); cr.line_to(x2, y2)
        cr.set_source_rgba(*color, 0.24 * self.fade); cr.stroke()
        for x, y in self.nodes:
            # Each circle needs a fresh subpath: otherwise Cairo fills triangles
            # joining consecutive circles across the entire mesh.
            cr.new_sub_path(); cr.arc(x, y, 1.3 * scale, 0, TAU)
        cr.set_source_rgba(*color, 0.36 * self.fade); cr.fill()
        for i, (u, v, progress, speed) in enumerate(self.packets):
            x1, y1 = self.nodes[u]; x2, y2 = self.nodes[v]
            x, y = x1 + (x2 - x1) * progress, y1 + (y2 - y1) * progress
            c = color if i % 3 else self.theme.secondary_rgb
            halo(cr, x, y, 9 * scale, c, 0.32 * self.fade)
            cr.set_source_rgba(*c, 0.65 * self.fade)
            cr.set_line_width(1.8 * scale)
            start = max(0, progress - 0.24)
            cr.move_to(x1 + (x2 - x1) * start, y1 + (y2 - y1) * start)
            cr.line_to(x, y); cr.stroke()
        cr.restore()
