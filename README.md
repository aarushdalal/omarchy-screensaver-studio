# Screensaver Studio (`omarchy-screensaver-studio`)

> **Unofficial / Community Plugin**: An independent multi-mode screensaver suite for Omarchy.

A native Wayland screensaver engine with 42 visual modes (18 signature ambient scenes and 24 DAEMON Satisfying procedural GPU prototypes), OLED burn-in prevention, dynamic Omarchy theme synchronization, real-time PipeWire audio spectrum visualization, and full integration with Quickshell's idle monitor and Omarchy launcher menus — running under application ID `org.omarchy.screensaver`.

This project was developed through an AI-assisted workflow. The concept, customization, configuration, testing, integration, and final iteration were directed and carried out by me.

---

## DAEMON Satisfying Procedural Collection

The studio now includes 42 visual modes across four collections, adding 24 procedural GPU-accelerated mathematical prototypes (`daemon_satisfying`) built on OpenGL ES 3.0 and native GTK4 `GLArea`.

- **Harmonic & Rosettes**: `harmonograph`, `zen_geometry`, `harmonic_sculpture`
- **Fluid & Advection**: `infinite_ripples`, `ink_singularity`, `midnight_rain`, `ink_choreography`
- **Kinematic & Mechanical**: `the_perfect_machine`, `mechanical_eternity`, `domino_architect`, `wave_field`, `infinite_origami`*, `infinite_marble_machine`*
- **Generative Growth & Graph Routing**: `fractal_bloom`, `particle_architect`, `circuit_genesis`, `circuit_weaver`, `silk_continuum`, `orbital_synchronization`, `monolithic_construction`, `infinite_zen_garden`
- **Raymarched Distance Fields**: `liquid_obsidian`, `mercury_garden`, `event_horizon`

