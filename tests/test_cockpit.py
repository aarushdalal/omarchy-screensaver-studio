"""Measured telemetry and instrument-state regressions for the system cockpit."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from omarchy_screensaver.metrics import SystemMetrics
from omarchy_screensaver.modes.system import SystemDashboardMode
from omarchy_screensaver.config import Config
from omarchy_screensaver.theme import ThemePalette
import cairo


class CockpitRegression(unittest.TestCase):
    def test_per_core_usage_uses_deltas_and_counts_iowait_as_idle(self):
        metrics = SimpleNamespace(_last_per_core={})
        SystemMetrics._update_per_core(metrics, [b'cpu0 10 0 10 70 10 0 0 0', b'cpu1 0 0 10 90 0 0 0 0'])
        SystemMetrics._update_per_core(metrics, [b'cpu0 20 0 30 130 20 0 0 0', b'cpu1 0 0 10 190 0 0 0 0'])
        self.assertAlmostEqual(metrics.cpu_per_core[0], 30.0)
        self.assertAlmostEqual(metrics.cpu_per_core[1], 0.0)
        # CPU hotplug and reset counters do not yield negative or stale bars.
        SystemMetrics._update_per_core(metrics, [b'cpu2 1 0 2 97 0 0 0 0'])
        self.assertEqual(metrics.cpu_per_core, [0])
        self.assertEqual(set(metrics._last_per_core), {b'cpu2'})

    def test_pressure_is_avg10_some_not_full_or_total(self):
        self.assertEqual(SystemMetrics._parse_pressure('some avg10=4.20 avg60=9.0 total=12345\nfull avg10=2.0'), 4.2)
        self.assertIsNone(SystemMetrics._parse_pressure('full avg10=2.0 total=1234'))
        self.assertIsNone(SystemMetrics._parse_pressure('some avg10=nan'))

    def test_peak_marker_holds_then_decays_toward_live_value(self):
        theme = ThemePalette('test', {'background': '#000000', 'accent': '#66887a'})
        mode = SystemDashboardMode(theme, Config({}))
        metrics = SystemMetrics()
        metrics.cpu_percent = 80
        mode.update(2, metrics, None)
        peak = mode.peaks['cpu'][0]
        metrics.cpu_percent = 10
        mode.update(1, metrics, None)
        self.assertAlmostEqual(mode.peaks['cpu'][0], peak)
        mode.update(4, metrics, None)
        self.assertLess(mode.peaks['cpu'][0], peak)
        self.assertGreaterEqual(mode.peaks['cpu'][0], mode.values['cpu'])

    def test_missing_sensors_are_labelled_unavailable_and_estimates_are_explicit(self):
        metrics = SystemMetrics()
        metrics.cpu_temp_valid = False
        metrics.has_gpu = False
        metrics.has_battery = False
        metrics.pressure_cpu = metrics.pressure_memory = metrics.pressure_io = None
        mode = SystemDashboardMode(ThemePalette('test', {'accent': '#66887a'}), Config({}))
        mode.update(2, metrics, None)
        cr = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1200, 675))
        text = []
        original = mode._text
        def capture(cr, value, *args, **kwargs):
            text.append(value)
            return original(cr, value, *args, **kwargs)
        with patch.object(mode, '_text', side_effect=capture):
            mode.render(cr, 1200, 675, 1)
        self.assertIn('Sensor unavailable', text)
        self.assertIn('No supported GPU sensor', text)
        self.assertIn('CPU est.', text)
        self.assertIn('No battery installed', text)
        self.assertIn('CPU — · MEM — · IO —', text)


if __name__ == '__main__':
    unittest.main()
