"""Mode 5: Music Visualizer.

Integrates with real-time PipeWire/PulseAudio spectrum capture (<10ms beat latency)
and MPRIS media players via DBus. Renders glowing song title, artist, album,
and a physics-driven spectrum audio frequency visualizer with peak hold.
"""

import math
from typing import Optional

import cairo
from gi.repository import Pango

from ..metrics import SystemMetrics
from ..mpris import MediaInfo, MprisClient
from ..theme import ThemePalette, with_alpha
from .base import BaseMode


class VisualizerMode(BaseMode):
    """Audio visualizer screensaver mode."""

    def __init__(self, theme: ThemePalette, config, monitor_index: int = 0):
        super().__init__(theme, config, monitor_index)
        self.bar_count = self.config.visualizer_bar_count
        self.mpris = MprisClient(bar_count=self.bar_count)
        self.media_info: Optional[MediaInfo] = None
        self.fade_in = 0.0
        self.target_fps = 60  # Full 60 FPS for responsive beat rendering

        # Dynamic fallback delegate if configured
        self._fallback_mode: Optional[BaseMode] = None
        self._setup_fallback()

    def _setup_fallback(self):
        fallback_name = getattr(self.config, "visualizer_fallback_mode", "idle").lower()
        if fallback_name in ("selected", "auto", "idle", "visualizer", ""):
            self._fallback_mode = None
        elif fallback_name == "clock":
            from .clock import ClockMode
            self._fallback_mode = ClockMode(self.theme, self.config, self.monitor_index)
        elif fallback_name == "particles":
            from .particles import ParticlesMode
            self._fallback_mode = ParticlesMode(self.theme, self.config, self.monitor_index)
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
        if self._fallback_mode:
            self._fallback_mode.on_resize(width, height)

    def update(self, dt: float, metrics: SystemMetrics, media_info: Optional[MediaInfo]):
        super().update(dt, metrics, media_info)
        self.media_info = media_info or self.mpris.poll()

        is_playing = bool(self.media_info and self.media_info.is_playing)
        self.mpris.update_spectrum(dt, is_playing)

        if self.fade_in < 1.0:
            self.fade_in = min(1.0, self.fade_in + dt * 2.0)

        if not is_playing and self._fallback_mode:
            self._fallback_mode.update(dt, metrics, self.media_info)

    def render(self, cr: cairo.Context, width: int, height: int, scale: float):
        is_playing = bool(self.media_info and self.media_info.is_playing)
        has_media = bool(self.media_info and self.media_info.title)

        # If user explicitly requested delegation to another mode when idle
        if not is_playing and self._fallback_mode:
            self._fallback_mode.render(cr, width, height, scale)
            self.draw_text(
                cr, "󰎈  MEDIA PLAYER IDLE", width * 0.5, height - 36.0,
                self.FONT_MONO, 11.0, with_alpha(self.theme.muted, 0.6),
                align="center"
            )
            return

        self.clear_background(cr, width, height)

        fade = self.fade_in
        cx = width * 0.5 + self.burn_x
        cy = height * 0.45 + self.burn_y

        title = self.media_info.title if has_media else "Awaiting Audio Stream"
        artist = self.media_info.artist if has_media else "Omarchy Soundscape"
        album = self.media_info.album if has_media else ""
        player = self.media_info.player if self.media_info else "AUDIO"

        # Ambient central glow
        glow_pat = cairo.RadialGradient(cx, cy, 20, cx, cy, width * 0.45)
        if is_playing:
            glow_pat.add_color_stop_rgba(0.0, *with_alpha(self.theme.primary, 0.16 * fade))
        else:
            glow_pat.add_color_stop_rgba(0.0, *with_alpha(self.theme.muted, 0.08 * fade))
        glow_pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(glow_pat)
        cr.paint()

        # 1. Player Status Badge
        if is_playing:
            badge_str = f"󰎈  {player.upper()}  •  PLAYING"
            badge_color = with_alpha(self.theme.accent, fade * 0.95)
        elif has_media:
            badge_str = f"󰏤  {player.upper()}  •  PAUSED"
            badge_color = with_alpha(self.theme.warning, fade * 0.85)
        else:
            badge_str = "󰎈  OMARCHY VISUALIZER  •  IDLE"
            badge_color = with_alpha(self.theme.muted, fade * 0.75)

        self.draw_text(
            cr, badge_str, cx, cy - 140.0,
            self.FONT_MONO, 12.0, badge_color,
            align="center", weight=Pango.Weight.BOLD
        )

        # 2. Song Title (Large, glowing when playing)
        title_color = (
            with_alpha(self.theme.bright_foreground, fade)
            if is_playing
            else with_alpha(self.theme.foreground, fade * 0.85)
        )
        self.draw_text(
            cr, title, cx, cy - 85.0,
            self.FONT_SANS, 34.0, title_color,
            align="center", weight=Pango.Weight.BOLD, glow=is_playing
        )

        # 3. Artist & Album
        artist_album = f"{artist}   —   {album}" if album else artist
        self.draw_text(
            cr, artist_album, cx, cy - 40.0,
            self.FONT_SANS, 16.0, with_alpha(self.theme.foreground, fade * (0.85 if is_playing else 0.65)),
            align="center", weight=Pango.Weight.NORMAL
        )

        # 4. Audio Spectrum Equalizer
        bands = self.mpris.bands
        peaks = self.mpris.peaks
        n_bars = len(bands)

        vis_w = min(850.0, width * 0.80)
        vis_h = 160.0
        bar_gap = 4.0
        bar_w = (vis_w - (n_bars - 1) * bar_gap) / max(1, n_bars)
        start_x = cx - vis_w * 0.5
        base_y = cy + 130.0

        for i in range(n_bars):
            bx = start_x + i * (bar_w + bar_gap)
            val = bands[i]
            bar_height = max(4.0, val * vis_h)
            by = base_y - bar_height

            # Draw bar with vertical gradient
            self.draw_rounded_rect(cr, bx, by, bar_w, bar_height, bar_w * 0.35)
            grad = cairo.LinearGradient(bx, by, bx, base_y)
            if is_playing:
                grad.add_color_stop_rgba(0.0, *with_alpha(self.theme.secondary, 0.95 * fade))
                grad.add_color_stop_rgba(0.55, *with_alpha(self.theme.primary, 0.85 * fade))
                grad.add_color_stop_rgba(1.0, *with_alpha(self.theme.accent, 0.40 * fade))
            else:
                grad.add_color_stop_rgba(0.0, *with_alpha(self.theme.primary, 0.40 * fade))
                grad.add_color_stop_rgba(1.0, *with_alpha(self.theme.muted, 0.15 * fade))
            cr.set_source(grad)
            cr.fill()

            # Floating peak dot (only during active playback)
            peak_val = peaks[i]
            if is_playing and peak_val > 0.05:
                peak_y = base_y - peak_val * vis_h - 5.0
                if peak_y < base_y:
                    cr.set_source_rgba(*with_alpha(self.theme.bright_foreground, 0.92 * fade))
                    cr.arc(bx + bar_w * 0.5, peak_y, bar_w * 0.42, 0, math.pi * 2)
                    cr.fill()

        # Baseline reflection rule
        rule_y = base_y + 8.0
        cr.set_source_rgba(*with_alpha(self.theme.primary, 0.3 * fade))
        cr.set_line_width(1.0)
        cr.move_to(start_x, rule_y)
        cr.line_to(start_x + vis_w, rule_y)
        cr.stroke()