Find every mode, its launch ID and a video in the [showcase catalogue](#showcase-gallery). The [DAEMON Satisfying guide](docs/DAEMON-SATISFYING.md) covers settings and prototype limitations.

> [!NOTE]
> *`infinite_origami` and `infinite_marble_machine` are early kinematic approximations under active development. This release is an authorized preview and does not claim final commercial completeness or verified multi-hour temporal comfort.

## Background-only glass (1.9.0)

Set `background_opacity = 0.68` under `[display]` to reveal the compositor-blurred desktop while keeping text, gauges and scene effects at their normal opacity. The default remains `1.0` for an opaque background. Transparent GTK surfaces and replacement background painting prevent black backing layers and opacity buildup across frames. Whole-window opacity should stay at 100%; blur comes from the compositor. Existing previews predate this feature. Live glass appearance still needs checking on the target desktop.

## Audio and startup refinement (1.8.1)

Aurora Flow now separates larger track information from the live spectrum, with falling peak caps, low/mid/high band-activity meters and quiet theme-coloured ribbons. Live desktop sound responds even without a named player. Audio listeners share capture safely, and all bar counts span the complete frequency range. The cockpit wakes its seven instruments in sequence, then brings activity and detail panels into view. [Audio Visualizer guide](docs/AUDIO-VISUALIZER.md) · [Telemetry guide](docs/SYSTEM-COCKPIT.md).

## Ambient collection refresh (1.8.0)

The 1.8.0 refresh brought the original 18 modes into one searchable menu. Open it with `omarchy-menu-screensaver`, type a name such as Rain or Eclipse, and choose it to apply. The current selection is marked with a check. **Preview Screensavers** opens separate 12-second previews. **Follow Desktop Colours** keeps scenes matched to the active desktop palette. Running screensavers pick up mode, palette and rotation edits within 1.5 seconds without restarting.

New scenes: **Eclipse** (lunar silhouette and solar corona), **Ink Flow** (slow silk filaments), and **Rain on Glass** (night lights and drifting droplets). These inherit the active desktop palette.

Rebuilt Cyber Nexus eliminates accidental filled triangles and an unbounded packet refill loop. Topography now draws nested island contours; Quantum Helix has continuous depth-sorted strands; Celestial Orbit uses matching eccentric guides and time-based trails. Synthwave has opaque terrain silhouettes. Initial allocation and later resizes reach each mode, logical pixel scaling avoids doubled high-DPI effects, the system cockpit fits smaller screens, and long media titles are truncated within the available width.

Existing selected mode, palette, rotation list, ambient controls, audio backend and idle/lock integration are retained during the local upgrade. The default configuration for new installations includes the new scenes in rotation.

Validation: `/usr/bin/python3 -m unittest discover -s tests -v`. These rendering and integration checks require the system PyGObject and Cairo packages.

## My Contribution

I did not write Omarchy, Quickshell, Hyprland, GTK4, or PipeWire from scratch. What I contributed:

- **Plugin Architecture**: Designed and structured this as a conformant Omarchy plugin with `manifest.json` and `BarWidget.qml` following the Omarchy plugin conventions.
- **Python GTK4/Cairo Screensaver Engine**: Designed and implemented the multi-mode screensaver as a native GTK4 Wayland window under application ID `org.omarchy.screensaver` (integrates with Hyprland window rules and Quickshell's `IdleMonitor`). Core modules: `app.py`, `window.py`, `modes/`, `theme.py`, `config.py`.
- **18 Signature Visual Modes**: Authored all visual mode rendering logic:
  - `eclipse`: A lunar silhouette encircled by a softly breathing solar corona.
  - `ink_flow`: Layered silk filaments slowly folding through black space.
  - `rain`: Quiet droplets over distant night lights and reflections.
  - `clock`: Minimalist floating typographic clock with celestial orbital aura, date, and battery status.
  - `matrix`: 3D parallax cybernetic rain with authentic Katakana glyphs, hex numbers, and phosphor decay.
  - `particles`: Volumetric cosmic constellation with wandering gravitational attractor.
  - `warp`: Relativistic 3D starfield hyperspace jump with speed streaks and depth scaling.
  - `geometry`: Hypnotic 4D rotating hypercube (tesseract) with depth cueing and chromatic glow.
  - `singularity`: Kerr rotating black hole with relativistic Doppler-beamed accretion disk.
  - `system`: Digital Cockpit Speedometer Telemetry Cluster — Automotive instrument cluster with precision tachometers (CPU, GPU, RAM), dynamic voltage & amperage badges, dual-trace Bezier 60-second activity sparkline, and an elevated 3-column precision telemetry deck (`ELECTRICAL & POWER` with CPU/GPU/Total SoC/DRAM wattage/volts/amps, `STORAGE & MEMORY I/O` with live NVMe read/write MB/s, IOPS, lifetime transfer totals, and RAM bus bandwidth, and `KERNEL & RUNTIME` with 16-thread queue capacity and load averages).
  - `terminal`: Borderless diagnostic waterfall streaming live Linux kernel and procfs metrics.
  - `visualizer`: Aurora ribbons, live spectrum bars with falling peak caps, low/mid/high activity meters and readable MPRIS track information. See [the Audio Visualizer guide](docs/AUDIO-VISUALIZER.md).
  - `aurora`: Multi-octave harmonic spline ribbons with celestial stardust motes.
  - `cyber_nexus`: Subtle glowing neural nodes connected by pulsing data lines in deep OLED black.
  - `synthwave`: 3D perspective retro wireframe horizon with gentle neon gradient sun.
  - `quantum_helix`: Dual rotating DNA/quantum strands with orbital stardust motes.
  - `topography`: Dynamic topographic contour elevation lines undulating smoothly in dark ambient space.
  - `celestial_orbit`: Gravitational multi-orbital planetary system with planetary trails.
- **OLED Burn-in Protection**: Implemented true `#000000` black subpixel shutoff mode with continuous imperceptible orbital coordinate drift to safeguard OLED/AMOLED displays.
- **Ambient Study Display Mode**: Created dedicated ambient study display toggle with sleep/lock inhibition and touch immunity (shortcut: `SUPER + I`), plus live audio visualizer toggle (`SUPER + T` / `'t'`).
- **Dynamic Palette Synchronizer**: Designed `theme.py` to inherit color schemes dynamically from the active Omarchy `colors.toml` or built-in presets (`aurora`, `cyberpunk`, `matrix`, `minimal`, `osaka`) with 100% theme harmony.
- **Real-Time PipeWire Audio Spectrum Engine**: Native C PipeWire audio monitor (`audio_spectrum.c` compiled into `libomarchy_audio.so`) running at native 48,000 Hz with 64 continuous-frequency Goertzel filters, progressive acoustic tilt equalization and 8–64 display bars spanning the full spectrum (40 Hz - 11.5 kHz), and study mode visualizer toggle (`SUPER + T` / keypress `'t'`).
- **Idle Lifecycle Integration**: Wired `Service.qml` (Quickshell) to trigger the screensaver via `omarchy-launch-screensaver` wrapper and `shell.json` configuration. Wake dismissal (key press, mouse motion, click) cancels idle cycles.
- **Interactive Menu Suite & Extensions**: Designed the floating modal HUD selector (`omarchy-menu-screensaver`), keyboard-driven terminal manager (`omarchy-screensaver-menu` via Gum), CLI state manager (`omarchy-screensaver-select`), and `omarchy-menu-extension.jsonc` for Omarchy application launcher integration.
- **Bar Widget**: Implemented `BarWidget.qml` showing screensaver mode and controls in the Omarchy top bar.
- **Theme Definitions**: Authored `themes/` directory with per-mode color palette overrides.
- **Performance Tuning**: Bounded particle populations, local random generators and mode-specific frame limits; the ambient collection targets 30 FPS. Actual throughput varies with resolution, theme, graphics driver and load.
- **Installer**: Authored `./install.sh` with timestamped backup manifests.
- **Testing**: 33 rendering, selection, theme, audio and telemetry regression checks pass locally. All 18 modes redraw under palette changes; native selection and the updated cockpit recording were checked on the local Hyprland desktop.

---

## Based On / Credits

- **[Omarchy](https://github.com/basecamp/omarchy)** — The open-source Arch Linux desktop environment and plugin system by Basecamp. This plugin uses the Omarchy plugin manifest format, bar widget API, and idle lifecycle integration.
- **[Quickshell](https://quickshell.outfoxxed.me)** — The Qt6 QML Wayland layer-shell desktop shell. `Service.qml` connects to Quickshell's `IdleMonitor` for automatic idle triggering.
- **[Hyprland](https://hyprland.org)** — The Wayland compositor. Window rules target `org.omarchy.screensaver` for fullscreen/float placement.
- **GTK4 / PyGObject / Cairo** — The native Wayland rendering toolkit used for all visual modes.
- **[PipeWire](https://pipewire.org)** — The audio server. The optional audio spectrum engine captures audio via `libpulse-simple` from PipeWire's PulseAudio compatibility layer.

**Related Repos**:
- [omarchy-system-pulse](https://github.com/aarushdalal/omarchy-system-pulse) — System telemetry and audio dashboard
- [omarchy-focus-hub](https://github.com/aarushdalal/omarchy-focus-hub) — Pomodoro and focus session manager
- [omarchy-aesthetic-themes](https://github.com/aarushdalal/omarchy-aesthetic-themes) — Anime color themes (palettes used by screensaver)

---

## Plugin Manifest

This repository includes a valid `manifest.json` for the Omarchy plugin system:

```json
{
  "schemaVersion": 1,
  "id": "daemon0.screensaver-studio",
  "name": "Screensaver Studio",
  "version": "2.0.0-beta.7",
  "author": "Daemon0",
  "description": "42-mode screensaver studio (18 classic scenes and 24 DAEMON Satisfying procedural GPU prototypes) with live telemetry, audio spectrum and native preview controls",
  "kinds": ["bar-widget"],
  "entryPoints": { "barWidget": "BarWidget.qml" },
  "barWidget": {
    "displayName": "Screensaver Studio",
    "category": "Desktop",
    "allowMultiple": false,
    "defaultSection": "right"
  }
}
```

---

## Status / Experimental Warning

This project contains native Python GTK4 rendering code and optional C extensions. **Pre-compiled binary objects (`.so`) are excluded from the public repository.** Build tools (`gcc`, `libpulse`) are required only if you want real-time audio reactivity. Framerate, rendering overhead, and battery consumption vary by GPU driver and CPU architecture.

---

## Features

- **Sub-Second Latency & Low Resource Consumption**: Instant startup ($\le 0.45$s) using deferred background subsystem initialization and optimized lightweight rendering loops.
- **18 Signature Visual Modes**:
  - `eclipse`: A lunar silhouette encircled by a softly breathing solar corona.
  - `ink_flow`: Layered silk filaments slowly folding through black space.
  - `rain`: Quiet droplets over distant night lights and reflections.
  - `clock`: Minimal typographic clock with orbital aura
  - `matrix`: 3D Katakana & hex cybernetic cascading rain with glyph caching
  - `particles`: Volumetric constellation network with wandering attractor (clamped to 90 particles for low CPU load)
  - `warp`: Relativistic starfield warp with perspective streaks (300 stars)
  - `geometry`: 4D rotating hypercube (tesseract) with depth cueing
  - `singularity`: Kerr black hole with Doppler-beamed accretion disk (220 particles)
  - `terminal`: Borderless holographic diagnostic stream
  - `system`: Digital Cockpit Speedometer Telemetry Cluster — Automotive tachometers, live CPU/GPU/SoC/DRAM electrical rails (W, V, A), real-time NVMe read/write speeds, IOPS, and lifetime stats, memory bus bandwidth (GB/s), and 16-thread run queue capacity
  - `visualizer`: Real-time PipeWire audio spectrum & MPRIS metadata
  - `aurora`: Harmonic Perlin spline ribbons with stardust motes (20 FPS smooth flow)
  - `cyber_nexus`: Subtle glowing neural nodes connected by pulsing data lines in deep OLED black
  - `synthwave`: 3D perspective retro wireframe horizon with gentle neon gradient sun
  - `quantum_helix`: Dual rotating DNA/quantum strands with orbital stardust motes
  - `topography`: Dynamic topographic contour elevation lines undulating smoothly in dark ambient space
  - `celestial_orbit`: Gravitational multi-orbital planetary system with planetary trails
- **OLED True-Black Mode**: `#000000` subpixel shutoff with continuous micro-drift protection
- **Dual-OS Integration**: Unified controls and synchronized launcher menus across both Omarchy and DaemonOS (`SUPER + CTRL + I` and `SUPER + I`)
- **Dynamic Palette Synchronizer**: Inherits color schemes from the active Omarchy theme (`colors.toml`) or built-in presets
- **Interactive Floating HUD**: `omarchy-menu-screensaver` modal menu and top-bar integration
- **Terminal TUI Manager**: `omarchy-screensaver-menu` powered by Gum
- **Omarchy Menu Integration**: Bundled `omarchy-menu-extension.jsonc` adds direct screensaver controls into Omarchy launcher menus
- **Idle Lifecycle Integration**: App ID `org.omarchy.screensaver` — integrates with Quickshell idle services, dismisses instantly on input
- **Real-Time Audio Spectrum**: Optional C/PipeWire backend with 36 Goertzel filters, sub-10ms latency

### System Cockpit in 1.8.0

The system display now puts the most useful readings first, with larger text and seven animated gauges. On launch, a labelled car-style instrument check starts CPU, graphics and memory in sequence, then temperature, storage, load and battery. Each needle sweeps to 100, returns to zero, then hands over to real utilization. Activity and detail panels fade in as later components:

1. **Core load:** CPU, GPU and memory utilization. Smooth needles follow the readings; a separate outer marker holds the recent peak. Per-core activity, VRAM and swap bars sit below the main instruments.
2. **Capacity and thermals:** CPU temperature, root-storage usage, normalized one-minute load and battery charge. The temperature instrument uses a labelled 0–100°C display scale. Unsupported sensors show N/A.
3. **Activity:** separate processor and network histories, with solid/dashed traces that remain distinguishable in monochrome themes, pulsing live endpoints and a subtle moving scan line.
4. **Details:** power/electrical readings; today’s disk reads/writes; lifetime NVMe reads, writes, I/O-command snapshot and estimated endurance; current disk throughput/IOPS; memory activity; and kernel, tasks, governor, uptime and Linux resource pressure.

Per-core activity comes from successive `/proc/stat` samples. Pressure readings use `some avg10` from `/proc/pressure`: the percentage of the preceding ten seconds in which at least one task was stalled. The load/capacity gauge divides one-minute load average by logical CPU count; it is not CPU utilization. Network rates aggregate non-loopback interfaces and use an explicitly labelled automatic graph scale.

CPU/GPU power allocation and DRAM values are estimates and are labelled **est.** A readable hardware power sensor is shown separately. **VM page flow** describes allocation/free-page activity; it is not a measured physical memory-bus benchmark. Missing pressure/temperature sensors remain unavailable rather than inventing readings.

Rendering targets 30 FPS with bounded drawing work, while metrics are sampled about twice a second. Actual throughput depends on hardware, resolution and load. The layout scales together to preserve its hierarchy on smaller displays. All accents and highlights follow the active palette. See [the full cockpit field and layout guide](docs/SYSTEM-COCKPIT.md), including daily-total coverage, the optional SMART snapshot refresh and what **PRESSURE 10s / PSI** means.

---

## Showcase Gallery

**42 screensavers across four collections.** Choose a name to watch it in the [browser gallery](https://aarushdalal.github.io/omarchy-screensaver-studio/) or download its silent WebM from [v2.0.0-beta.7](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/tag/v2.0.0-beta.7).

To run the live screensavers, follow [Installation](#installation). After installing, run `omarchy-menu-screensaver` to browse the collection or `omarchy-screensaver-preview <mode-id> 10` to play a timed preview.

### Quiet Focus

| Screensaver | Mode ID | Preview | Description |
|---|---|---|---|
| [Eclipse](https://aarushdalal.github.io/omarchy-screensaver-studio/#eclipse)<br>[![Eclipse preview](assets/showcase/previews/eclipse.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#eclipse) | `eclipse` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/eclipse.webm) | A lunar silhouette with a breathing solar corona |
| [Ink Flow](https://aarushdalal.github.io/omarchy-screensaver-studio/#ink_flow)<br>[![Ink Flow preview](assets/showcase/previews/ink_flow.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#ink_flow) | `ink_flow` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/ink_flow.webm) | Layered silk filaments folding through darkness |
| [Rain on Glass](https://aarushdalal.github.io/omarchy-screensaver-studio/#rain)<br>[![Rain on Glass preview](assets/showcase/previews/rain.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#rain) | `rain` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/rain.webm) | Quiet droplets, soft night lights and reflections |
| [Floating Clock](https://aarushdalal.github.io/omarchy-screensaver-studio/#clock)<br>[![Floating Clock preview](assets/showcase/previews/clock.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#clock) | `clock` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/clock.webm) | Clean typography, orbital halo and date |
| [Aurora](https://aarushdalal.github.io/omarchy-screensaver-studio/#aurora)<br>[![Aurora preview](assets/showcase/previews/aurora.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#aurora) | `aurora` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/aurora.webm) | Slow luminous ribbons and drifting stardust |
| [Topography](https://aarushdalal.github.io/omarchy-screensaver-studio/#topography)<br>[![Topography preview](assets/showcase/previews/topography.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#topography) | `topography` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/topography.webm) | Living islands traced by nested contour lines |

### Space & Motion

| Screensaver | Mode ID | Preview | Description |
|---|---|---|---|
| [Celestial Orbit](https://aarushdalal.github.io/omarchy-screensaver-studio/#celestial_orbit)<br>[![Celestial Orbit preview](assets/showcase/previews/celestial_orbit.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#celestial_orbit) | `celestial_orbit` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/celestial_orbit.webm) | Elliptical planetary paths and fading trails |
| [Singularity](https://aarushdalal.github.io/omarchy-screensaver-studio/#singularity)<br>[![Singularity preview](assets/showcase/previews/singularity.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#singularity) | `singularity` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/singularity.webm) | A dark core surrounded by swirling matter |
| [Tesseract](https://aarushdalal.github.io/omarchy-screensaver-studio/#geometry)<br>[![Tesseract preview](assets/showcase/previews/geometry.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#geometry) | `geometry` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/geometry.webm) | A rotating four-dimensional wireframe |
| [Quantum Helix](https://aarushdalal.github.io/omarchy-screensaver-studio/#quantum_helix)<br>[![Quantum Helix preview](assets/showcase/previews/quantum_helix.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#quantum_helix) | `quantum_helix` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/quantum_helix.webm) | Continuous double strands with depth and dust |
| [Constellation](https://aarushdalal.github.io/omarchy-screensaver-studio/#particles)<br>[![Constellation preview](assets/showcase/previews/particles.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#particles) | `particles` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/particles.webm) | Drifting particles joined by delicate filaments |
| [Starfield Warp](https://aarushdalal.github.io/omarchy-screensaver-studio/#warp)<br>[![Starfield Warp preview](assets/showcase/previews/warp.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#warp) | `warp` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/warp.webm) | Perspective stars and flowing light trails |
| [Synthwave Horizon](https://aarushdalal.github.io/omarchy-screensaver-studio/#synthwave)<br>[![Synthwave Horizon preview](assets/showcase/previews/synthwave.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#synthwave) | `synthwave` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/synthwave.webm) | A distant striped sun over a wireframe landscape |

### Digital & Live

| Screensaver | Mode ID | Preview | Description |
|---|---|---|---|
| [Cyber Nexus](https://aarushdalal.github.io/omarchy-screensaver-studio/#cyber_nexus)<br>[![Cyber Nexus preview](assets/showcase/previews/cyber_nexus.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#cyber_nexus) | `cyber_nexus` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/cyber_nexus.webm) | Honeycomb circuitry with travelling signals |
| [Matrix Rain](https://aarushdalal.github.io/omarchy-screensaver-studio/#matrix)<br>[![Matrix Rain preview](assets/showcase/previews/matrix.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#matrix) | `matrix` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/matrix.webm) | Cascading Katakana and phosphor trails |
| [Audio Visualizer](https://aarushdalal.github.io/omarchy-screensaver-studio/#visualizer)<br>[![Audio Visualizer preview](assets/showcase/previews/visualizer.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#visualizer) | `visualizer` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/visualizer.webm) | Live spectrum, falling peaks and low/mid/high activity |
| [System Cockpit](https://aarushdalal.github.io/omarchy-screensaver-studio/#system)<br>[![System Cockpit preview](assets/showcase/previews/system.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#system) | `system` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/system.webm) | Staggered gauge startup and daily/lifetime SSD telemetry |
| [Diagnostic Stream](https://aarushdalal.github.io/omarchy-screensaver-studio/#terminal)<br>[![Diagnostic Stream preview](assets/showcase/previews/terminal.gif)](https://aarushdalal.github.io/omarchy-screensaver-studio/#terminal) | `terminal` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/terminal.webm) | A borderless stream of system activity |

### DAEMON Satisfying

| Screensaver | Mode ID | Preview | Description |
|---|---|---|---|
| [Harmonograph](https://aarushdalal.github.io/omarchy-screensaver-studio/#harmonograph) | `harmonograph` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/harmonograph.webm) | Rotary-table coupled pendulum rosettes |
| [Infinite Ripples](https://aarushdalal.github.io/omarchy-screensaver-studio/#infinite_ripples) | `infinite_ripples` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/infinite_ripples.webm) | Fluid surface wave propagation and interference |
| [The Perfect Machine](https://aarushdalal.github.io/omarchy-screensaver-studio/#the_perfect_machine) | `the_perfect_machine` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/the_perfect_machine.webm) | Interlocking precision gear train kinematics |
| [Ink Singularity](https://aarushdalal.github.io/omarchy-screensaver-studio/#ink_singularity) | `ink_singularity` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/ink_singularity.webm) | Vortex dye advection and filament transport |
| [Zen Geometry](https://aarushdalal.github.io/omarchy-screensaver-studio/#zen_geometry) | `zen_geometry` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/zen_geometry.webm) | Concentric multi-pass geometric rosette drawing |
| [Fractal Bloom](https://aarushdalal.github.io/omarchy-screensaver-studio/#fractal_bloom) | `fractal_bloom` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/fractal_bloom.webm) | Recursive blooming branch growth and breath |
| [Particle Architect](https://aarushdalal.github.io/omarchy-screensaver-studio/#particle_architect) | `particle_architect` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/particle_architect.webm) | Smooth coordinate-arcing geometric formations |
| [Harmonic Sculpture](https://aarushdalal.github.io/omarchy-screensaver-studio/#harmonic_sculpture) | `harmonic_sculpture` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/harmonic_sculpture.webm) | Projected 3D Lissajous ribbon sculpture |
| [Circuit Genesis](https://aarushdalal.github.io/omarchy-screensaver-studio/#circuit_genesis) | `circuit_genesis` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/circuit_genesis.webm) | Growing orthogonal conductor traces and bus lines |
| [Circuit Weaver](https://aarushdalal.github.io/omarchy-screensaver-studio/#circuit_weaver) | `circuit_weaver` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/circuit_weaver.webm) | Deterministic A* routing with obstacle clearance |
| [Mechanical Eternity](https://aarushdalal.github.io/omarchy-screensaver-studio/#mechanical_eternity) | `mechanical_eternity` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/mechanical_eternity.webm) | Planetary clockwork stage and balance mechanism |
| [Silk Continuum](https://aarushdalal.github.io/omarchy-screensaver-studio/#silk_continuum) | `silk_continuum` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/silk_continuum.webm) | Braided spatial ribbons with stiffness physics |
| [Infinite Marble Machine](https://aarushdalal.github.io/omarchy-screensaver-studio/#infinite_marble_machine) | `infinite_marble_machine` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/infinite_marble_machine.webm) | Arc-length integrated velocity roller track |
| [Domino Architect](https://aarushdalal.github.io/omarchy-screensaver-studio/#domino_architect) | `domino_architect` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/domino_architect.webm) | Assembled branching domino chain cascade |
| [Wave Field](https://aarushdalal.github.io/omarchy-screensaver-studio/#wave_field) | `wave_field` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/wave_field.webm) | Spatial oscillating matrix of height pins |
| [Orbital Synchronization](https://aarushdalal.github.io/omarchy-screensaver-studio/#orbital_synchronization) | `orbital_synchronization` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/orbital_synchronization.webm) | Multi-ring resonance returning to coplanar phase |
| [Infinite Origami](https://aarushdalal.github.io/omarchy-screensaver-studio/#infinite_origami) | `infinite_origami` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/infinite_origami.webm) | Continuous spatial panel folding kinematics |
| [Monolithic Construction](https://aarushdalal.github.io/omarchy-screensaver-studio/#monolithic_construction) | `monolithic_construction` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/monolithic_construction.webm) | Spatial arch block assembly and placement |
| [Midnight Rain](https://aarushdalal.github.io/omarchy-screensaver-studio/#midnight_rain) | `midnight_rain` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/midnight_rain.webm) | Glass-plane droplet kinematics and volume merge |
| [Liquid Obsidian](https://aarushdalal.github.io/omarchy-screensaver-studio/#liquid_obsidian) | `liquid_obsidian` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/liquid_obsidian.webm) | Smooth minimum distance-field raymarching |
| [Mercury Garden](https://aarushdalal.github.io/omarchy-screensaver-studio/#mercury_garden) | `mercury_garden` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/mercury_garden.webm) | Attracted liquid metal droplets with high specularity |
| [Event Horizon](https://aarushdalal.github.io/omarchy-screensaver-studio/#event_horizon) | `event_horizon` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/event_horizon.webm) | Gravitational lensing starfield deflection |
| [Infinite Zen Garden](https://aarushdalal.github.io/omarchy-screensaver-studio/#infinite_zen_garden) | `infinite_zen_garden` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/infinite_zen_garden.webm) | Procedural multi-tine sand rake grooves |
| [Ink Choreography](https://aarushdalal.github.io/omarchy-screensaver-studio/#ink_choreography) | `ink_choreography` | [WebM](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/download/v2.0.0-beta.7/ink_choreography.webm) | Symmetric dual-emitter fluid choreography |

See [recording details](docs/SHOWCASE.md) for capture provenance and formats.

---

## Requirements

- **Operating System**: Arch Linux (rolling release, x86_64)
- **Desktop Shell**: Omarchy (`dev (13f18b2c) / 4.0.2`) with Quickshell (`0.3.1`)
- **Compositor**: Hyprland (`0.56.2`)
- **Runtime Dependencies**: `python3`, `gtk4`, `python-gobject`, `cairo`, `jq`, `python-numpy`, and EGL/OpenGL ES 3.0 drivers (`mesa` on supported Intel/AMD hardware)
- **Optional (for Audio Spectrum)**: `pipewire-pulse`, `libpulse`, `gcc`
- **Optional (for Terminal TUI)**: `gum`

---

## Compatibility

| Component | Tested Version | Compatibility Status |
|---|---|---|
| Omarchy | `dev (13f18b2c) / 4.0.2` | Fully compatible |
| Quickshell | `0.3.1` | Fully compatible |
| Hyprland | `0.56.2` | Fully compatible |
| GTK | GTK4 Wayland | Fully compatible |

---

## Installation

### Method 1: Using Omarchy Plugin Manager (Recommended)

```bash
omarchy plugin add https://github.com/aarushdalal/omarchy-screensaver-studio.git --enable
```

### Method 2: Using the Safe User Installer

```bash
git clone --branch v2.0.0-beta.7 https://github.com/aarushdalal/omarchy-screensaver-studio.git
cd omarchy-screensaver-studio

./install.sh check
./install.sh install --dry-run
./install.sh install
```

---

## System Setup Before Installation

1. Install GTK4 PyGObject dependencies:
   ```bash
   sudo pacman -S gtk4 python-gobject cairo jq python-numpy mesa
   ```
2. Optional — audio development headers for the spectrum visualizer:
   ```bash
   sudo pacman -S libpulse base-devel
   ```
3. Optional — terminal TUI manager:
   ```bash
   sudo pacman -S gum
   ```

---

## Configuration Guide

See [**docs/CONFIGURATION.md**](docs/CONFIGURATION.md) for detailed per-mode TOML parameter specifications, theme overrides, and OLED settings.

---

## Usage

- **Preview Any Mode for 5 Seconds**:
  ```bash
  omarchy-screensaver-preview matrix 5
  omarchy-screensaver-preview warp 5
  omarchy-screensaver-preview geometry 5
  omarchy-screensaver-preview singularity 5
  omarchy-screensaver-preview harmonograph 10
  ```
- **Open Interactive Mode HUD**:
  ```bash
  omarchy-menu-screensaver
  ```
- **Open Terminal TUI Manager**:
  ```bash
  omarchy-screensaver-menu
  ```
- **Switch Default Mode**:
  ```bash
  omarchy-screensaver-select mode singularity
  ```
- **Toggle Ambient Study Display**:
  ```bash
  omarchy-screensaver-toggle
  ```

---

## Update

```bash
omarchy plugin update daemon0.screensaver-studio
```

---

## Uninstall

```bash
./install.sh uninstall
# Or:
omarchy plugin remove daemon0.screensaver-studio --yes
```

---

## Security and Privacy

- No external network requests are made.
- Audio capture (if enabled) analyzes local frequency amplitudes only and never records, stores, or transmits audio streams.

---

## Contributing

Contributions are welcome!

---

## License

[MIT License](LICENSE).

---

## Credits / Third-Party Notices

- Built for the [Omarchy](https://github.com/basecamp/omarchy) desktop environment.
- Powered by [Quickshell](https://quickshell.outfoxxed.me/), [Hyprland](https://hyprland.org/), GTK4, and [PipeWire](https://pipewire.org/).
- Not an official Omarchy product.

## Refinement and privacy update

Ambient motion · optional telemetry · private previews. The showcase gallery includes reviewed recordings; see [release privacy](docs/RELEASE-PRIVACY.md). Existing Git history is preserved.
