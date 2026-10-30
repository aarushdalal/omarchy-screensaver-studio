"""Real-time audio spectrum capture engine for Omarchy Screensaver.

Interfaces with the native C PipeWire / PulseAudio monitor (libomarchy_audio.so)
to provide beat-reactive frequency bands for the visualizer.
"""

import ctypes
import os
import sys
import threading
from pathlib import Path
from typing import List, Optional, Tuple


class AudioEngine:
    """Provides high-performance live audio spectrum telemetry."""

    # The native library has one worker per process. Share its lifetime and a
    # fixed 64-band spectrum; each window can request its own resolution.
    _worker_lock = threading.RLock()
    _worker_users = {}
    NATIVE_BANDS = 64

    def __init__(self, bar_count: int = 36):
        self.bar_count = max(8, min(self.NATIVE_BANDS, int(bar_count)))
        self._lib = None
        self._running = False
        self._worker_key = None
        self._bands_buf = (ctypes.c_float * 64)()
        self._peaks_buf = (ctypes.c_float * 64)()
        self._load_library()

    def _load_library(self):
        # Search candidate paths for libomarchy_audio.so
        search_dirs = [
            Path(__file__).resolve().parent,
            Path.home() / ".local" / "share" / "omarchy-screensaver" / "omarchy_screensaver",
            Path(__file__).resolve().parent.parent / "omarchy_screensaver",
        ]

        for d in search_dirs:
            so_path = d / "libomarchy_audio.so"
            if so_path.exists():
                try:
                    lib = ctypes.CDLL(str(so_path))
                    lib.audio_spectrum_start.argtypes = [ctypes.c_int]
                    lib.audio_spectrum_start.restype = ctypes.c_int

                    lib.audio_spectrum_get.argtypes = [
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.c_int,
                    ]
                    lib.audio_spectrum_get.restype = ctypes.c_int

                    lib.audio_spectrum_stop.restype = None

                    self._lib = lib
                    self._worker_key = str(so_path.resolve())
                    return
                except Exception as e:
                    print(f"[omarchy-audio] Error loading {so_path}: {e}", file=sys.stderr)

    @property
    def is_available(self) -> bool:
        return self._lib is not None

    def start(self, bar_count: Optional[int] = None) -> bool:
        """Start the audio capture thread."""
        if bar_count is not None:
            self.bar_count = max(8, min(self.NATIVE_BANDS, int(bar_count)))
        with self._worker_lock:
            if self._running:
                return True
            if not self._lib:
                return False
            try:
                users = self._worker_users.get(self._worker_key, 0)
                if not users and not self._lib.audio_spectrum_start(self.NATIVE_BANDS):
                    return False
                self._worker_users[self._worker_key] = users + 1
                self._running = True
            except Exception as e:
                print(f"[omarchy-audio] Error starting spectrum worker: {e}", file=sys.stderr)
                return False
        return True

    def stop(self):
        """Release this listener; other windows retain uninterrupted capture."""
        with self._worker_lock:
            if not self._running or not self._lib:
                return
            self._running = False
            users = self._worker_users.get(self._worker_key, 1) - 1
            if users > 0:
                self._worker_users[self._worker_key] = users
            else:
                self._worker_users.pop(self._worker_key, None)
                try:
                    self._lib.audio_spectrum_stop()
                except Exception:
                    pass

    @staticmethod
    def _resample(values, count):
        """Interpolate across the entire log-frequency span at every bar count."""
        if count == len(values):
            return list(values)
        result = []
        for i in range(count):
            pos = i * (len(values) - 1) / max(1, count - 1)
            low = int(pos)
            high = min(len(values) - 1, low + 1)
            result.append(values[low] + (values[high] - values[low]) * (pos - low))
        return result

    def get_spectrum(self, count: Optional[int] = None) -> Tuple[List[float], List[float], bool]:
        """Get the latest real-time frequency bands and peaks.

        Returns:
            (bands, peaks, has_signal):
                bands: list of normalized values 0.0 - 1.0 per bar
                peaks: list of peak hold values 0.0 - 1.0 per bar
                has_signal: True if audio signal is currently active, False if silent
        """
        n = max(1, min(self.NATIVE_BANDS, int(count if count is not None else self.bar_count)))
        if not self._running or not self._lib:
            return ([0.0] * n, [0.0] * n, False)

        try:
            has_signal = bool(self._lib.audio_spectrum_get(self._bands_buf, self._peaks_buf, self.NATIVE_BANDS))
            bands = self._resample(self._bands_buf, n)
            peaks = self._resample(self._peaks_buf, n)
            return (bands, peaks, has_signal)
        except Exception:
            return ([0.0] * n, [0.0] * n, False)

    def __del__(self):
        self.stop()
