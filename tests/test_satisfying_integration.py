"""Integration test suite for DAEMON Satisfying and Screensaver Studio public release."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

EXPECTED_SATISFYING_MODES = [
    "harmonograph",
    "infinite_ripples",
    "the_perfect_machine",
    "ink_singularity",
    "zen_geometry",
    "fractal_bloom",
    "particle_architect",
    "harmonic_sculpture",
    "circuit_genesis",
    "circuit_weaver",
    "mechanical_eternity",
    "silk_continuum",
    "infinite_marble_machine",
    "domino_architect",
    "wave_field",
    "orbital_synchronization",
    "infinite_origami",
    "monolithic_construction",
    "midnight_rain",
    "liquid_obsidian",
    "mercury_garden",
    "event_horizon",
    "infinite_zen_garden",
    "ink_choreography",
]


class TestSatisfyingPublicIntegration(unittest.TestCase):
    """Verifies complete wiring and relocatability of 42 screensaver modes."""

    def test_catalog_contains_all_42_modes(self):
        from omarchy_screensaver.catalog import GROUPS, MODES

        self.assertIn("satisfying", GROUPS)
        self.assertEqual(len(MODES), 42)

        mode_keys = [m[0] for m in MODES]
        self.assertEqual(len(set(mode_keys)), 42)
        for expected in EXPECTED_SATISFYING_MODES:
            self.assertIn(expected, mode_keys)

    def test_available_modes_and_lazy_resolution(self):
        from omarchy_screensaver.modes import AVAILABLE_MODES, get_mode_class

        self.assertEqual(len(AVAILABLE_MODES), 42)
        for name in EXPECTED_SATISFYING_MODES:
            self.assertIn(name, AVAILABLE_MODES)
            cls = get_mode_class(name)
            self.assertTrue(getattr(cls, "is_gpu", False))
            self.assertEqual(getattr(cls, "effect_id", None), name)

    def test_preview_and_select_validators(self):
        # 1. Check select script VALID_MODES
        select_file = REPO_ROOT / "bin" / "omarchy-screensaver-select"
        self.assertTrue(select_file.exists())
        content = select_file.read_text(encoding="utf-8")
        for mode in EXPECTED_SATISFYING_MODES:
            self.assertIn(f'"{mode}"', content)

        # 2. Check preview script regex
        preview_file = REPO_ROOT / "bin" / "omarchy-screensaver-preview"
        self.assertTrue(preview_file.exists())
        p_content = preview_file.read_text(encoding="utf-8")
        for mode in EXPECTED_SATISFYING_MODES:
            self.assertIn(mode, p_content)

    def test_native_menu_json_extension(self):
        menu_file = REPO_ROOT / "omarchy-menu-extension.jsonc"
        self.assertTrue(menu_file.exists())
        raw = menu_file.read_text(encoding="utf-8")
        clean = re.sub(r"//.*", "", raw)
        data = json.loads(clean)

        self.assertIn("style.screensaver.modes", data)
        self.assertIn("style.screensaver.satisfying", data)
        self.assertIn("style.screensaver.satisfying.settings", data)

        for mode in EXPECTED_SATISFYING_MODES:
            key = f"style.screensaver.modes.{mode}"
            self.assertIn(key, data, f"Missing menu entry for {mode}")
            self.assertEqual(data[key]["action"], f"omarchy-screensaver-select mode {mode}")

    def test_preferences_defaults_and_validation(self):
        from daemon_satisfying.preferences import default_preset, validate_preset

        preset = default_preset()
        self.assertEqual(preset["version"], 1)
        self.assertEqual(preset["quality"], "balanced")
        self.assertEqual(len(preset["favorites"]), 0)
        self.assertTrue(validate_preset(preset))

    def test_deterministic_routing_planner(self):
        from daemon_satisfying.routing import plan_routes

        res1 = plan_routes(seed=42, node_count=8, obstacle_density=0.1, size=32)
        res2 = plan_routes(seed=42, node_count=8, obstacle_density=0.1, size=32)
        self.assertEqual(res1, res2)
        self.assertIn("paths", res1)
        self.assertIn("nodes", res1)

    def test_bridge_lifecycle_ordering(self):
        from daemon_satisfying.bridge import HarmonographMode

        mode = HarmonographMode(theme=None, config=None)
        call_order = []

        mock_surface = MagicMock()
        mock_surface.make_current.side_effect = lambda: call_order.append("make_current")
        mock_surface.get_realized.return_value = True

        mock_engine = MagicMock()
        mock_engine.close.side_effect = lambda: call_order.append("engine_close")
        mock_surface.engine = mock_engine

        mode.surface = mock_surface
        mode.close()

        self.assertEqual(call_order, ["make_current", "engine_close"])
        self.assertIsNone(mode.surface)
        self.assertIsNone(mock_surface.engine)

    def test_window_set_mode_resets_tick_clock(self):
        """set_mode must reset _last_tick_time to 0.0 to prevent huge dt upon mode switch."""
        from omarchy_screensaver.window import ScreensaverWindow

        mock_win = MagicMock(spec=ScreensaverWindow)
        mock_win.mode_name = "clock"
        mock_win._last_tick_time = 123456789.0
        mock_win.active_mode = MagicMock()
        mock_win.theme = None
        mock_win.config = None
        mock_win.monitor_index = 0
        mock_win.window_width = 1920
        mock_win.window_height = 1080

        # Invoke actual set_mode unbound method
        ScreensaverWindow.set_mode(mock_win, "harmonograph")

        self.assertEqual(mock_win.mode_name, "harmonograph")
        self.assertEqual(mock_win._last_tick_time, 0.0)

    def test_material_engine_resolution_capping(self):
        """liquid_obsidian and mercury_garden must bound material target resolution by profile caps."""
        from daemon_satisfying.gpu import Headless
        from daemon_satisfying.engine import Engine

        headless = Headless(128, 72, allow_software=True)
        try:
            # 4K resolution request on 'balanced' profile (cap 1280x720)
            engine = Engine(effect="liquid_obsidian", w=3840, h=2160, quality="balanced", seed=1, params={})
            try:
                self.assertEqual(engine.material_size, (1280, 720))
                self.assertIsNotNone(engine.material_target)
            finally:
                engine.close()
        finally:
            headless.close()


if __name__ == "__main__":
    unittest.main()
