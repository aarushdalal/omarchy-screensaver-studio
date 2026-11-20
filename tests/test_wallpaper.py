"""Unit tests for wallpaper blur provider and caching."""

import os
import unittest
import cairo
from omarchy_screensaver.wallpaper import WallpaperManager


class TestWallpaperManager(unittest.TestCase):
    def setUp(self):
        self.wm = WallpaperManager()

    def test_wallpaper_detection_returns_valid_path_or_none(self):
        wp = self.wm.get_wallpaper_path()
        if wp is not None:
            self.assertTrue(os.path.exists(wp))

    def test_cache_path_is_deterministic(self):
        path1 = self.wm.get_cache_path("/path/to/wall.png", 1920, 1080, 123456.0)
        path2 = self.wm.get_cache_path("/path/to/wall.png", 1920, 1080, 123456.0)
        path3 = self.wm.get_cache_path("/path/to/wall.png", 1536, 864, 123456.0)
        self.assertEqual(path1, path2)
        self.assertNotEqual(path1, path3)
        self.assertIn("1920x1080", path1)

    def test_draw_background_paints_opaque_base(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        cr = cairo.Context(surface)
        self.wm.draw_background(cr, 100, 100, default_bg=(0.1, 0.2, 0.3, 1.0))
        surface.flush()
        pixel = int.from_bytes(surface.get_data()[:4], __import__('sys').byteorder)
        alpha = (pixel >> 24) & 255
        self.assertEqual(alpha, 255)

    def test_get_rgba_bytes_returns_bytes_when_wallpaper_present(self):
        wp = self.wm.get_wallpaper_path()
        if wp is not None:
            raw = self.wm.get_rgba_bytes(64, 64, flip_y=True)
            if raw is not None:
                self.assertEqual(len(raw), 64 * 64 * 4)

    def test_blur_generation_matches_lockscreen_without_black_blend(self):
        """Generated blur must not be dimmed by black blend, preserving image brightness."""
        from PIL import Image, ImageStat
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            test_img_path = f.name
        try:
            im = Image.new('RGB', (100, 100), (200, 200, 200))
            im.save(test_img_path)
            orig_get = self.wm.get_wallpaper_path
            orig_lock = self.wm.LOCKSCREEN_BLUR_PATH
            # Disable lockscreen path reuse for isolated generator test
            self.wm.LOCKSCREEN_BLUR_PATH = "/nonexistent/lockscreen/path.png"
            self.wm.get_wallpaper_path = lambda: test_img_path
            cache_file = self.wm.ensure_blurred_wallpaper(100, 100)
            self.assertIsNotNone(cache_file)
            self.assertTrue(os.path.exists(cache_file))
            with Image.open(cache_file) as res:
                stat = ImageStat.Stat(res)
                # Mean should remain close to 200, NOT dimmed by 33% black blend (~134)
                self.assertGreater(stat.mean[0], 180)
        finally:
            self.wm.get_wallpaper_path = orig_get
            self.wm.LOCKSCREEN_BLUR_PATH = orig_lock
            if os.path.exists(test_img_path):
                os.unlink(test_img_path)


if __name__ == '__main__':
    unittest.main()
