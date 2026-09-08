"""Screensaver window implementation using GTK4, Cairo, and Wayland.
"""

import math
import time
from typing import Optional, Tuple

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk, Pango

from .metrics import SystemMetrics
from .modes import BaseMode, create_mode
from .mpris import MediaInfo
from .theme import ThemePalette, with_alpha


class ScreensaverWindow(Gtk.ApplicationWindow):
    """Fullscreen screensaver window covering a specific display monitor."""

    def __init__(
        self,
        app: Gtk.Application,
        monitor: Gdk.Monitor,
        monitor_index: int,
        config,
        theme: ThemePalette,
        mode_name: str,
        is_preview: bool = False,
        is_debug: bool = False,
        is_ambient: bool = False,
    ):
        super().__init__(application=app)
        self.monitor = monitor
        self.monitor_index = monitor_index
        self.config = config
        self.theme = theme
        self.mode_name = mode_name
        self.is_preview = is_preview
        self.is_debug = is_debug
        self.is_ambient = is_ambient

        self.active_mode: BaseMode = create_mode(mode_name, theme, config, monitor_index)

        # Mouse motion threshold tracking
        self._initial_mouse_pos: Optional[Tuple[float, float]] = None

        # Timing and FPS tracking
        self._last_tick_time: float = 0.0
        self._frame_count: int = 0
        self._fps_accumulator_time: float = 0.0
        self.live_fps: float = 60.0
        self.current_scale: float = 1.0
        self.window_width: int = 1920
        self.window_height: int = 1080

        self._setup_window()
        self._setup_drawing_area()
        self._setup_input_controllers()

    def _setup_window(self):
        self.set_title(f"Omarchy Screensaver (Monitor {self.monitor_index})")
        self.fullscreen_on_monitor(self.monitor)

        # Hide cursor completely
        try:
            cursor = Gdk.Cursor.new_from_name("none", None)
            self.set_cursor(cursor)
        except Exception:
            pass

    def _setup_drawing_area(self):
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self._on_draw)
        self.drawing_area.add_tick_callback(self._on_tick)
        self.set_child(self.drawing_area)

    def _setup_input_controllers(self):
        # Keyboard Controller
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

        # Mouse Motion Controller
        motion_ctrl = Gtk.EventControllerMotion.new()
        motion_ctrl.connect("motion", self._on_mouse_motion)
        self.add_controller(motion_ctrl)

        # Mouse Click Controller
        click_ctrl = Gtk.GestureClick.new()
        click_ctrl.connect("pressed", self._on_mouse_click)
        self.add_controller(click_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if self.is_preview:
            # ESC or any key dismisses preview
            self.get_application().dismiss()
            return True

        if self.is_ambient:
            # In ambient study mode: NO key press closes it (only shortcut can toggle it off)
            if getattr(self.config, "ambient_exit_on_key_press", False):
                self.get_application().dismiss()
                return True
            return False

        # Filter out standalone modifier keys (Super, Ctrl, Alt, Shift, etc.)
        MODIFIER_KEYVALS = {
            Gdk.KEY_Super_L, Gdk.KEY_Super_R,
            Gdk.KEY_Control_L, Gdk.KEY_Control_R,
            Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
            Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
            Gdk.KEY_Caps_Lock, Gdk.KEY_Num_Lock,
            Gdk.KEY_ISO_Level3_Shift, Gdk.KEY_Meta_L, Gdk.KEY_Meta_R,
        }
        if keyval in MODIFIER_KEYVALS:
            return False

        # If Super, Control, or Alt is held down, pass through to compositor for global shortcuts
        modifier_mask = (
            Gdk.ModifierType.SUPER_MASK
            | Gdk.ModifierType.CONTROL_MASK
            | Gdk.ModifierType.ALT_MASK
        )
        if bool(state & modifier_mask):
            return False

        # In regular screensaver mode: ESC, q, or any key press dismisses
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q) or self.config.exit_on_key_press:
            self.get_application().dismiss()
            return True

        return False

    def _on_mouse_motion(self, controller, x, y):
        if self.is_ambient and not getattr(self.config, "ambient_exit_on_mouse_move", False):
            return

        if self._initial_mouse_pos is None:
            self._initial_mouse_pos = (x, y)
            return

        if not self.config.exit_on_mouse_move:
            return

        threshold = (
            self.config.ambient_mouse_move_threshold
            if self.is_ambient
            else self.config.mouse_move_threshold
        )
        x0, y0 = self._initial_mouse_pos
        dist = math.hypot(x - x0, y - y0)

        # Dismiss if movement exceeds threshold
        if dist >= threshold:
            self.get_application().dismiss()

    def _on_mouse_click(self, gesture, n_press, x, y):
        if self.is_ambient and not getattr(self.config, "ambient_exit_on_mouse_click", False):
            return

        self.get_application().dismiss()

    def set_mode(self, mode_name: str):
        """Switch visual mode."""
        if mode_name != self.mode_name:
            self.mode_name = mode_name
            self.active_mode = create_mode(mode_name, self.theme, self.config, self.monitor_index)
            self.active_mode.on_resize(self.window_width, self.window_height)

    def set_theme(self, theme: ThemePalette):
        """Update active theme palette."""
        self.theme = theme
        if self.active_mode:
            self.active_mode.update_theme(theme)

    def _on_tick(self, area: Gtk.DrawingArea, clock) -> bool:
        now = time.time()
        if self._last_tick_time == 0.0:
            self._last_tick_time = now
            return GLib.SOURCE_CONTINUE

        dt = now - self._last_tick_time

        # Target frame rate regulation (mode-adaptive + battery throttling)
        app = self.get_application()
        mode_fps = getattr(self.active_mode, "target_fps", self.config.fps)
        target_fps = min(float(self.config.fps), float(mode_fps))
        if app and app.metrics and not app.metrics.ac_online and self.config.battery_reduce_fps:
            target_fps = min(target_fps, float(self.config.battery_fps))

        frame_budget = 1.0 / target_fps
        if dt < frame_budget * 0.92:
            # Yield frame to maintain target FPS and save CPU
            return GLib.SOURCE_CONTINUE

        self._last_tick_time = now

        # Compute live FPS
        self._frame_count += 1
        self._fps_accumulator_time += dt
        if self._fps_accumulator_time >= 0.5:
            self.live_fps = self._frame_count / self._fps_accumulator_time
            self._frame_count = 0
            self._fps_accumulator_time = 0.0

        # Update mode physics and state
        metrics = app.metrics if app else None
        media = app.media_info if app else None

        self.active_mode.update(dt, metrics, media)
        self.drawing_area.queue_draw()

        return GLib.SOURCE_CONTINUE

    def _on_draw(self, area: Gtk.DrawingArea, cr: cairo.Context, width: int, height: int):
        self.window_width = width
        self.window_height = height
        scale = float(self.get_scale_factor())
        self.current_scale = scale

        # Render active screensaver mode
        self.active_mode.render(cr, width, height, scale)

        # Preview Banner
        if self.is_preview:
            banner_alpha = max(0.0, 1.0 - (self.active_mode.time / 4.0))
            if banner_alpha > 0.05:
                banner_text = "OMARCHY SCREENSAVER  •  PREVIEW MODE  [PRESS ANY KEY OR ESC TO EXIT]"
                self.active_mode.draw_text(
                    cr, banner_text, width * 0.5, 32.0,
                    BaseMode.FONT_MONO, 11.0,
                    with_alpha(self.theme.accent, banner_alpha * 0.9),
                    align="center", weight=Pango.Weight.BOLD, glow=True
                )

        # Diagnostics HUD for --debug
        if self.is_debug:
            self._render_debug_hud(cr, width, height)

    def _render_debug_hud(self, cr: cairo.Context, width: int, height: int):
        app = self.get_application()
        m = app.metrics if app else None

        hud_w = 340.0
        hud_h = 245.0
        hx = 24.0
        hy = 24.0

        # Background card
        self.active_mode.draw_rounded_rect(cr, hx, hy, hud_w, hud_h, 8.0)
        cr.set_source_rgba(0.04, 0.06, 0.08, 0.88)
        cr.fill_preserve()
        cr.set_source_rgba(*with_alpha(self.theme.primary, 0.6))
        cr.set_line_width(1.0)
        cr.stroke()

        pad_x = hx + 16.0
        cur_y = hy + 20.0
        line_h = 19.0

        self.active_mode.draw_text(
            cr, "OMARCHY SCREENSAVER DEBUG", pad_x, cur_y,
            BaseMode.FONT_MONO, 11.0, self.theme.accent, align="left", weight=Pango.Weight.BOLD
        )
        cur_y += line_h * 1.2

        cpu_val = f"{m.cpu_percent:.1f}%" if m else "N/A"
        mem_val = f"{m.mem_used_gib:.1f} / {m.mem_total_gib:.1f} GiB" if m else "N/A"
        power_val = f"{'AC Connected' if (m and m.ac_online) else 'Battery'} ({m.battery_percent}%)" if m else "N/A"

        debug_lines = [
            ("Renderer", "GTK4 / Cairo (GPU Vector Engine)"),
            ("Backend", "Wayland (Hyprland 0.56.2)"),
            ("Monitor", f"{width}x{height} (Scale {self.current_scale:.1f})"),
            ("Framerate", f"{self.live_fps:.1f} FPS (Target: {self.config.fps})"),
            ("Active Theme", f"{self.theme.name}"),
            ("Visual Mode", f"{self.mode_name}"),
            ("CPU Load", f"{cpu_val} ({m.cpu_model if m else ''})"),
            ("Memory", f"{mem_val}"),
            ("Power State", f"{power_val}"),
        ]

        for k, v in debug_lines:
            self.active_mode.draw_text(
                cr, f"{k:<12} : ", pad_x, cur_y,
                BaseMode.FONT_MONO, 9.5, with_alpha(self.theme.muted, 0.9), align="left"
            )
            self.active_mode.draw_text(
                cr, v, pad_x + 95.0, cur_y,
                BaseMode.FONT_MONO, 9.5, self.theme.bright_foreground, align="left"
            )
            cur_y += line_h
