"""Rendering and integration regressions; run with system Python (PyGObject)."""
import math
import random
import unittest
import ast
import tempfile
import json
import os
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch
import cairo
from omarchy_screensaver.catalog import MODES
from omarchy_screensaver.config import Config
from omarchy_screensaver.metrics import SystemMetrics
from omarchy_screensaver.modes import AVAILABLE_MODES, create_mode
from omarchy_screensaver.theme import ThemePalette
from omarchy_screensaver.window import ScreensaverWindow

AMBIENT = ['eclipse', 'ink_flow', 'rain', 'cyber_nexus', 'topography', 'quantum_helix', 'celestial_orbit']


class StudioRegression(unittest.TestCase):
    def setUp(self):
        self.config = Config({})
        self.metrics = SystemMetrics()
        self.theme = ThemePalette('test', {'background': '#000000', 'accent': '#7d9b91', 'secondary': '#a8b4bd'})

    def test_catalogue_covers_every_renderable_mode_once(self):
        self.assertEqual(len(MODES), len(AVAILABLE_MODES))
        self.assertEqual({row[0] for row in MODES}, set(AVAILABLE_MODES))

    def test_native_and_daemonos_menu_return_formats(self):
        from omarchy_screensaver.browser import choose
        row = ('☾', 'Eclipse', 'A quiet solar corona', 'eclipse')
        for response in ['Eclipse', 'Eclipse\tA quiet solar corona', '☾\tEclipse']:
            with self.subTest(response=response), patch('omarchy_screensaver.browser.subprocess.run',
                    return_value=SimpleNamespace(returncode=0, stdout=response)):
                self.assertEqual(choose('Test', [row]), 'eclipse')

    def test_preview_ignores_pointer_motion_but_idle_saver_still_dismisses(self):
        app = Mock()
        window = SimpleNamespace(is_preview=True, is_ambient=False, config=self.config,
                                 _initial_mouse_pos=(0, 0), get_application=lambda: app)
        ScreensaverWindow._on_mouse_motion(window, None, 500, 500)
        app.dismiss.assert_not_called()
        window.is_preview = False
        ScreensaverWindow._on_mouse_motion(window, None, 500, 500)
        app.dismiss.assert_called_once()

    def test_escape_closes_the_studio_without_reopening_parent_pages(self):
        from omarchy_screensaver.browser import choose, MenuCancelled
        with patch('omarchy_screensaver.browser.subprocess.run',
                   return_value=SimpleNamespace(returncode=1, stdout='')):
            with self.assertRaises(MenuCancelled):
                choose('Eclipse', [('☾', 'Preview', 'Try this mode', 'preview')])

    def test_showcase_fallback_uses_registry_instead_of_recording_helper_modules(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / 'bin/record-showcase').read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'discover_modes')
        namespace = {'run_cmd': lambda args: SimpleNamespace(returncode=1, stdout=''),
                     'get_modes_dir': lambda: root / 'omarchy_screensaver/modes'}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<recorder>', 'exec'), namespace)
        modes = namespace['discover_modes']()
        self.assertEqual(set(modes), set(AVAILABLE_MODES))
        self.assertNotIn('studio', modes)

    def test_collection_selection_applies_directly_with_no_confirmation_page(self):
        from omarchy_screensaver.browser import browse
        with patch('omarchy_screensaver.browser.choose', return_value='eclipse') as choose, \
             patch('omarchy_screensaver.browser.run', return_value=0) as run:
            self.assertTrue(browse('quiet'))
            choose.assert_called_once()
            run.assert_called_once_with('omarchy-screensaver-select', 'mode', 'eclipse')

    def test_successful_selection_closes_browser_instead_of_reopening_home(self):
        from omarchy_screensaver.browser import main
        with patch('omarchy_screensaver.browser.sys.argv', ['browser']), \
             patch('omarchy_screensaver.browser.choose', return_value='mode:eclipse') as choose, \
             patch('omarchy_screensaver.browser.run', return_value=0) as run:
            main()
            choose.assert_called_once()
            run.assert_called_once_with('omarchy-screensaver-select', 'mode', 'eclipse')
            rows = choose.call_args.args[1]
            self.assertEqual({row[3][5:] for row in rows if row[3].startswith('mode:')}, set(AVAILABLE_MODES))

    def test_running_windows_receive_new_selection_theme_and_rotation(self):
        from omarchy_screensaver.app import ScreensaverApp
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.toml'
            path.write_text('[general]\nmode="ink_flow"\ntheme="aurora"\nrotation=true\n')
            old = Config({'general': {'mode': 'clock', 'theme': 'auto'}})
            window = Mock()
            app = SimpleNamespace(config=old, _config_signature=None, windows=[window],
                selected_mode='clock', current_mode='clock', forced_mode=None, is_preview=False,
                _saved_mode_before_audio='geometry', _saved_mode_before_visualizer_toggle='system',
                log=Mock(), switch_mode=Mock(), _configure_rotation_timer=Mock(),
                _get_config_signature=ScreensaverApp._get_config_signature)
            with patch.object(Config, 'CONFIG_FILE', str(path)), \
                 patch('omarchy_screensaver.app.ThemeManager', return_value=SimpleNamespace(palette=self.theme)):
                ScreensaverApp._reload_config_if_changed(app)
                app.switch_mode.assert_called_once_with('ink_flow')
                window.set_theme.assert_called_once_with(self.theme)
                window.close.assert_not_called()
                self.assertEqual(window.active_mode.config.mode, 'ink_flow')
                self.assertIsNone(app._saved_mode_before_audio)
                self.assertIsNone(app._saved_mode_before_visualizer_toggle)
                app._configure_rotation_timer.assert_called_once()
                # Half-written edits must not reset the running mode or palette.
                path.write_text('[general]\nmode=')
                ScreensaverApp._reload_config_if_changed(app)
                self.assertEqual(app.selected_mode, 'ink_flow')
                app.switch_mode.assert_called_once()

    def test_reselecting_saved_mode_restores_it_after_temporary_visualizer_toggle(self):
        from omarchy_screensaver.app import ScreensaverApp
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.toml'
            path.write_text('[general]\nmode="clock"\ntheme="auto"\n')
            old = Config({'general': {'mode': 'clock', 'theme': 'auto'}})
            app = SimpleNamespace(config=old, _config_signature=None, windows=[],
                selected_mode='clock', current_mode='visualizer', forced_mode=None, is_preview=False,
                log=Mock(), switch_mode=Mock(), _configure_rotation_timer=Mock(),
                _get_config_signature=ScreensaverApp._get_config_signature)
            with patch.object(Config, 'CONFIG_FILE', str(path)):
                ScreensaverApp._reload_config_if_changed(app)
            app.switch_mode.assert_called_once_with('clock')

    def test_all_modes_redraw_when_the_desktop_palette_changes(self):
        first = ThemePalette('warm', {'background': '#000000', 'accent': '#c26c42',
                                     'secondary': '#d5a874', 'foreground': '#d8c5a0'})
        second = ThemePalette('cool', {'background': '#000000', 'accent': '#42b4c2',
                                      'secondary': '#7494d5', 'foreground': '#a0c5d8'})
        for name in AVAILABLE_MODES:
            with self.subTest(mode=name):
                mode = create_mode(name, first, self.config)
                mode.on_resize(640, 360)
                for _ in range(90):
                    mode.update(1 / 30, self.metrics, None)
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
                cr = cairo.Context(surface)
                mode.render(cr, 640, 360, 0.5)
                before = bytes(surface.get_data())
                mode.update_theme(second)
                mode.render(cr, 640, 360, 0.5)
                self.assertNotEqual(hashlib.sha256(before).hexdigest(),
                                    hashlib.sha256(surface.get_data()).hexdigest())

    def test_daemonos_auto_palette_reads_colours_and_tracks_scheme_changes(self):
        from omarchy_screensaver.theme import ThemeManager
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scheme.json'
            data = {'name': 'test', 'mode': 'dark', 'colours': {'primary': '#123456', 'secondary': '456789'}}
            path.write_text(json.dumps(data))
            with patch.object(ThemeManager, 'CAELESTIA_SCHEME_FILE', str(path)), \
                 patch('subprocess.run', return_value=SimpleNamespace(returncode=0)):
                manager = ThemeManager('auto')
                self.assertEqual(manager.palette.hex_accent, '#123456')
                before = path.stat().st_mtime_ns
                data['colours']['primary'] = '779944'
                path.write_text(json.dumps(data))
                os.utime(path, ns=(before + 1000000000, before + 1000000000))
                self.assertTrue(manager.check_for_updates())
                self.assertEqual(manager.palette.hex_accent, '#779944')

    def test_actual_window_allocation_notifies_mode_and_uses_logical_scale(self):
        mode = Mock()
        window = SimpleNamespace(window_width=0, window_height=0, active_mode=mode,
                                 is_preview=False, is_debug=False)
        cr = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1536, 864))
        ScreensaverWindow._on_draw(window, None, cr, 1536, 864)
        mode.on_resize.assert_called_once_with(1536, 864)
        self.assertAlmostEqual(mode.render.call_args.args[-1], 0.8)
        ScreensaverWindow._on_draw(window, None, cr, 1536, 864)
        mode.on_resize.assert_called_once()
        ScreensaverWindow._on_draw(window, None, cr, 1200, 675)
        self.assertEqual(mode.on_resize.call_args.args, (1200, 675))

    def test_ambient_modes_do_not_reseed_global_randomness(self):
        for name in AMBIENT:
            with self.subTest(mode=name):
                random.seed(298); before = random.getstate()
                create_mode(name, self.theme, self.config, 2)
                self.assertEqual(before, random.getstate())

    def test_changed_modes_render_after_resize_and_long_idle_in_both_palettes(self):
        for light in (False, True):
            theme = self.theme if not light else ThemePalette('light', {'mode': 'light', 'background': '#e8e7e4', 'accent': '#334943'})
            for name in AMBIENT + ['clock', 'system', 'visualizer', 'synthwave']:
                mode = create_mode(name, theme, self.config)
                for width, height in [(1200, 675), (640, 360), (1920, 1080), (1536, 864)]:
                    with self.subTest(mode=name, light=light, size=(width, height)):
                        mode.on_resize(width, height)
                        mode.update(600, self.metrics, None)
                        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
                        mode.render(cairo.Context(surface), width, height, min(width / 1920, height / 1080))
                        self.assertEqual(surface.status() if hasattr(surface, 'status') else 0, 0)

    def test_circuit_population_stays_bounded_across_resizes_and_suspend(self):
        mode = create_mode('cyber_nexus', self.theme, self.config)
        for width, height in [(640, 360), (3840, 2160), (1200, 675)]:
            mode.on_resize(width, height)
            for dt in [1 / 30] * 500 + [3600, 0, 1 / 30]:
                mode.update(dt, self.metrics, None)
            self.assertEqual(len(mode.packets), 18)
            for u, v, progress, speed in mode.packets:
                self.assertIn(v, mode.adjacency[u])
                self.assertTrue(math.isfinite(progress) and 0 <= progress < 1)

    def test_long_media_title_fits_and_next_text_does_not_inherit_constraint(self):
        mode = create_mode('clock', self.theme, self.config)
        cr = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360))
        w, _ = mode.draw_text(cr, 'An unusually long title ' * 30, 320, 150, mode.FONT_SANS, 32,
                              self.theme.foreground, max_width=480)
        self.assertLessEqual(w, 480)
        w2, _ = mode.draw_text(cr, 'Short', 320, 200, mode.FONT_SANS, 12, self.theme.foreground)
        self.assertLess(w2, 150)


if __name__ == '__main__':
    unittest.main()
