"""Mode 5: Minimalist Aurora Flow Audio Visualizer.

A clean, zen, hyper-satisfying audio visualizer featuring:
  - Undulating multi-harmonic Aurora Borealis liquid silk ribbons modulated by real-time audio frequencies
  - Ethereal chromatic dispersion between primary, secondary, and accent theme palettes
  - Generous vertical spacing ensuring zero typography overlap across all screen resolutions
  - Clean minimalist frequency lines (no clunky balls or radar clutter)
  - Drifting ambient stardust motes floating through the aurora curtains
  - Pure #000000 true-black OLED subpixel shutoff and Lissajous burn-in drift
  - Lag-free, butter-smooth 60 FPS rendering
"""

import math
import random
from typing import List, Optional

import cairo
from gi.repository import Pango

from ..metrics import SystemMetrics
from ..mpris import MediaInfo, MprisClient
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class AuroraStardust:
    """Drifting ambient stardust mote floating through the aurora night sky."""
    __slots__ = ("x", "y", "size", "alpha", "speed_y", "phase", "color_idx")

    def __init__(self, x: float, y: float, size: float, alpha: float, speed_y: float, phase: float, color_idx: int):
        self.x = x
        self.y = y
        self.size = size
        self.alpha = alpha
        self.speed_y = speed_y
        self.phase = phase
        self.color_idx = color_idx


