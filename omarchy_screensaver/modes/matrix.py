"""Mode 7: Cybernetic Digital Rain (Matrix Stream).

Simulates high-density cascading digital code rain with 3D parallax depth layers,
white-hot mutating leading glyphs, decaying phosphor trails, and complete OLED black background.
"""

import math
import random
from typing import List, Optional, Tuple

import cairo
from gi.repository import Pango, PangoCairo

from ..metrics import SystemMetrics
from ..mpris import MediaInfo
from ..theme import ThemePalette, with_alpha
from .base import BaseMode

# Rich authentic cyber glyph set: Half-width Katakana + Hex + Math symbols
GLYPHS = [
    chr(i) for i in range(0xFF66, 0xFF9E)  # Half-width Katakana (ｦ - ﾟ)
] + list("0123456789ABCDEF<>/*+=-_~#$@&%|:")


class RainDrop:
    """Represents an active falling code stream."""

    def __init__(self, col: int, depth: float, y: float, speed: float, length: int):
        self.col = col
        self.depth = depth          # 0.3 (deep/dim), 0.6 (mid), 1.0 (foreground)
        self.y = y                  # Head position in row units
        self.speed = speed          # Rows per second
        self.length = length        # Tail length in glyphs
        self.chars: List[str] = [random.choice(GLYPHS) for _ in range(length + 2)]
        self.head_char = random.choice(GLYPHS)
        self.mutation_timer = random.uniform(0.05, 0.15)


class MatrixMode(BaseMode):
    """3D Parallax Digital Rain screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width = 1920
        self.height = 1080
        self.target_fps = 45
        self.fade_in = 0.0

        self.font_size = getattr(self.config, "matrix_font_size", 14)
        self.col_width = self.font_size * 1.25
        self.row_height = self.font_size * 1.55

        self.drops: List[RainDrop] = []
        self._init_drops()

    def _init_drops(self):
        random.seed(1337 + self.monitor_index * 42)
        cols = max(1, int(self.width / self.col_width))
        num_drops = int(cols * getattr(self.config, "matrix_density", 0.85))

        self.drops = []
        speed_scale = getattr(self.config, "matrix_speed", 1.0)

        for _ in range(num_drops):
            col = random.randint(0, cols - 1)
            depth = random.choice([0.35, 0.65, 1.0])
            speed = random.uniform(12.0, 26.0) * speed_scale * (0.6 + 0.4 * depth)
            length = random.randint(12, getattr(self.config, "matrix_rain_length", 26))
            y = random.uniform(-length, float(int(self.height / self.row_height)))
            self.drops.append(RainDrop(col, depth, y, speed, length))

    def on_resize(self, width: int, height: int):
        if width > 0 and height > 0 and (width != self.width or height != self.height):
            self.width = width
            self.height = height
            self._init_drops()

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 1.5)

        max_rows = int(self.height / self.row_height) + 2
        cols = max(1, int(self.width / self.col_width))
        speed_scale = getattr(self.config, "matrix_speed", 1.0)

        for d in self.drops:
            d.y += d.speed * dt

            # Random glyph mutation
            d.mutation_timer -= dt
            if d.mutation_timer <= 0:
                d.mutation_timer = random.uniform(0.05, 0.15)
                d.head_char = random.choice(GLYPHS)
                idx = random.randint(0, len(d.chars) - 1)
                d.chars[idx] = random.choice(GLYPHS)

            # Respawn when tail passes screen bottom
            if d.y - d.length > max_rows:
                d.col = random.randint(0, cols - 1)
                d.depth = random.choice([0.35, 0.65, 1.0])
                d.speed = random.uniform(12.0, 26.0) * speed_scale * (0.6 + 0.4 * d.depth)
                d.length = random.randint(12, getattr(self.config, "matrix_rain_length", 26))
                d.y = random.uniform(-d.length - 4, -1)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        if width != self.width or height != self.height:
            self.on_resize(width, height)

        # 100% true OLED pitch black
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        head_color = self.oled_color((1.0, 1.0, 1.0, 1.0), fade)
        accent_color = self.theme.accent
        primary_color = self.theme.primary

        # Render glyphs column by column
        layout = self.create_pango_layout(
            cr, " ", self.FONT_MONO, self.font_size, Pango.Weight.BOLD
        )

        for d in self.drops:
            x = d.col * self.col_width + (self.col_width * 0.1)
            head_row = int(d.y)

            # 1. Render glowing leading head glyph
            if 0 <= head_row * self.row_height <= height + 20:
                y = head_row * self.row_height
                layout.set_text(d.head_char, -1)
                
                # Subtle glow
                if d.depth > 0.6:
                    cr.set_source_rgba(*self.oled_color(with_alpha(accent_color, 0.35 * fade * d.depth)))
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        cr.move_to(x + dx, y + dy)
                        PangoCairo.show_layout(cr, layout)

                cr.set_source_rgba(*head_color)
                cr.move_to(x, y)
                PangoCairo.show_layout(cr, layout)

            # 2. Render trailing phosphorescent glyphs with decay
            tail_count = min(d.length, len(d.chars))
            for i in range(1, tail_count):
                row = head_row - i
                y = row * self.row_height
                if y < -20 or y > height + 20:
                    continue

                decay_ratio = 1.0 - (i / float(tail_count))
                char = d.chars[i % len(d.chars)]
                layout.set_text(char, -1)

                if i <= 2:
                    # Bright phosphor transition
                    glyph_c = self.oled_color(with_alpha(accent_color, decay_ratio * fade * d.depth))
                else:
                    # Deep green/primary phosphor fading into void
                    alpha = (decay_ratio ** 1.8) * 0.85 * fade * d.depth
                    glyph_c = self.oled_color(with_alpha(primary_color, alpha))

                cr.set_source_rgba(*glyph_c)
                cr.move_to(x, y)
                PangoCairo.show_layout(cr, layout)
