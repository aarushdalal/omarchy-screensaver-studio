# Changelog

All notable changes to `omarchy-screensaver-studio` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