class VisualizerMode(BaseMode):
    """Clean minimalist Aurora Flow audio visualizer."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.width: float = 1920.0
        self.height: float = 1080.0
        self.bar_count: int = getattr(self.config, "visualizer_bar_count", 36)
        self.mpris = MprisClient(bar_count=self.bar_count)
        self.media_info: Optional[MediaInfo] = None
        self.fade_in: float = 0.0
        self.target_fps: int = 60

        # Smoothed audio frequency buffers for fluid liquid interpolation
        self.smooth_bands = [0.0] * self.bar_count
        self.bass_energy: float = 0.0
        self.mid_energy: float = 0.0
        self.treble_energy: float = 0.0

        # Ambient stardust particles
        self.stardust: List[AuroraStardust] = []
        self._init_stardust(36)

        # Dynamic fallback delegate if configured
        self._fallback_mode: Optional[BaseMode] = None
        self._setup_fallback()

    def _init_stardust(self, count: int):
        random.seed(1337 + self.monitor_index * 99)
        self.stardust.clear()
        for _ in range(count):
            self.stardust.append(AuroraStardust(
                x=random.random(),
                y=random.random(),
                size=random.uniform(1.2, 2.6),
                alpha=random.uniform(0.20, 0.65),
                speed_y=random.uniform(6.0, 18.0),
                phase=random.uniform(0.0, math.pi * 2.0),
                color_idx=random.randint(0, 2),
            ))

    def _setup_fallback(self):
        fallback_name = getattr(self.config, "visualizer_fallback_mode", "selected").lower()
        if fallback_name in ("selected", "auto", "idle", "visualizer", ""):
            self._fallback_mode = None
        elif fallback_name == "clock":
            from .clock import ClockMode
            self._fallback_mode = ClockMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "matrix":
            from .matrix import MatrixMode
            self._fallback_mode = MatrixMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "particles":
            from .particles import ParticlesMode
            self._fallback_mode = ParticlesMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "warp":
            from .warp import WarpMode
            self._fallback_mode = WarpMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "geometry":
            from .geometry import GeometryMode
            self._fallback_mode = GeometryMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "singularity":
            from .singularity import SingularityMode
            self._fallback_mode = SingularityMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "aurora":
            from .aurora import AuroraMode
            self._fallback_mode = AuroraMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "system":
            from .system import SystemMode
            self._fallback_mode = SystemMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "terminal":
            from .terminal import TerminalMode
            self._fallback_mode = TerminalMode(self.theme, self.config, self.monitor_index)

    def update_theme(self, theme: ThemePalette):
        super().update_theme(theme)
        if self._fallback_mode:
            self._fallback_mode.update_theme(theme)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.width = float(width)
        self.height = float(height)
        if self._fallback_mode:
            self._fallback_mode.on_resize(width, height)

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.media_info = media_info or self.mpris.poll()

        is_playing = bool(self.media_info and self.media_info.is_playing)
        self.target_fps = 55 if is_playing else 30
        self.mpris.update_spectrum(dt, is_playing)

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 2.0)

        raw_bands = self.mpris.bands
        n = min(len(raw_bands), self.bar_count)

        # Smooth frequency interpolation with high audio sensitivity
        attack_rate = min(1.0, dt * 28.0)
        decay_rate = min(1.0, dt * 8.5)

        for i in range(n):
            raw = raw_bands[i]
            # Dynamic perceptual sensitivity boost curve (makes bars jump higher and react to subtle beats)
            target = min(1.0, math.pow(max(0.0, raw * 1.45), 0.72))
            if target > self.smooth_bands[i]:
                self.smooth_bands[i] += (target - self.smooth_bands[i]) * attack_rate
            else:
                self.smooth_bands[i] += (target - self.smooth_bands[i]) * decay_rate

        # Calculate frequency sub-band energies
        b_count = max(1, n // 4)
        m_count = max(1, n // 2)
        self.bass_energy = sum(self.smooth_bands[:b_count]) / b_count if n > 0 else 0.0
        self.mid_energy = sum(self.smooth_bands[b_count:m_count]) / max(1, m_count - b_count) if n > 0 else 0.0
        self.treble_energy = sum(self.smooth_bands[m_count:]) / max(1, n - m_count) if n > 0 else 0.0

        # Update drifting stardust motes with gentle Brownian sway
        for s in self.stardust:
            s.y = (s.y - (s.speed_y * dt) / max(1.0, self.height)) % 1.0
            s.x = (s.x + math.sin(self.time * 0.6 + s.phase) * (14.0 * dt) / max(1.0, self.width)) % 1.0
            s.phase += dt * 1.8

        if not is_playing and self._fallback_mode:
            self._fallback_mode.update(dt, metrics, self.media_info)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        is_playing = bool(self.media_info and self.media_info.is_playing)
        has_media = bool(self.media_info and self.media_info.title)

        # If user explicitly requested delegation to another mode when idle
        if not is_playing and self._fallback_mode:
            self._fallback_mode.render(cr, width, height, scale)
            self.draw_text(
                cr, "󰎈  MEDIA STREAM IDLE", width * 0.5, height - 36.0,
                self.FONT_MONO, 11.0, with_alpha(self.theme.muted, 0.6),
                align="center"
            )
            return

        # True OLED pure #000000 true black clear
        self.clear_background(cr, width, height)

        fade = self.fade_in * self.luminance_factor
        w, h = float(width), float(height)

        cx = w * 0.5 + self.burn_x + self.jitter_x
        # Typography positioned gracefully in the upper 28% to prevent ANY overlap with the aurora waves
        cy_text = h * 0.28 + self.burn_y + self.jitter_y

        title = self.media_info.title if has_media else "Awaiting Audio Stream"
        artist = self.media_info.artist if has_media else "PipeWire · PulseAudio · MPRIS"
        album = self.media_info.album if has_media else ""
        player = self.media_info.player if self.media_info else "SOUNDSCAPE"

        # -------------------------------------------------------------
        # 1. Ambient Background Acoustic Aurora Glow
        # -------------------------------------------------------------
        glow_alpha = (0.12 + self.bass_energy * 0.14) * fade if is_playing else 0.08 * fade
        glow_pat = cairo.RadialGradient(cx, h * 0.62, 10, cx, h * 0.62, w * 0.50)
        glow_pat.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(self.theme.accent, glow_alpha)))
        glow_pat.add_color_stop_rgba(0.55, *self.oled_color(with_alpha(self.theme.dark_accent, glow_alpha * 0.55)))
        glow_pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(glow_pat)
        cr.paint()

        # -------------------------------------------------------------
        # 2. Ambient Drifting Stardust Motes
        # -------------------------------------------------------------
        stardust_colors = [self.theme.accent, self.theme.secondary, self.theme.dark_accent]
        for s in self.stardust:
            sx = s.x * w
            sy = s.y * h
            pulse = 0.65 + 0.35 * math.sin(s.phase)
            c = stardust_colors[s.color_idx % len(stardust_colors)]
            cr.set_source_rgba(*self.oled_color(with_alpha(c, s.alpha * pulse * fade)))
            cr.arc(sx, sy, s.size, 0, math.pi * 2)
            cr.fill()

        # -------------------------------------------------------------
        # 3. Undulating Multi-Harmonic Aurora Flow Ribbons
        # -------------------------------------------------------------
        # 3 harmonic aurora curtains traversing across the screen with rich darker theme depth
        t = self.time
        aurora_layers = [
            # (color, alpha, speed, freq, y_ratio, amp_boost, energy_source)
            (self.theme.accent, 0.28, 0.40, 1.2, 0.66, 130.0, self.bass_energy),
            (self.theme.secondary, 0.22, 0.65, 1.8, 0.58, 100.0, self.mid_energy),
            (self.theme.dark_accent, 0.20, 0.90, 2.4, 0.52, 80.0, self.treble_energy),
        ]

        for color, alpha, speed, freq, y_ratio, amp_boost, energy in aurora_layers:
            self._render_aurora_ribbon(
                cr, w, h, t * speed, freq, h * y_ratio, amp_boost, energy, color, alpha * fade, is_playing
            )

        # -------------------------------------------------------------
        # 4. Clean Minimalist Frequency Horizon Lines (No Balls / Clutter)
        # -------------------------------------------------------------
        self._render_minimal_spectrum(cr, cx, w, h, fade, is_playing)

        # -------------------------------------------------------------
        # 5. Clean, Minimalist Typography (Ample Breathing Room)
        # -------------------------------------------------------------
        # Status Pill
        if is_playing:
            badge_str = f"󰎈  {player.upper()}  ·  PLAYING"
            badge_color = self.oled_color(with_alpha(self.theme.accent, fade * 0.90))
        elif has_media:
            badge_str = f"󰏤  {player.upper()}  ·  PAUSED"
            badge_color = self.oled_color(with_alpha(self.theme.muted, fade * 0.85))
        else:
            badge_str = "󰎈  OMARCHY AURORA FLOW  ·  IDLE"
            badge_color = self.oled_color(with_alpha(self.theme.dark_accent, fade * 0.70))

        self.draw_text(
            cr, badge_str, cx, cy_text - 40.0,
            self.FONT_MONO, 12.0, badge_color,
            align="center", weight=Pango.Weight.BOLD
        )

        # Track Title
        title_color = self.oled_color(with_alpha(self.theme.foreground, fade * 0.95))
        self.draw_text(
            cr, title, cx, cy_text,
            self.FONT_SANS, 32.0, title_color,
            align="center", weight=Pango.Weight.BOLD, glow=is_playing
        )

        # Artist & Album
        artist_album = f"{artist}   —   {album}" if album else artist
        self.draw_text(
            cr, artist_album, cx, cy_text + 38.0,
            self.FONT_SANS, 15.0, self.oled_color(with_alpha(self.theme.dark_foreground, fade * (0.85 if is_playing else 0.60))),
            align="center", weight=Pango.Weight.NORMAL
        )

    def _render_aurora_ribbon(
        self,
        cr: cairo.Context,
        w: float,
        h: float,
        t: float,
        freq: float,
        base_y: float,
        amp_boost: float,
        energy: float,
        color: tuple,
        alpha: float,
        is_playing: bool,
    ):
        """Renders a single fluid, continuous Aurora Borealis curtain."""
        cr.save()

        num_steps = 28
        step_w = w / (num_steps - 1)
        points = []

        # Real-time wave modulation using audio frequency energy
        amp = (25.0 + energy * amp_boost) if is_playing else 18.0

        for i in range(num_steps):
            x = i * step_w
            u = i / (num_steps - 1)

            # Sample audio band corresponding to horizontal position
            b_idx = int(u * (len(self.smooth_bands) - 1))
            band_val = self.smooth_bands[b_idx] if self.smooth_bands else 0.0

            # Smooth multi-octave harmonic undulation
            wave = (
                math.sin(t * 1.2 + u * freq * 3.8) * amp
                + math.cos(t * 0.7 - u * 2.4) * (amp * 0.55)
                + math.sin(t * 2.2 + u * 6.5) * (amp * 0.25)
                - band_val * amp_boost * 0.85
            )
            y = base_y + wave
            points.append((x, y))

        # 1. Fill flowing translucent aurora curtain to bottom
        cr.move_to(0, h)
        cr.line_to(points[0][0], points[0][1])

        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            mid_x = (p0[0] + p1[0]) * 0.5
            mid_y = (p0[1] + p1[1]) * 0.5
            cr.curve_to(p0[0], p0[1], p0[0], p0[1], mid_x, mid_y)
        cr.line_to(points[-1][0], points[-1][1])
        cr.line_to(w, h)
        cr.close_path()

        curtain_grad = cairo.LinearGradient(0, base_y - amp * 1.5, 0, h)
        curtain_grad.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
        curtain_grad.add_color_stop_rgba(0.20, *self.oled_color(with_alpha(color, alpha * 0.95)))
        curtain_grad.add_color_stop_rgba(0.55, *self.oled_color(with_alpha(self.theme.dark_accent, alpha * 0.45)))
        curtain_grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(curtain_grad)
        cr.fill()

        # 2. Glowing crest laser thread along top edge of aurora ribbon
        cr.set_line_width(2.0)
        cr.set_source_rgba(*self.oled_color(with_alpha(color, alpha * 1.25)))
        cr.move_to(points[0][0], points[0][1])
        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            mid_x = (p0[0] + p1[0]) * 0.5
            mid_y = (p0[1] + p1[1]) * 0.5
            cr.curve_to(p0[0], p0[1], p0[0], p0[1], mid_x, mid_y)
        cr.line_to(points[-1][0], points[-1][1])
        cr.stroke()

        cr.restore()

    def _render_minimal_spectrum(self, cr: cairo.Context, cx: float, w: float, h: float, fade: float, is_playing: bool):
        """Renders sleek, clean minimalist frequency lines without balls or visual clutter."""
        cr.save()

        bands = self.smooth_bands
        n_bars = len(bands)
        if n_bars == 0:
            cr.restore()
            return

        vis_w = min(920.0, w * 0.82)
        base_y = h * 0.83
        # Expressive dynamic height: bars can rise up to 250px tall
        max_h = min(250.0, h * 0.28)

        bar_gap = 5.0
        bar_w = max(3.0, (vis_w - (n_bars - 1) * bar_gap) / n_bars)
        start_x = cx - vis_w * 0.5

        # Thin glowing horizon line in deep theme colors
        cr.set_line_width(1.4)
        h_pat = cairo.LinearGradient(start_x, base_y, start_x + vis_w, base_y)
        h_pat.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
        h_pat.add_color_stop_rgba(0.20, *self.oled_color(with_alpha(self.theme.dark_accent, 0.35 * fade)))
        h_pat.add_color_stop_rgba(0.50, *self.oled_color(with_alpha(self.theme.accent, 0.75 * fade)))
        h_pat.add_color_stop_rgba(0.80, *self.oled_color(with_alpha(self.theme.dark_accent, 0.35 * fade)))
        h_pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(h_pat)
        cr.move_to(start_x, base_y)
        cr.line_to(start_x + vis_w, base_y)
        cr.stroke()

        # Clean vertical frequency lines with darker, richer theme palette
        for i in range(n_bars):
            bx = start_x + i * (bar_w + bar_gap)
            val = bands[i]
            bar_height = max(4.0, val * max_h)
            by = base_y - bar_height

            # Upper line
            self.draw_rounded_rect(cr, bx, by, bar_w, bar_height, bar_w * 0.45)
            grad = cairo.LinearGradient(bx, by, bx, base_y)
            if is_playing:
                # Flow from rich signature accent at peak, through deep secondary, to darker accent/muted at base
                grad.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(self.theme.accent, 0.95 * fade)))
                grad.add_color_stop_rgba(0.35, *self.oled_color(with_alpha(self.theme.secondary, 0.85 * fade)))
                grad.add_color_stop_rgba(0.70, *self.oled_color(with_alpha(self.theme.dark_accent, 0.75 * fade)))
                grad.add_color_stop_rgba(1.0, *self.oled_color(with_alpha(self.theme.muted, 0.45 * fade)))
            else:
                grad.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(self.theme.dark_accent, 0.40 * fade)))
                grad.add_color_stop_rgba(1.0, *self.oled_color(with_alpha(self.theme.muted, 0.10 * fade)))
            cr.set_source(grad)
            cr.fill()

            # Subtle mirrored reflection downwards into OLED true black
            refl_h = bar_height * 0.35
            self.draw_rounded_rect(cr, bx, base_y + 2.0, bar_w, refl_h, bar_w * 0.45)
            refl_grad = cairo.LinearGradient(bx, base_y + 2.0, bx, base_y + 2.0 + refl_h)
            refl_grad.add_color_stop_rgba(0.0, *self.oled_color(with_alpha(self.theme.dark_accent, 0.40 * fade)))
            refl_grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(refl_grad)
            cr.fill()

        cr.restore()
