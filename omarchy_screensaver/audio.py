"""Real-time audio spectrum capture engine for Omarchy Screensaver.

Interfaces with the native C PipeWire / PulseAudio monitor (libomarchy_audio.so)
to provide sub-10ms beat-reactive frequency visualization with zero lag.
"""

import ctypes
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple


class AudioEngine:
    """Provides high-performance live audio spectrum telemetry."""

    def __init__(self, bar_count: int = 36):
        self.bar_count = bar_count
        self._lib = None
        self._running = False
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
                    return
                except Exception as e:
                    print(f"[omarchy-audio] Error loading {so_path}: {e}", file=sys.stderr)

    @property
    def is_available(self) -> bool:
        return self._lib is not None

    def start(self, bar_count: Optional[int] = None) -> bool:
        """Start the audio capture thread."""
        if bar_count:
            self.bar_count = bar_count

        if self._running:
            return True

        if self._lib:
            try:
                res = self._lib.audio_spectrum_start(self.bar_count)
                self._running = bool(res)
                return self._running
            except Exception as e:
                print(f"[omarchy-audio] Error starting spectrum worker: {e}", file=sys.stderr)
                self._running = False
                return False

        return False

    def stop(self):
        """Stop audio capture."""
        if self._running and self._lib:
            try:
                self._lib.audio_spectrum_stop()
            except Exception:
                pass
            self._running = False

    def get_spectrum(self, count: Optional[int] = None) -> Tuple[List[float], List[float], bool]:
        """Get the latest real-time frequency bands and peaks.

        Returns:
            (bands, peaks, has_signal):
                bands: list of normalized values 0.0 - 1.0 per bar
                peaks: list of peak hold values 0.0 - 1.0 per bar
                has_signal: True if audio signal is currently active, False if silent
        """
        n = count or self.bar_count
        if not self._running or not self._lib:
            return ([0.0] * n, [0.0] * n, False)

        try:
            has_signal = bool(self._lib.audio_spectrum_get(self._bands_buf, self._peaks_buf, n))
            bands = [float(self._bands_buf[i]) for i in range(n)]
            peaks = [float(self._peaks_buf[i]) for i in range(n)]
            return (bands, peaks, has_signal)
        except Exception:
            return ([0.0] * n, [0.0] * n, False)

    def __del__(self):
        self.stop()
