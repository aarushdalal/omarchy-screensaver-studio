"""Wallpaper background provider for Omarchy screensaver.
Generates and caches 12px Gaussian blur at 67% opacity over dark backdrop,
matching the visual architecture: wallpaper > 12px blur layer (67% opacity) > screensaver.
"""

import hashlib
import os
import time
from typing import Optional, Tuple
import cairo

try:
    from PIL import Image, ImageFilter, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class WallpaperManager:
    """Manages wallpaper detection, 12px Gaussian blur, 67% opacity blending, and caching."""

    CACHE_DIR = os.path.expanduser("~/.cache/omarchy-screensaver")
    DEFAULT_BLUR_RADIUS = 12
    DEFAULT_OPACITY = 0.67

    def __init__(self):
        self._cairo_cache = {}  # (w, h, mtime): cairo.ImageSurface
        self._gl_bytes_cache = {}  # (w, h, mtime): (bytes, w, h)
        self._gl_textures = {}  # (w, h, mtime): texture_id
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    @classmethod
    def get_wallpaper_path(cls) -> Optional[str]:
        """Detect current active desktop wallpaper path."""
        env_wp = os.environ.get("OMARCHY_WALLPAPER")
        if env_wp and os.path.exists(env_wp):
            return os.path.realpath(env_wp)

        candidates = [
            os.path.expanduser("~/.local/state/omarchy/current/background"),
            os.path.expanduser("~/.current-wallpaper"),
            os.path.expanduser("~/.cache/omarchy/lockscreen/background-blur.png"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return os.path.realpath(path)
        return None

    def get_cache_path(self, wp_path: str, width: int, height: int, mtime: float) -> str:
        h = hashlib.sha256(f"{wp_path}:{mtime}:{width}:{height}:r{self.DEFAULT_BLUR_RADIUS}:o{self.DEFAULT_OPACITY}".encode()).hexdigest()[:16]
        return os.path.join(self.CACHE_DIR, f"blur_{width}x{height}_{h}.png")

    def ensure_blurred_wallpaper(self, width: int, height: int) -> Optional[str]:
        """Ensure the blurred 12px / 67% opacity wallpaper PNG exists on disk and return path."""
        if not HAS_PIL or width <= 0 or height <= 0:
            return None

        wp_path = self.get_wallpaper_path()
        if not wp_path or not os.path.isfile(wp_path):
            return None

        try:
            mtime = os.path.getmtime(wp_path)
        except OSError:
            return None

        cache_path = self.get_cache_path(wp_path, width, height, mtime)
        if os.path.exists(cache_path):
            try:
                if os.path.getsize(cache_path) > 1000 and os.path.getmtime(cache_path) >= mtime:
                    return cache_path
            except OSError:
                pass

        # Generate blurred wallpaper
        try:
            with Image.open(wp_path) as raw:
                im = raw.convert("RGB")
            fitted = ImageOps.fit(im, (width, height), method=Image.Resampling.LANCZOS)
            blurred = fitted.filter(ImageFilter.GaussianBlur(radius=self.DEFAULT_BLUR_RADIUS))
            black = Image.new("RGB", (width, height), (0, 0, 0))
            blended = Image.blend(black, blurred, self.DEFAULT_OPACITY)

            temp_path = cache_path + f".tmp.{os.getpid()}"
            blended.save(temp_path, format="PNG", optimize=False)
            os.replace(temp_path, cache_path)
            return cache_path
        except Exception:
            return None

    def get_cairo_surface(self, width: int, height: int) -> Optional[cairo.ImageSurface]:
        """Return cached cairo.ImageSurface of the blurred wallpaper at exact monitor dimensions."""
        wp_path = self.get_wallpaper_path()
        if not wp_path:
            return None

        try:
            mtime = os.path.getmtime(wp_path)
        except OSError:
            mtime = 0.0

        key = (width, height, mtime)
        if key in self._cairo_cache:
            return self._cairo_cache[key]

        cache_path = self.ensure_blurred_wallpaper(width, height)
        if not cache_path:
            return None

        try:
            surf = cairo.ImageSurface.create_from_png(cache_path)
            # Evict old cached surfaces
            if len(self._cairo_cache) > 4:
                self._cairo_cache.clear()
            self._cairo_cache[key] = surf
            return surf
        except Exception:
            return None

    def draw_background(self, cr: cairo.Context, width: int, height: int, default_bg: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)):
        """Paint dark base and blurred wallpaper onto Cairo graphics context."""
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        # Always paint opaque base black so open applications never show through
        cr.set_source_rgba(default_bg[0], default_bg[1], default_bg[2], 1.0)
        cr.paint()

        surf = self.get_cairo_surface(width, height)
        if surf:
            cr.set_operator(cairo.OPERATOR_OVER)
            cr.set_source_surface(surf, 0, 0)
            cr.paint()
        cr.restore()

    def get_rgba_bytes(self, width: int, height: int, flip_y: bool = True) -> Optional[bytes]:
        """Return RGBA bytes for OpenGL/GLES texture uploading (vertically flipped for OpenGL UV origin)."""
        wp_path = self.get_wallpaper_path()
        if not wp_path:
            return None
        try:
            mtime = os.path.getmtime(wp_path)
        except OSError:
            mtime = 0.0

        key = (width, height, mtime, flip_y)
        if key in self._gl_bytes_cache:
            return self._gl_bytes_cache[key]

        cache_path = self.ensure_blurred_wallpaper(width, height)
        if not cache_path or not HAS_PIL:
            return None

        try:
            with Image.open(cache_path) as im:
                rgba = im.convert("RGBA")
                if flip_y:
                    rgba = rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                raw = rgba.tobytes("raw", "RGBA")
                if len(self._gl_bytes_cache) > 4:
                    self._gl_bytes_cache.clear()
                self._gl_bytes_cache[key] = raw
                return raw
        except Exception:
            return None


# Global singleton instance
wallpaper_manager = WallpaperManager()
