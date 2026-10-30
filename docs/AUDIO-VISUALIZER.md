# Aurora Flow — Audio Visualizer

Aurora Flow follows the desktop palette and gives track information, measured audio and background motion separate space. The track title stays above the aurora ribbons; long titles, artists and albums are shortened to fit. The whole layout scales with the display.

## What moves and what it means

- **Spectrum bars:** live output-monitor energy arranged from low to high frequencies. Attack is fast and release is smooth. The underlying capture spans approximately 40 Hz–11.5 kHz; any configured 8–64 display bars include both ends of that range.
- **Floating peak caps:** briefly hold recent transients, then fall toward the bars. They are separate from the current levels.
- **LOW / MID / HIGH activity meters:** averages of three equal regions of the logarithmic spectrum. These are relative, equalized activity readings, not calibrated loudness, dB, speaker volume or a hearing-safety measurement.
- **Aurora ribbons and stardust:** decorative ambience. Ribbons respond to band energy; their quiet idle motion does not represent measured sound.
- **Reflections:** a faint visual echo of the bars beneath the baseline.

The spectrum responds to actual desktop audio even when the source has no media-player metadata. With player metadata, it shows title, artist, album and player. A paused player's old title is hidden if another source supplies live audio. On silence the bars and peaks decay to zero; background ribbons may continue moving.

## Status

**LIVE AUDIO** means the output monitor currently detects a signal. **SILENT PASSAGE** means the player reports playback but the monitor currently has no signal. **PAUSED** means retained track metadata with paused playback. **LISTENING** is the waiting state without an active track. Metadata availability and sound detection are separate.

Your existing automatic visualizer switching and ambient-study toggle are retained. Auto-switching follows media playback state. When already showing the visualizer, audio without player metadata is still visualized. A 1.2-second quiet grace period keeps brief track gaps from flashing another scene. The configured fallback resumes when both playback and the detected signal stay stopped; the application's existing selected-mode switching rules also remain in effect.

## Settings

Use `[visualizer]` in `~/.config/omarchy-screensaver/config.toml`: `bar_count` controls density; `particles`, `wave_ribbon` and `mirrored` control the corresponding decorations. Existing `style`, `auto_switch_on_play` and `fallback_mode` settings are retained. Older effect keys such as `shockwaves`, `light_beams`, `bass_bounce` and `radial_core` are accepted for compatibility but do not enable effects in this composition.

## Audio continuity

The application and its windows share one native capture worker. Closing one listener or switching scenes does not stop capture for listeners that remain. The last listener releases the worker. This also prevents different bar counts from truncating the high-frequency end of the display.
