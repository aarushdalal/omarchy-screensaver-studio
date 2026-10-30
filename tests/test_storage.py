import datetime as dt
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from omarchy_screensaver.storage import DailyIOTracker, decode_nvme_attributes
from omarchy_screensaver.modes.system import SystemDashboardMode
from omarchy_screensaver.config import Config
from omarchy_screensaver.theme import ThemePalette
from omarchy_screensaver.metrics import SystemMetrics
import cairo


class StorageRegression(unittest.TestCase):
    def test_metrics_feed_daily_tracker_with_the_detected_device(self):
        with patch('omarchy_screensaver.storage.DailyIOTracker') as tracker:
            tracker.return_value.observe.return_value = {'read': 123, 'write': 456, 'partial': True}
            metrics = SystemMetrics()
            if not any(line.split()[2:3] == [metrics._primary_disk_dev.decode()] for line in Path('/proc/diskstats').read_text().splitlines()):
                self.skipTest('No detected disk counters on this host')
            tracker.return_value.observe.assert_called()
            self.assertEqual(metrics.disk_today_read_bytes, 123)

    def test_each_ring_sweeps_at_its_own_scheduled_time(self):
        metrics = SystemMetrics()
        mode = SystemDashboardMode(ThemePalette('test', {}), Config({}))
        mode.update(1, metrics, None)
        cr = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1200, 675))
        for index, (key, delay) in enumerate(mode.STARTUP_OFFSETS.items()):
            mode.time = mode.startup_delay + delay + 1
            with self.subTest(instrument=key), patch.object(mode, '_ring') as ring:
                mode.render(cr, 1200, 675, 1)
                self.assertEqual(len(ring.call_args_list), 7)
                self.assertEqual(ring.call_args_list[index].args[4], 100)
        mode.time = mode.startup_delay + .1
        self.assertGreater(mode.instrument_value(42, 'cpu'), 0)
        self.assertEqual(mode.instrument_value(42, 'gpu'), 0)
        self.assertEqual(mode.instrument_phase('gpu'), 'WAITING')
        mode.time = mode.startup_delay + 3.2
        self.assertEqual(mode.instrument_phase('cpu'), 'LIVE')
        self.assertEqual(mode.instrument_phase('battery'), 'CHECK')
        self.assertFalse(mode.startup_complete)
        mode.time = mode.startup_delay + 5.5
        self.assertTrue(mode.startup_complete)
        for key in mode.STARTUP_OFFSETS:
            self.assertAlmostEqual(mode.instrument_value(42, key), 42)

    def test_daily_deltas_survive_reopen_and_reboot_without_double_counting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'daily.json'
            tracker = DailyIOTracker(path, interval=0)
            now = dt.datetime(2026, 10, 30, 12, 0, tzinfo=dt.timezone.utc)
            boot = now - dt.timedelta(hours=3)
            one = tracker.observe('nvme0n1', 100, 200, now, 'boot-a', boot)
            self.assertEqual((one['read'], one['write']), (100, 200))
            two = DailyIOTracker(path, interval=0).observe('nvme0n1', 150, 280, now + dt.timedelta(seconds=1), 'boot-a', boot)
            self.assertEqual((two['read'], two['write']), (150, 280))
            three = tracker.observe('nvme0n1', 20, 30, now + dt.timedelta(hours=1), 'boot-b', now + dt.timedelta(minutes=50))
            self.assertEqual((three['read'], three['write']), (170, 310))

    def test_day_change_does_not_attribute_multiple_days_of_counter_growth_to_today(self):
        with tempfile.TemporaryDirectory() as directory:
            tracker = DailyIOTracker(Path(directory) / 'daily.json', interval=0)
            now = dt.datetime(2026, 10, 30, 12, 0, tzinfo=dt.timezone.utc)
            boot = now - dt.timedelta(days=2)
            one = tracker.observe('nvme0n1', 1000, 2000, now, 'a', boot)
            self.assertEqual(one['read'], 0)
            two = tracker.observe('nvme0n1', 5000, 6000, now + dt.timedelta(days=1), 'a', boot)
            self.assertEqual((two['read'], two['write']), (0, 0))
            self.assertTrue(two['partial'])

    def test_smart_health_is_wear_estimate_and_missing_commands_stay_unknown(self):
        result = decode_nvme_attributes({'percent_used': 19, 'total_data_read': 100, 'total_data_written': 200})
        self.assertEqual(result['health_percent'], 81)
        self.assertEqual(result['read_bytes'], 100)
        self.assertIsNone(result['read_commands'])
        self.assertEqual(decode_nvme_attributes({'percent_used': 120})['health_percent'], 0)

    def test_instrument_check_revs_to_full_back_to_zero_then_hands_over(self):
        mode = SystemDashboardMode(ThemePalette('test', {}), Config({}))
        for stamp, expected in [(0, 0), (.9, 100), (1.1, 100), (2.1, 0), (2.3, 0), (3.2, 42)]:
            with self.subTest(time=stamp):
                mode.time = mode.startup_delay + stamp
                self.assertAlmostEqual(mode.instrument_value(42), expected)


if __name__ == '__main__':
    unittest.main()
