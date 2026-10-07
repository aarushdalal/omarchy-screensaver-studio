# Changelog

All notable changes to `omarchy-screensaver-studio` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-10-07

### Added & Refined
- **CPU & GPU Electrical Voltage & Current Telemetry**:
  - Live CPU rail voltage ($V_{\text{core}}$ in V) and core amperage ($I_{\text{core}}$ in A) computed from real-time power draw and dynamic VF curve/hwmon.
  - Live GPU graphics voltage ($V_{\text{ddgfx}}$ in V) and current ($I_{\text{gfx}}$ in A) reading directly from `amdgpu` hwmon `in0_input` and VRM power.
  - Live battery voltage ($V_{\text{bat}}$ in V) and charging/discharging current ($I_{\text{bat}}$ in A) via sysfs power supply sensors.
  - Speedometer bottom dial badges now display live voltage and current (`CPU Model · 0.99V · 12.1A` and `VRAM · 1.04V · 4.8A`).
- **Advanced Technical System Metrics & Spacious 3-Column Bay**:
  - Re-engineered 3-Column Telemetry Bay with dedicated spacing and balanced line lengths to eliminate any text crowding or overlap:
    - **Column 1** (`● ELECTRICAL & POWER`): Live Wattage, Voltage, and Amperage across CPU rail, GPU rail, and Battery/SoC.
    - **Column 2** (`● STORAGE & I/O MESH`): NVMe SSD storage capacity, drive temperature, network download/upload rates, and memory bus active/free stats.
    - **Column 3** (`● KERNEL & RUNTIME`): Linux kernel release, session user, 1m/5m/15m system load averages with logical core count, CPU frequency governor, and system uptime.
- **High-Efficiency Engine & Performance Optimizations (Zero Refresh/Polling Compromise)**:
  - **7.1x Faster Metrics Polling**: System telemetry update loop dropped from 18.2 ms to 2.5 ms per poll cycle without changing the 1000ms polling interval.
  - **Non-Blocking NVMe Worker**: Moved PCIe NVMe SMART thermal sampling into an asynchronous background daemon worker, completely eliminating the 5.5 ms main-thread PCIe bus query stall.
  - **Direct Sysfs File Access (Zero Redundant Stat Calls)**: Cached validated sensor paths at initialization, eliminating over 25 redundant `os.path.exists()` / `stat()` syscalls per update cycle.
  - **Binary Early-Exit Memory Parsing**: Replaced 55-line UTF-8 text parser for `/proc/meminfo` with an early-exit binary parser, yielding a 3x speedup.
  - **Streaming Network I/O**: Streamed `/proc/net/dev` lines directly rather than allocating intermediate line lists.
  - **Pango Layout Reuse & Font Cache**: Reused single PangoLayout instances in `BaseMode.draw_text()` with cached `Pango.FontDescription` objects and 21x faster `layout.get_pixel_size()` measurement, reducing Cairo text rasterization overhead by ~42% across all visual modes.
  - **Batched Cairo Stroke Geometry**: Grouped radial dial ticks and sparkline division markers into unified paths, reducing stroke context switches by 57%.
  - **Cached Header Clock Strings**: Eliminated redundant 30 FPS `time.localtime()` and `strftime` allocations.

## [1.4.0] - 2026-10-02

### Added & Refined
- **Spacious 3-Column System Telemetry HUD**:
  - Re-architected system telemetry below the sparkline into 3 dedicated, well-spaced functional columns vertically aligned directly beneath the 3 speedometer gauges:
    - **Left Column** (`● POWER & BATTERY`): CPU & GPU wattage, total SoC package power, battery charge/discharge percentage & live rate.
    - **Center Column** (`● STORAGE & NETWORK`): NVMe SSD usage, drive temperature, active network interface, download & upload throughput.
    - **Right Column** (`● SYSTEM PLATFORM`): Linux kernel release, system uptime, and session user/hostname.
  - Eliminated cluttered horizontal paragraphs of concatenated abbreviations and dots.
  - Generous spacing between all HUD elements: clock-to-dial padding (195px), dial horizontal separation (380px), dial-to-sparkline margin (85px), and sparkline-to-telemetry margin (56px).
  - Streamlined speedometer tachometer dials with 10 clean automotive divisions, removing noisy micro-ticks for a tranquil, luxury instrument panel feel.
- **Audio Visualizer 48kHz Engine & Full 36-Band Dynamic Range**:
  - Upgraded native audio capture pipeline in `audio_spectrum.c` to native 48,000 Hz sample rate (matching PipeWire 1.6.8).
  - Switched to generalized continuous angular frequency calculations ($\omega = 2\pi f / f_s$), preventing low-frequency duplicate bins.
  - Extended musical frequency span to 40 Hz – 11,500 Hz, with progressive acoustic tilt equalization boost (`pow(rel, 1.15) * 8.5`) to overcome high-frequency acoustic roll-off.
  - Fixed dead/flat response in the top 4 visualizer bars (bands 32-35), providing full dynamic dance across the entire audible spectrum.
- **Ambient Study Mode Audio Visualizer Toggle**:
  - Added dedicated toggle mechanism (`omarchy-screensaver-visualizer-toggle`, bound to `SUPER + T` or keypress `'t'` in study mode) to switch between study desk display and live music visualizer without exiting study mode.
- **Strict Theme Palette Adherence**:
  - Eliminated ANSI terminal magenta/cyan bleeding into visualizer, aurora, particles, and widget ribbons by deriving `secondary` and `dark_accent` strictly from active desktop theme tokens (`dark_foreground`, `light_foreground`, `dark_accent`, `selection`).

## [1.3.0] - 2026-10-01

### Added
- **Digital Cockpit Speedometer Telemetry Cluster**: Complete visual overhaul of `system` mode into an automotive sports car instrument panel featuring:
  - **GPU Speedometer Hero Dial**: High-resolution 270° radial speedometer with dynamic neon speed arc, precision sweeping needle, illuminated needle boss, and glowing redline danger zone (80% - 100%).
  - **Live GPU Telemetry Stream**: Accurate GPU utilization percentage, VRAM allocation (used/total MB), GTT shared memory, GPU clock frequency (MHz), and GPU core temperature (°C) via cached direct sysfs queries.
  - **CPU Tachometer Dial**: Synchronized RPM/Load instrument tracking CPU load, multi-core average & max clock frequencies (GHz), core temperature (k10temp/Tctl), and CPU power draw.
  - **Multi-Channel Power Draw Console**: Real-time multi-channel power metrics displaying live CPU power (W), GPU power (W), SoC package total (PPT Watts), and Battery charge/discharge power (W).
  - **Automotive Motion Physics**: Eased spring-damped needle acceleration, high-RPM mechanical micro-vibrations (>75% load), and 3-second peak-hold indicators.
  - **Dedicated Hardware Badges**: Clean pill containers beneath each dial displaying CPU model, VRAM/GTT memory, and Swap memory without gauge dial clutter.
  - **Dual Live Bezier Telemetry Sparklines**: Simultaneous rolling history oscilloscopes for both CPU load and GPU load.
  - **Expanded Hardware Telemetry**: Added NVMe SSD temperature monitoring, network throughput, Linux kernel release, and system uptime.
- **Cross-Mode Telemetry Upgrades**: Added live GPU utilization and power draw metrics to both `clock` and `terminal` screensaver modes.

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
