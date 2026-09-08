"""MPRIS media player DBus integration and audio visualization math.

Connects to active media players via DBus org.mpris.MediaPlayer2 to retrieve
track metadata and playback state. Also simulates dynamic spectrum frequency
bands with peak hold and gravity decay physics for the audio visualizer.
"""

import math
import random
import time
from typing import Dict, List, Optional

from .audio import AudioEngine

try:
    import dbus
    HAS_DBUS = True
except ImportError:
    HAS_DBUS = False


class MediaInfo:
    """Represents current media playback state."""
    def __init__(
        self,
        player: str = "",
        status: str = "Stopped",
        title: str = "",
        artist: str = "",
        album: str = "",
        is_playing: bool = False,
    ):
        self.player = player
        self.status = status
        self.title = title
        self.artist = artist
        self.album = album
        self.is_playing = is_playing

    def __repr__(self):
        return f"<MediaInfo player={self.player} status={self.status} title={self.title!r}>"


class MprisClient:
    """Manages DBus queries to MPRIS players and real-time audio spectrum telemetry."""

    def __init__(self, bar_count: int = 36):
        self.bar_count = bar_count
        self._bus = None
        self._last_poll = 0.0
        self._cached_info: Optional[MediaInfo] = None
        self._bands = [0.0] * bar_count
        self._peaks = [0.0] * bar_count
        self._peak_speeds = [0.0] * bar_count
        self._time = 0.0
        self._has_audio_signal = False

        self.audio = AudioEngine(bar_count=self.bar_count)
        self.audio.start()

        if HAS_DBUS:
            try:
                self._bus = dbus.SessionBus()
            except Exception:
                self._bus = None

    def poll(self, force: bool = False) -> Optional[MediaInfo]:
        """Poll active media player via DBus."""
        now = time.time()
        if not force and (now - self._last_poll < 0.15) and self._cached_info is not None:
            return self._cached_info

        self._last_poll = now

        if not HAS_DBUS or self._bus is None:
            return None

        try:
            player_names = [
                str(n) for n in self._bus.list_names()
                if str(n).startswith("org.mpris.MediaPlayer2.")
            ]
            if not player_names:
                self._cached_info = None
                return None

            candidates: List[MediaInfo] = []
            for name in player_names:
                try:
                    obj = self._bus.get_object(name, "/org/mpris/MediaPlayer2")
                    props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
                    status = str(props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus"))
                    meta = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")

                    title = str(meta.get("xesam:title", ""))
                    artist_val = meta.get("xesam:artist", "")
                    if isinstance(artist_val, (list, tuple, dbus.Array)) and len(artist_val) > 0:
                        artist = ", ".join([str(a) for a in artist_val])
                    else:
                        artist = str(artist_val)
                    album = str(meta.get("xesam:album", ""))

                    # Clean player name
                    clean_player = name.replace("org.mpris.MediaPlayer2.", "")
                    clean_player = clean_player.split(".")[0].capitalize()

                    info = MediaInfo(
                        player=clean_player,
                        status=status,
                        title=title.strip(),
                        artist=artist.strip(),
                        album=album.strip(),
                        is_playing=(status.lower() == "playing"),
                    )
                    candidates.append(info)
                except Exception:
                    continue

            # Prioritize actively playing media
            playing = [c for c in candidates if c.is_playing and c.title]
            if playing:
                self._cached_info = playing[0]
            elif candidates:
                # First one with title
                with_title = [c for c in candidates if c.title]
                self._cached_info = with_title[0] if with_title else candidates[0]
            else:
                self._cached_info = None

        except Exception:
            self._cached_info = None

        return self._cached_info

    def update_spectrum(self, dt: float, is_playing: bool) -> List[float]:
        """Update audio spectrum bar values with live hardware audio capture or smooth idle decay."""
        self._time += dt

        # 1. High-priority real-time audio capture from PipeWire / PulseAudio
        if self.audio.is_available:
            live_bands, live_peaks, has_signal = self.audio.get_spectrum(self.bar_count)
            self._has_audio_signal = has_signal
            if has_signal:
                self._bands = live_bands
                self._peaks = live_peaks
                return self._bands

        # 2. If no hardware audio signal is active:
        self._has_audio_signal = False
        if is_playing:
            # Player reports playing but silent passage / between tracks: fast smooth decay
            for i in range(self.bar_count):
                self._bands[i] = max(0.01, self._bands[i] * 0.88)
                self._peaks[i] = max(0.0, self._peaks[i] - 1.5 * dt)
        else:
            # Paused or idle state: sleek, subtle resting baseline with gentle breathing
            for i in range(self.bar_count):
                rel = i / max(1, self.bar_count - 1)
                wave = math.sin(self._time * 1.2 + rel * 3.14) * 0.015 + 0.035
                self._bands[i] = max(0.02, min(0.06, wave))
                self._peaks[i] = 0.0

        return self._bands

    @property
    def has_signal(self) -> bool:
        return self._has_audio_signal

    @property
    def peaks(self) -> List[float]:
        return self._peaks

    @property
    def bands(self) -> List[float]:
        return self._bands
