"""Pixel regressions for background-only translucency, without desktop windows."""
import unittest
import cairo
from omarchy_screensaver.config import Config
from omarchy_screensaver.modes.base import BaseMode
from omarchy_screensaver.theme import ThemePalette


def alpha(surface, x=0, y=0):
    surface.flush()
    pixel = int.from_bytes(surface.get_data()[y * surface.get_stride() + x * 4:y * surface.get_stride() + x * 4 + 4], __import__('sys').byteorder)
    return (pixel >> 24) & 255


class BackgroundGlass(unittest.TestCase):
    def make_mode(self, opacity=None, oled=True):
        display = {'oled_mode': oled}
        if opacity is not None:
            display['background_opacity'] = opacity
        return BaseMode(ThemePalette('test', {'background':'#172333'}), Config({'display':display}))

    def test_native_background_replaces_opaque_pixels_and_keeps_foreground_solid(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 16, 16)
        cr = cairo.Context(surface)
        cr.set_source_rgb(0, 0, 0); cr.paint()
        self.make_mode(.74).clear_background(cr, 16, 16)
        self.assertAlmostEqual(alpha(surface), 255 * .74, delta=1)
        cr.set_source_rgba(1, 1, 1, 1); cr.rectangle(4, 4, 4, 4); cr.fill()
        self.assertEqual(alpha(surface, 5, 5), 255)
        self.assertAlmostEqual(alpha(surface, 0, 0), 255 * .74, delta=1)

    def test_repeated_frames_do_not_accumulate_to_black_or_leave_old_content(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 16, 16)
        cr = cairo.Context(surface); mode = self.make_mode(.74)
        for _ in range(30):
            cr.set_source_rgba(1, 1, 1, 1); cr.paint()
            mode.clear_background(cr, 16, 16)
            self.assertAlmostEqual(alpha(surface), 255 * .74, delta=1)
            self.assertEqual(cr.get_operator(), cairo.OPERATOR_OVER)

    def test_default_opaque_oled_and_explicit_background_alpha_remain_supported(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4); cr = cairo.Context(surface)
        self.make_mode().clear_background(cr, 4, 4)
        self.assertEqual(alpha(surface), 255)
        self.make_mode(.5, oled=False).clear_background(cr, 4, 4, custom_bg=(.1, .2, .3, .6))
        self.assertAlmostEqual(alpha(surface), 255 * .5 * .6, delta=1)

    def test_background_setting_is_bounded(self):
        self.assertEqual(self.make_mode(2).config.background_opacity, 1)
        self.assertEqual(self.make_mode(-1).config.background_opacity, 0)


if __name__ == '__main__':
    unittest.main()
