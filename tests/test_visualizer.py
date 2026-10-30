"""Audio ownership, frequency coverage and visible signal-state regressions."""
import math
import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cairo
from omarchy_screensaver.audio import AudioEngine
from omarchy_screensaver.config import Config
from omarchy_screensaver.modes.visualizer import VisualizerMode
from omarchy_screensaver.mpris import MediaInfo, MprisClient
from omarchy_screensaver.theme import ThemePalette


class VisualizerRegression(unittest.TestCase):
    def mode(self, bands=None, signal=True):
        fake = SimpleNamespace(bands=bands or [0.6] * 36, has_signal=signal,
                               poll=lambda: None, update_spectrum=lambda *a: None)
        with patch('omarchy_screensaver.modes.visualizer.MprisClient', return_value=fake):
            mode = VisualizerMode(ThemePalette('test', {}), Config({'visualizer': {'fallback_mode': 'idle', 'bar_count': 36}}))
        return mode

    def test_desktop_audio_animates_without_player_metadata_and_silence_decays(self):
        mode = self.mode()
        mode.update(.1, None, None)
        self.assertTrue(mode.signal_active)
        self.assertGreater(mode.bass_energy, .4)
        previous = mode.peak_bands[0]
        mode.mpris.has_signal = False
        mode._fallback_mode = Mock()
        mode.update(.5, None, None)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
        mode.render(cairo.Context(surface), 640, 360, 1)
        mode._fallback_mode.render.assert_not_called()
        for _ in range(40):
            mode.update(.1, None, None)
        self.assertLess(max(mode.smooth_bands), .00001)
        self.assertLess(max(mode.peak_bands), .00001)
        self.assertGreater(previous, 0)
        mode.render(cairo.Context(surface), 640, 360, 1)
        mode._fallback_mode.render.assert_called_once()

    def test_bad_and_short_capture_buffers_do_not_leave_stale_bands(self):
        mode = self.mode([float('nan'), float('inf'), -2, 4, 'bad'])
        for _ in range(10):
            mode.update(.05, None, None)
        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1 for v in mode.smooth_bands))
        self.assertEqual(mode.smooth_bands[4:], [0] * 32)

    def test_peak_hold_and_envelopes_are_independent_of_frame_rate(self):
        modes = [self.mode(), self.mode()]
        for mode, fps in zip(modes, (30, 60)):
            for _ in range(fps):
                mode.update(1 / fps, None, None)
            mode.mpris.has_signal = False
            for _ in range(fps // 2):
                mode.update(1 / fps, None, None)
        self.assertAlmostEqual(modes[0].smooth_bands[0], modes[1].smooth_bands[0], places=6)
        self.assertAlmostEqual(modes[0].peak_bands[0], modes[1].peak_bands[0], delta=.02)

    def test_long_metadata_small_windows_and_both_palettes_render(self):
        mode = self.mode()
        state = random.getstate()
        self.mode()
        self.assertEqual(random.getstate(), state)
        info = MediaInfo(player='Example', title='A very long song title ' * 30,
                         artist='An artist ' * 20, album='Album ' * 30, is_playing=True)
        for palette in [ThemePalette('dark', {}), ThemePalette('light', {'mode': 'light'})]:
            mode.update_theme(palette)
            for width, height in [(640, 360), (900, 700), (1920, 1080)]:
                mode.on_resize(width, height)
                mode.update(.2, None, info)
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
                mode.render(cairo.Context(surface), width, height, 1)
                surface.flush()
                self.assertEqual(surface.status() if hasattr(surface, 'status') else 0, 0)

        # Live sound from another source must not inherit a paused track label
        # or delegate to the configured idle scene.
        mode._fallback_mode = Mock()
        mode.update(.1, None, MediaInfo(title='Old paused song', is_playing=False))
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
        with patch.object(mode, 'draw_text', wraps=mode.draw_text) as text:
            mode.render(cairo.Context(surface), 640, 360, 1)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertNotIn('Old paused song', labels)
        self.assertIn('Your sound, in motion', labels)
        mode._fallback_mode.render.assert_not_called()

    def test_native_worker_survives_releasing_one_of_two_listeners(self):
        library = Mock()
        library.audio_spectrum_start.return_value = 1
        def load(engine):
            engine._lib = library
            engine._worker_key = 'unit-test-worker'
        with patch.object(AudioEngine, '_load_library', load):
            one, two = AudioEngine(36), AudioEngine(64)
            try:
                self.assertTrue(one.start())
                self.assertTrue(two.start())
                library.audio_spectrum_start.assert_called_once_with(64)
                one.stop()
                library.audio_spectrum_stop.assert_not_called()
                two.stop()
                library.audio_spectrum_stop.assert_called_once()
            finally:
                one.stop(); two.stop()

    def test_every_resolution_includes_bass_and_treble_and_stays_in_buffer(self):
        def load(engine):
            engine._lib = Mock()
            engine._worker_key = 'unit-test-bounds'
            def read(bands, peaks, count):
                self.assertEqual(count, 64)
                for i in range(count):
                    bands[i] = peaks[i] = i / 63
                return 1
            engine._lib.audio_spectrum_get.side_effect = read
        with patch.object(AudioEngine, '_load_library', load):
            engine = AudioEngine(500)
            try:
                engine.start()
                for count in [8, 36, 40, 64, 500]:
                    values, _, signal = engine.get_spectrum(count)
                    self.assertTrue(signal)
                    self.assertEqual(len(values), min(count, 64))
                    self.assertEqual((values[0], values[-1]), (0, 1))
            finally:
                engine.stop()

    def test_no_player_poll_is_cached_as_well_as_playing_metadata(self):
        client = object.__new__(MprisClient)
        client._last_poll = 99.95
        client._cached_info = None
        client._bus = Mock()
        with patch('omarchy_screensaver.mpris.time.time', return_value=100):
            self.assertIsNone(client.poll())
        client._bus.list_names.assert_not_called()
