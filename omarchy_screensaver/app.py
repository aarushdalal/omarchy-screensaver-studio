"""Application controller for Omarchy Screensaver.

Manages multi-monitor fullscreen windows, mode rotation, theme watching,
system metrics polling, and clean signal-based shutdown.
"""

import os
import signal
import sys
import time
from typing import List, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk

from .config import Config
from .metrics import SystemMetrics
from .modes import AVAILABLE_MODES
from .mpris import MediaInfo, MprisClient
from .theme import ThemeManager
from .window import ScreensaverWindow


class ScreensaverApp(Gtk.Application):
    """Main GTK4 application for the Omarchy screensaver engine."""

    PID_FILE = os.path.expanduser("~/.config/omarchy-screensaver/screensaver.pid")
    LOG_FILE = os.path.expanduser("~/.config/omarchy-screensaver/logs/screensaver.log")

    def __init__(
        self,
        config: Config,
        forced_mode: Optional[str] = None,
        is_preview: bool = False,
        is_debug: bool = False,
        is_ambient: bool = False,
    ):
        super().__init__(
            application_id="org.omarchy.screensaver",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.config = config
        self.forced_mode = forced_mode
        self.is_preview = is_preview
        self.is_debug = is_debug
        self.is_ambient = is_ambient

        self.selected_mode = self.forced_mode or self.config.mode
        if self.selected_mode not in AVAILABLE_MODES and self.selected_mode != "auto":
            self.selected_mode = "clock"
        self.current_mode = self.selected_mode
        self._saved_mode_before_audio: Optional[str] = None

        self.windows: List[ScreensaverWindow] = []
        self.theme_manager = ThemeManager(self.config.theme, self.config.THEMES_DIR)
        self.metrics = SystemMetrics()
        self.mpris = MprisClient()
        self.media_info: Optional[MediaInfo] = None

        self._rotation_idx = 0
        self._rotation_modes = [m for m in self.config.rotation_modes if m in AVAILABLE_MODES]
        if not self._rotation_modes:
            self._rotation_modes = AVAILABLE_MODES

        self._is_dismissed = False

        self.connect("activate", self._on_activate)

    def log(self, message: str):
        """Append message to user log file."""
        try:
            os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except Exception:
            pass

    def _on_activate(self, app):
        self._write_pid()
        self._setup_signals()

        display = Gdk.Display.get_default()
        if not display:
            print("[omarchy-screensaver] Error: No default Wayland/GDK display found.")
            self.quit()
            return

        monitors = display.get_monitors()
        n_monitors = monitors.get_n_items()

        self.log(
            f"Startup: mode={self.current_mode} theme={self.theme_manager.palette.name} "
            f"monitors={n_monitors} preview={self.is_preview} debug={self.is_debug} ambient={self.is_ambient}"
        )

        active_mode_name = self.current_mode
        if active_mode_name == "auto":
            active_mode_name = self._rotation_modes[0]

        # Initial media state check: if media is actively playing, launch visualizer
        self.media_info = self.mpris.poll(force=True)
        if (
            self.media_info
            and self.media_info.is_playing
            and self.config.visualizer_auto_switch_on_play
            and not self.forced_mode
            and not self.is_preview
        ):
            if active_mode_name != "visualizer":
                self._saved_mode_before_audio = active_mode_name
                active_mode_name = "visualizer"
                self.current_mode = "visualizer"
                self.log(f"Media playing at launch: auto-switched to visualizer (saved: {self._saved_mode_before_audio})")

        # Multi-monitor window creation
        if self.config.multi_monitor == "single" or n_monitors <= 1:
            mon = monitors.get_item(0)
            win = ScreensaverWindow(
                app=self,
                monitor=mon,
                monitor_index=0,
                config=self.config,
                theme=self.theme_manager.palette,
                mode_name=active_mode_name,
                is_preview=self.is_preview,
                is_debug=self.is_debug,
                is_ambient=self.is_ambient,
            )
            self.windows.append(win)
            win.present()
        else:
            # Independent or Mirror on all monitors
            for i in range(n_monitors):
                mon = monitors.get_item(i)
                win = ScreensaverWindow(
                    app=self,
                    monitor=mon,
                    monitor_index=i,
                    config=self.config,
                    theme=self.theme_manager.palette,
                    mode_name=active_mode_name,
                    is_preview=self.is_preview,
                    is_debug=self.is_debug,
                    is_ambient=self.is_ambient,
                )
                self.windows.append(win)
                win.present()

        # Register timers (200ms responsive MPRIS poll for instant play/pause reaction)
        GLib.timeout_add(1000, self._on_metrics_timer)
        GLib.timeout_add(1200, self._on_theme_timer)
        GLib.timeout_add(200, self._on_mpris_timer)

        # Mode rotation timer if enabled
        if self.config.rotation and not self.forced_mode and not self.is_preview:
            interval_ms = max(10, self.config.rotation_interval) * 1000
            GLib.timeout_add(interval_ms, self._on_rotation_timer)

    def _on_metrics_timer(self) -> bool:
        if self._is_dismissed:
            return GLib.SOURCE_REMOVE
        self.metrics.update()
        return GLib.SOURCE_CONTINUE

    def _on_theme_timer(self) -> bool:
        if self._is_dismissed:
            return GLib.SOURCE_REMOVE
        if self.theme_manager.check_for_updates():
            new_palette = self.theme_manager.palette
            self.log(f"Theme reloaded: {new_palette.name}")
            for win in self.windows:
                win.set_theme(new_palette)
        return GLib.SOURCE_CONTINUE

    def _on_mpris_timer(self) -> bool:
        if self._is_dismissed:
            return GLib.SOURCE_REMOVE

        was_playing = bool(self.media_info and self.media_info.is_playing)
        self.media_info = self.mpris.poll()
        is_playing = bool(self.media_info and self.media_info.is_playing)

        # 1. Auto-switch to visualizer when audio starts playing
        if (
            not was_playing
            and is_playing
            and self.config.visualizer_auto_switch_on_play
            and not self.forced_mode
            and not self.is_preview
        ):
            if self.current_mode != "visualizer":
                self._saved_mode_before_audio = self.current_mode
                self.switch_mode("visualizer")
                self.log(f"Media started: auto-switched to visualizer (saved: {self._saved_mode_before_audio})")

        # 2. Revert back to the user's selected visual mode when audio stops or pauses
        elif (
            was_playing
            and not is_playing
            and not self.forced_mode
            and not self.is_preview
        ):
            if self.current_mode == "visualizer":
                target_mode = getattr(self, "_saved_mode_before_audio", None) or self.selected_mode
                if target_mode == "auto":
                    target_mode = self._rotation_modes[0]
                if target_mode != "visualizer":
                    self.switch_mode(target_mode)
                    self.log(f"Media paused/stopped: reverted to selected mode '{target_mode}'")
                self._saved_mode_before_audio = None

        return GLib.SOURCE_CONTINUE

    def _on_rotation_timer(self) -> bool:
        if self._is_dismissed:
            return GLib.SOURCE_REMOVE
        self._rotation_idx = (self._rotation_idx + 1) % len(self._rotation_modes)
        next_mode = self._rotation_modes[self._rotation_idx]
        self.switch_mode(next_mode)
        return GLib.SOURCE_CONTINUE

    def switch_mode(self, mode_name: str):
        """Switch visual mode across all monitor windows."""
        if mode_name in AVAILABLE_MODES and mode_name != self.current_mode:
            self.current_mode = mode_name
            self.log(f"Mode switched to: {mode_name}")
            for win in self.windows:
                win.set_mode(mode_name)

    def dismiss(self):
        """Cleanly close all screensaver windows and exit."""
        if self._is_dismissed:
            return
        self._is_dismissed = True
        self.log("Dismissed by user interaction or signal")

        if hasattr(self, "mpris") and hasattr(self.mpris, "audio"):
            try:
                self.mpris.audio.stop()
            except Exception:
                pass

        for win in self.windows:
            try:
                win.close()
            except Exception:
                pass

        # Clean up ambient stay-awake indicator if set by screensaver
        marker = os.path.expanduser("~/.local/state/omarchy/indicators/stay-awake-screensaver")
        stay_awake = os.path.expanduser("~/.local/state/omarchy/indicators/stay-awake")
        if os.path.exists(marker):
            try:
                os.remove(marker)
            except Exception:
                pass
            try:
                if os.path.exists(stay_awake):
                    os.remove(stay_awake)
            except Exception:
                pass

        self._remove_pid()
        self.quit()

    def _setup_signals(self):
        # Handle termination signals cleanly
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            try:
                GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, self._signal_handler, sig)
            except Exception:
                pass

    def _signal_handler(self, sig: int) -> bool:
        self.log(f"Received signal {sig}, terminating...")
        self.dismiss()
        return GLib.SOURCE_REMOVE

    def _write_pid(self):
        try:
            os.makedirs(os.path.dirname(self.PID_FILE), exist_ok=True)
            with open(self.PID_FILE, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass

    def _remove_pid(self):
        try:
            if os.path.exists(self.PID_FILE):
                os.remove(self.PID_FILE)
        except Exception:
            pass
