# Changelog

All notable changes to `omarchy-screensaver-studio` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-30

### Performance & Optimization
- Ultra-low launch latency: study/ambient mode startup reduced from ~3.2s to ~0.45s (surpassing the $\le 1.5$s target).
- Eliminated DBus application ID registration stalls during startup; app ID is now cleanly registered via `GLib.set_prgname("org.omarchy.screensaver")` without blocking on name ownership.
- Deferred MPRIS client connection and audio visualizer engine threads until after initial Wayland surface presentation.
- Optimized engine loops across all modes: reduced redundant Cairo/Pango glyph rendering, clamped particle counts (90 particles, 300 warp stars, 220 singularity particles), and lowered target idle framerates to minimize CPU, GPU, and battery consumption.
- Replaced Python subshell debouncing in `omarchy-screensaver-toggle` with native Bash epoch timing.

### Added
- 5 new dark, non-glaring ambient modes (expanding the suite to 15 visual modes):
  - `cyber_nexus`: Subtle glowing neural nodes connected by pulsing data lines in deep OLED black.
  - `synthwave`: 3D perspective retro wireframe horizon with gentle neon gradient sun.
  - `quantum_helix`: Dual rotating DNA/quantum strands with orbital stardust motes.
  - `topography`: Dynamic topographic contour elevation lines undulating smoothly in dark ambient space.
  - `celestial_orbit`: Gravitational multi-orbital planetary system with planetary trails.
- Synchronized menu and selector support across Omarchy and DaemonOS (`SUPER + CTRL + I` and `SUPER + I`).
- Updated `omarchy-screensaver-select`, `omarchy-screensaver-menu`, `omarchy-menu-screensaver`, and `omarchy-menu-extension.jsonc` to fully support all 15 modes.

## [1.1.0] - 2026-09-13

### Added
- 4 brand new visual modes (expanding total suite to 10 modes):
  - `matrix`: 3D parallax cybernetic rain with authentic Katakana glyphs, hex numbers, and phosphor decay.
  - `warp`: Relativistic starfield warp with perspective speed streaks.
  - `geometry`: 4D rotating hypercube (tesseract) with depth cueing and chromatic glow.
  - `singularity`: Kerr rotating black hole with Doppler-beamed accretion disk.
- OLED burn-in protection with pure `#000000` subpixel shutoff and continuous orbital drift.
- Ambient study desk display mode with input immunity and sleep/lock inhibition (`SUPER + I`).
- Bundled `omarchy-menu-extension.jsonc` for native Omarchy application launcher integration.
- Updated HUD (`omarchy-menu-screensaver`), Terminal TUI (`omarchy-screensaver-menu`), and selector CLI (`omarchy-screensaver-select`) for all 10 visual modes.

## [1.0.0] - 2026-09-08

### Added
- Initial clean public release for Omarchy 4.0.2 / Arch Linux.
- 6 signature screensaver modes: minimal clock, generative particles, terminal diagnostics, system telemetry, audio visualizer, and aurora stardust.
- Native GTK4 Wayland window under app ID `org.omarchy.screensaver`.
- Integrated floating HUD selector and CLI management utilities.
- Comprehensive safe user installer script (`install.sh`) supporting `--dry-run`.
- Full security exclusions, sanitized configurations, and complete documentation.
