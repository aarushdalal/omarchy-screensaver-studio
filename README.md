# Screensaver Studio (`omarchy-screensaver-studio`)

> **Unofficial / Community Project**: An independent screensaver suite for Omarchy.

A multi-mode Wayland screensaver engine featuring generative visual animations, system diagnostics, dynamic theme synchronization, and optional audio visualization for Omarchy Hyprland.

---

## Status / Experimental Warning

This project contains native Python GTK4 rendering code and optional C extensions. **It excludes pre-compiled binary objects (`.so`) from the public repository.** Build tools (`gcc`, `libpulse`) are required only if you desire real-time audio reactivity. Framerate, rendering overhead, and battery consumption will vary depending on your GPU driver and CPU architecture.

---

## Features

- **6 Signature Visual Modes**:
  - `clock`: Minimalist typography with breathing colon, date, and status pills.
  - `particles`: Constellation network with proximity filaments and kinetic drift.
  - `terminal`: Simulated futuristic kernel audit and diagnostic logs.
  - `system`: Live CPU, memory, and battery sparklines and telemetry gauges.
  - `visualizer`: Real-time reactive equalizer bars with MPRIS media integration.
  - `aurora`: Flowing color wave curtains with celestial stardust.
- **Dynamic Palette Synchronizer**: Inherits color schemes dynamically from the active Omarchy theme (`colors.toml`) or built-in presets (`aurora`, `cyberpunk`, `matrix`, `minimal`, `osaka`).
- **Interactive Floating HUD**: Floating modal menu (`omarchy-menu-screensaver`) and top-bar integration.
- **Idle Lifecycle Integration**: Declared under application ID `org.omarchy.screensaver`, integrating with Quickshell idle services and dismissing instantly on keyboard or mouse input.

---

## Requirements

- **Operating System**: Arch Linux (rolling release, x86_64)
- **Desktop Shell**: Omarchy (`dev (13f18b2c) / 4.0.2`) with Quickshell (`0.3.1`)
- **Compositor**: Hyprland (`0.56.2`)
- **Runtime Dependencies**: `python3`, `gtk4`, `python-gobject`, `cairo`
- **Optional (for Audio Spectrum Visualizer)**: `pipewire-pulse`, `libpulse`, `gcc`

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

### Method 1: Using Omarchy Plugin Manager

```bash
omarchy plugin add https://github.com/YOUR-USERNAME/omarchy-screensaver-studio.git --enable
```

### Method 2: Using the Safe User Installer

```bash
git clone https://github.com/YOUR-USERNAME/omarchy-screensaver-studio.git
cd omarchy-screensaver-studio

./install.sh check
./install.sh install --dry-run
./install.sh install
```

---

## System Setup Before Installation

1. Install GTK4 PyGObject dependencies on Arch Linux:
   ```bash
   sudo pacman -S gtk4 python-gobject cairo
   ```
2. Optional audio development headers:
   ```bash
   sudo pacman -S libpulse base-devel
   ```

---

## Usage

- **Preview Any Mode for 5 Seconds**:
  ```bash
  omarchy-screensaver-preview particles 5
  ```
- **Open Interactive Mode HUD**:
  ```bash
  omarchy-menu-screensaver
  ```
- **Switch Default Mode**:
  ```bash
  omarchy-screensaver-select mode aurora
  ```

---

## Update

```bash
omarchy plugin update daemon0.screensaver-studio
```

---

## Uninstall / Rollback

```bash
./install.sh uninstall
```

---

## Security and Privacy

- No external network requests are made.
- Audio capture (if enabled) analyzes local frequency amplitudes only and never records, stores, or transmits audio streams.

---

## Showcase

> Visual previews, UI screenshots, and recordings for documentation and release verification.

### Main experience

<!-- Future image: assets/showcase/screensaver-hero.png -->
<!-- ![Main desktop experience](assets/showcase/screensaver-hero.png) -->

### Feature gallery

<!-- Future image: assets/showcase/screensaver-clock.png -->
<!-- ![screensaver-clock.png](assets/showcase/screensaver-clock.png) -->

<!-- Future image: assets/showcase/screensaver-particles.png -->
<!-- ![screensaver-particles.png](assets/showcase/screensaver-particles.png) -->

<!-- Future image: assets/showcase/screensaver-terminal.png -->
<!-- ![screensaver-terminal.png](assets/showcase/screensaver-terminal.png) -->

<!-- Future image: assets/showcase/screensaver-system.png -->
<!-- ![screensaver-system.png](assets/showcase/screensaver-system.png) -->

<!-- Future image: assets/showcase/screensaver-visualizer.png -->
<!-- ![screensaver-visualizer.png](assets/showcase/screensaver-visualizer.png) -->

<!-- Future image: assets/showcase/screensaver-aurora.png -->
<!-- ![screensaver-aurora.png](assets/showcase/screensaver-aurora.png) -->

<!-- Future image: assets/showcase/feature-07.png -->
<!-- ![Feature preview 7](assets/showcase/feature-07.png) -->

<!-- Future image: assets/showcase/feature-08.png -->
<!-- ![Feature preview 8](assets/showcase/feature-08.png) -->

<!-- Future image: assets/showcase/feature-09.png -->
<!-- ![Feature preview 9](assets/showcase/feature-09.png) -->

<!-- Future image: assets/showcase/feature-10.png -->
<!-- ![Feature preview 10](assets/showcase/feature-10.png) -->

### Motion and interaction

<!-- Future GIF: assets/showcase/interaction-01.gif -->
<!-- ![Interaction preview](assets/showcase/interaction-01.gif) -->

<!-- Future GIF: assets/showcase/interaction-02.gif -->
<!-- ![Transition preview](assets/showcase/interaction-02.gif) -->

### Video demonstrations

<!-- Future thumbnail: assets/showcase/video-01-thumbnail.png -->
<!-- [![Watch demo video](assets/showcase/video-01-thumbnail.png)](https://github.com/YOUR-USERNAME/PROJECT-NAME/releases) -->


---

## Contributing

Contributions are welcome!

---

## License

[MIT License](LICENSE).
