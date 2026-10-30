"""Aurora Flow: a readable, theme-aware stage for the live desktop spectrum."""
import math
import random
from typing import Optional

import cairo
from gi.repository import Pango

from ..mpris import MediaInfo, MprisClient
from ..theme import with_alpha
from .base import BaseMode
from .studio import smooth_path


class VisualizerMode(BaseMode):
    """Measured spectrum and peak caps, framed by quiet decorative ribbons."""
    CANVAS = (1600, 1000)

    def __init__(self, theme, config, monitor_index=0):
        super().__init__(theme, config, monitor_index)
        self.width, self.height = self.CANVAS
        self.bar_count = max(8, min(64, int(getattr(config, 'visualizer_bar_count', 36))))
        self.mpris = MprisClient(bar_count=self.bar_count)
        self.media_info: Optional[MediaInfo] = None
        self.target_fps = 30
        self.fade_in = 0.0
        self.smooth_bands = [0.0] * self.bar_count
        self.peak_bands = [0.0] * self.bar_count
        self._peak_holds = [0.0] * self.bar_count
        self.bass_energy = self.mid_energy = self.treble_energy = 0.0
        self.signal_active = False
        self._idle_time = 0.0
        rng = random.Random(1337 + monitor_index * 99)
        self.stardust = [(rng.random(), rng.random(), rng.uniform(.6, 1.6),
                         rng.uniform(0, math.tau)) for _ in range(28)]
        self._fallback_mode = None
        fallback = str(getattr(config, 'visualizer_fallback_mode', 'selected')).lower()
        if fallback not in ('selected', 'auto', 'idle', 'visualizer', ''):
            from . import create_mode
            self._fallback_mode = create_mode(fallback, theme, config, monitor_index)

    def update_theme(self, theme):
        super().update_theme(theme)
        if self._fallback_mode:
            self._fallback_mode.update_theme(theme)

    def on_resize(self, width, height):
        if width > 0 and height > 0:
            self.width, self.height = width, height
        if self._fallback_mode:
            self._fallback_mode.on_resize(width, height)

    @staticmethod
    def _level(value):
        """Discard bad capture samples before they can poison the animation."""
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(1.0, max(0.0, value)) if math.isfinite(value) else 0.0

    def update(self, dt, metrics, media_info):
        dt = max(0.0, dt)
        super().update(dt, metrics, media_info)
        self.media_info = media_info if media_info is not None else self.mpris.poll()
        playing = bool(self.media_info and self.media_info.is_playing)
        self.mpris.update_spectrum(dt, playing)
        self.signal_active = bool(self.mpris.has_signal)
        self._idle_time = 0.0 if self.signal_active or playing else self._idle_time + dt
        self.target_fps = 55 if self.signal_active or playing else 30
        self.fade_in = min(1, self.fade_in + dt * 1.8)
        raw = self.mpris.bands
        # Time-based envelopes stay consistent across frame rates and suspend.
        for i in range(self.bar_count):
            sample = self._level(raw[i]) if self.signal_active and i < len(raw) else 0.0
            target = sample ** .90
            rate = 36 if target > self.smooth_bands[i] else 7
            self.smooth_bands[i] += (target - self.smooth_bands[i]) * (1 - math.exp(-dt * rate))
            value = self.smooth_bands[i]
            if value >= self.peak_bands[i]:
                self.peak_bands[i] = value
                self._peak_holds[i] = .22
            else:
                falling = max(0.0, dt - self._peak_holds[i])
                self._peak_holds[i] = max(0.0, self._peak_holds[i] - dt)
                self.peak_bands[i] = max(value, self.peak_bands[i] - falling * .55)
        # Three equal regions of the logarithmic spectrum, not calibrated VU/dB.
        edges = (0, self.bar_count // 3, 2 * self.bar_count // 3, self.bar_count)
        energies = [sum(self.smooth_bands[a:b]) / (b - a) for a, b in zip(edges, edges[1:])]
        self.bass_energy, self.mid_energy, self.treble_energy = energies
        if self._idle_time >= 1.2 and not playing and not self.signal_active and self._fallback_mode:
            self._fallback_mode.update(dt, metrics, self.media_info)

    def _text(self, cr, text, x, y, size=12, color=None, alpha=1, align='left', width=None, bold=False):
        return self.draw_text(cr, text, x, y, self.FONT_SANS if size >= 20 else self.FONT_MONO,
                              size, with_alpha(color or self.theme.foreground, alpha * self.fade_in),
                              align=align, max_width=width,
                              weight=Pango.Weight.BOLD if bold else Pango.Weight.NORMAL)

    def _ribbons(self, cr, fade):
        """Decorative silk responds to actual bands; idle motion is not a meter."""
        cr.save()
        cr.rectangle(64, 360, 1472, 450); cr.clip()
        for layer, (color, energy) in enumerate(zip(
                (self.theme.accent, self.theme.secondary, self.theme.dark_accent),
                (self.bass_energy, self.mid_energy, self.treble_energy))):
            points = []
            for i in range(65):
                u = i / 64
                index = u * (self.bar_count - 1)
                a = int(index); b = min(a + 1, self.bar_count - 1)
                band = self.smooth_bands[a] * (1 - (index - a)) + self.smooth_bands[b] * (index - a)
                envelope = math.sin(math.pi * u) ** .8
                wave = math.sin(u * 7.5 + self.time * (.38 + layer * .12) + layer * 1.5)
                wave += .42 * math.cos(u * 15 - self.time * .25 + layer)
                y = 618 + layer * 32 + envelope * (wave * (20 + energy * 50) - band * 70)
                points.append((64 + u * 1472, y))
            smooth_path(cr, points)
            cr.line_to(1536, 810); cr.line_to(64, 810); cr.close_path()
            gradient = cairo.LinearGradient(0, 495, 0, 810)
            gradient.add_color_stop_rgba(0, *with_alpha(color, .12 * fade))
            gradient.add_color_stop_rgba(1, *with_alpha(color, 0))
            cr.set_source(gradient); cr.fill()
            smooth_path(cr, points)
            cr.set_source_rgba(*with_alpha(color, (.18 + energy * .13) * fade))
            cr.set_line_width(1.4); cr.stroke()
        cr.restore()

    def _spectrum(self, cr, fade):
        left, width, baseline, height = 184, 1232, 742, 272
        cell = width / self.bar_count
        bar_w = min(17, cell * .50)
        # A quiet baseline makes the direction of the frequency axis obvious.
        line = cairo.LinearGradient(left, 0, left + width, 0)
        for stop, alpha in ((0, 0), (.1, .28), (.9, .28), (1, 0)):
            line.add_color_stop_rgba(stop, *with_alpha(self.theme.accent, alpha * fade))
        cr.set_source(line); cr.set_line_width(1)
        cr.move_to(left, baseline); cr.line_to(left + width, baseline); cr.stroke()
        for i, (value, peak) in enumerate(zip(self.smooth_bands, self.peak_bands)):
            x = left + cell * (i + .5)
            bar_h = value * height
            top = baseline - bar_h
            if bar_h > .4:
                self.draw_rounded_rect(cr, x - bar_w / 2, top, bar_w, max(1, bar_h), min(3, bar_h / 2))
                color = self.theme.accent if i < self.bar_count // 2 else self.theme.secondary
                gradient = cairo.LinearGradient(0, top, 0, baseline)
                gradient.add_color_stop_rgba(0, *with_alpha(color, .88 * fade))
                gradient.add_color_stop_rgba(.55, *with_alpha(color, .52 * fade))
                gradient.add_color_stop_rgba(1, *with_alpha(color, .10 * fade))
                cr.set_source(gradient); cr.fill()
                # A slender crest gives transients definition without a solid wall.
                cr.move_to(x - bar_w / 2, top); cr.line_to(x + bar_w / 2, top)
                cr.set_source_rgba(*with_alpha(self.theme.foreground, .62 * fade))
                cr.set_line_width(1.4); cr.stroke()
                if getattr(self.config, 'visualizer_mirrored', True):
                    reflection = min(44, bar_h * .17)
                    gradient = cairo.LinearGradient(0, baseline + 4, 0, baseline + 4 + reflection)
                    gradient.add_color_stop_rgba(0, *with_alpha(color, .18 * fade))
                    gradient.add_color_stop_rgba(1, *with_alpha(color, 0))
                    cr.rectangle(x - bar_w / 2, baseline + 4, bar_w, reflection)
                    cr.set_source(gradient); cr.fill()
            if peak > .025:
                py = baseline - peak * height - 7
                cr.move_to(x - bar_w / 2, py); cr.line_to(x + bar_w / 2, py)
                cr.set_source_rgba(*with_alpha(self.theme.foreground, .42 * fade))
                cr.set_line_width(1.1); cr.stroke()
        for x, label in ((left, 'LOW END'), (800, 'MIDRANGE'), (left + width, 'HIGH END')):
            self._text(cr, label, x, 803, 10, self.theme.dark_foreground, .72 * fade,
                       align='left' if x == left else 'right' if x > 800 else 'center')

    def render(self, cr, width, height, scale):
        playing = bool(self.media_info and self.media_info.is_playing)
        if self._idle_time >= 1.2 and not playing and not self.signal_active and self._fallback_mode:
            self._fallback_mode.render(cr, width, height, scale)
            return
        self.clear_background(cr, width, height)
        s = min(width / 1600, height / 1000)
        if s <= 0:
            return
        cr.save()
        cr.translate((width - 1600 * s) / 2 + (self.burn_x + self.jitter_x) * .15 * s,
                     (height - 1000 * s) / 2 + (self.burn_y + self.jitter_y) * .15 * s)
        cr.scale(s, s)
        fade = self.luminance_factor if self.theme.is_dark else 1
        opacity = self.fade_in * fade
        accent, secondary = self.theme.accent, self.theme.secondary
        # Light stays behind the music, leaving clear space around track type.
        glow = cairo.RadialGradient(800, 610, 0, 800, 610, 670)
        glow.add_color_stop_rgba(0, *with_alpha(accent, (.035 + self.bass_energy * .07) * opacity))
        glow.add_color_stop_rgba(1, *with_alpha(accent, 0))
        cr.set_source(glow); cr.paint()
        self._text(cr, 'AURORA FLOW', 96, 72, 15, accent, fade, bold=True)
        status = 'LIVE AUDIO' if self.signal_active else 'SILENT PASSAGE' if playing else 'PAUSED' if self.media_info and self.media_info.title else 'LISTENING'
        self._text(cr, status, 1504, 72, 11, self.theme.dark_foreground, fade, 'right')
        cr.arc(1330, 72, 3, 0, math.tau)
        cr.set_source_rgba(*with_alpha(accent, (.55 + .25 * math.sin(self.time * 2)) * opacity)); cr.fill()
        has_media = bool(self.media_info and self.media_info.title and (playing or not self.signal_active))
        player = (self.media_info.player or 'Media player') if has_media else 'DESKTOP AUDIO'
        self._text(cr, player.upper(), 800, 178, 11, secondary, fade, 'center', width=1120)
        title = self.media_info.title if has_media else 'Your sound, in motion' if self.signal_active else 'Ready when you are'
        self._text(cr, title, 800, 235, 34, alpha=fade, align='center', width=1240, bold=True)
        if has_media:
            artist = self.media_info.artist
            album = self.media_info.album
            subtitle = '  ·  '.join(part for part in (artist, album) if part)
        else:
            subtitle = 'Listening to your desktop audio' if self.signal_active else 'Play something to bring the spectrum to life'
        self._text(cr, subtitle, 800, 294, 17, self.theme.dark_foreground, fade, 'center', width=1180)
        if getattr(self.config, 'visualizer_particles', True):
            for x, y, radius, phase in self.stardust:
                px = 96 + (x * 1408 + math.sin(self.time * .09 + phase) * 15) % 1408
                py = 380 + ((y * 370 - self.time * (2 + radius)) % 370)
                cr.arc(px, py, radius, 0, math.tau)
                cr.set_source_rgba(*with_alpha(secondary, (.12 + .07 * math.sin(phase + self.time * .5)) * opacity)); cr.fill()
        if getattr(self.config, 'visualizer_wave_ribbon', True):
            self._ribbons(cr, opacity)
        self._spectrum(cr, opacity)
        # These meters show relative band activity, not fabricated loudness units.
        for i, (name, energy) in enumerate(zip(('LOW', 'MID', 'HIGH'),
                (self.bass_energy, self.mid_energy, self.treble_energy))):
            x = 184 + i * 432
            self.draw_rounded_rect(cr, x, 854, 368, 68, 12)
            cr.set_source_rgba(*with_alpha(self.theme.surface, .42 * opacity)); cr.fill_preserve()
            cr.set_source_rgba(*with_alpha(accent, .13 * opacity)); cr.set_line_width(1); cr.stroke()
            self._text(cr, name, x + 18, 875, 10, self.theme.dark_foreground, fade)
            self._text(cr, 'BAND ACTIVITY', x + 350, 875, 8.5, self.theme.dark_foreground, .65 * fade, 'right')
            cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_width(3)
            cr.move_to(x + 20, 899); cr.line_to(x + 348, 899)
            cr.set_source_rgba(*with_alpha(accent, .13 * opacity)); cr.stroke()
            if energy > .001:
                cr.move_to(x + 20, 899); cr.line_to(x + 20 + 328 * energy, 899)
                cr.set_source_rgba(*with_alpha(secondary if i == 1 else accent, .7 * opacity)); cr.stroke()
        footer = 'LIVE SPECTRUM  ·  PEAK HOLD & SOFT RELEASE' if self.signal_active else 'QUIET AMBIENCE  ·  WAITING FOR SOUND'
        self._text(cr, footer, 800, 963, 9, self.theme.dark_foreground, .6 * fade, 'center')
        cr.restore()
