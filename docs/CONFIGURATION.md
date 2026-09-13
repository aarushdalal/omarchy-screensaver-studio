# Omarchy Screensaver Configuration Guide

The configuration file is located at `~/.config/omarchy-screensaver/config.toml`.

---

## Configuration Reference

### `[general]`

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | `bool` | `true` | Enables or disables the screensaver globally. |
| `mode` | `string` | `"clock"` | Active mode when launching without `--mode`. Options: `"clock"`, `"particles"`, `"terminal"`, `"system"`, `"visualizer"`, `"aurora"`, `"auto"`. |
| `rotation` | `bool` | `false` | When true, automatically cycles between visual modes during screensaver operation. |
| `rotation_interval` | `int` | `300` | Seconds between each mode change during automatic rotation. |
| `rotation_modes` | `array` | `["clock", "particles", ...]` | Ordered list of modes to cycle through when rotation is active. |
| `theme` | `string` | `"auto"` | Palette selection. Set to `"auto"` to match active Omarchy desktop theme (`colors.toml`), or specify a custom theme file name from `themes/` (e.g. `"cyberpunk"`, `"matrix"`, `"minimal"`, `"aurora"`, `"osaka"`). |

---

### `[display]`

| Key | Type | Default | Description |
|---|---|---|---|
| `fps` | `int` | `60` | Target framerate on AC power. |
| `multi_monitor` | `string` | `"independent"` | Multi-monitor mode: `"independent"` (independent window and animation seeds per display), `"mirror"` (same visuals across all screens), `"single"` (focused or primary monitor only). |
| `exit_on_mouse_move` | `bool` | `true` | Exit screensaver when mouse motion is detected. |
| `mouse_move_threshold` | `int` | `12` | Distance in pixels mouse must move before triggering exit (prevents accidental trackpad jitter from closing screensaver). |
| `exit_on_key_press` | `bool` | `true` | Exit screensaver on any keyboard key press. |
| `burn_in_protection` | `bool` | `true` | Applies very slow, imperceptible sinusoidal position drift (12px over 15 mins) to prevent OLED/IPS panel pixel retention. |

---

### `[ambient]`

Settings applied when screensaver is toggled as an **ambient study desk display** (`omarchy-screensaver-toggle` / `SUPER + I`):

| Key | Type | Default | Description |
|---|---|---|---|
| `exit_on_mouse_move` | `bool` | `false` | When false, accidental mouse nudges or desk vibrations while studying will not dismiss the ambient display. |
| `mouse_move_threshold` | `int` | `100` | Minimum mouse movement distance in pixels to trigger dismissal if `exit_on_mouse_move` is enabled. |
| `exit_on_key_press` | `bool` | `false` | When false, key presses will not close the display (only the `SUPER + I` shortcut can toggle it). |
| `exit_on_mouse_click` | `bool` | `false` | When false, mouse clicks will not close the display. |

---

### `[performance]`

| Key | Type | Default | Description |
|---|---|---|---|
| `profile` | `string` | `"balanced"` | Preset performance profile. Options: `"low"` (caps FPS to 30, reduces particles by 50%), `"balanced"` (optimal efficiency), `"high"` (maximum particle density and shader rich effects). |

---

### `[battery]`

| Key | Type | Default | Description |
|---|---|---|---|
| `auto_detect` | `bool` | `true` | Automatically detect when laptop is unplugged from AC power. |
| `reduce_fps` | `bool` | `true` | Throttles framerate when running on battery power. |
| `battery_fps` | `int` | `30` | Maximum framerate when running on battery power. |
| `particle_multiplier` | `float` | `0.5` | Density multiplier applied to particle systems on battery power. |

---

### `[clock]`

| Key | Type | Default | Description |
|---|---|---|---|
| `format_24h` | `bool` | `true` | 24-hour time format (`14:27`) vs 12-hour format (`02:27 PM`). |
| `show_seconds` | `bool` | `false` | Display seconds counter alongside hours and minutes. |
| `show_date` | `bool` | `true` | Display weekday and formatted date below the clock. |
| `show_system_info` | `bool` | `true` | Display CPU, RAM, Battery, and Uptime status pill. |
| `colon_blink` | `bool` | `true` | Gently breathes the colon separator (`:`) with a smooth sinusoidal pulse. |

---

### `[particles]`

| Key | Type | Default | Description |
|---|---|---|---|
| `count` | `int` | `160` | Number of ambient particles (scaled on battery or small resolutions). |
| `speed` | `float` | `0.18` | Velocity scale of particle movement. |
| `connection_distance` | `int` | `120` | Proximity distance in pixels for drawing dynamic connection lines. |
| `particle_size` | `float` | `1.8` | Base particle radius in pixels. |
| `glow` | `bool` | `true` | Renders a subtle glowing outer corona around each particle. |

---

### `[terminal]`

| Key | Type | Default | Description |
|---|---|---|---|
| `cursor_blink_rate` | `float` | `0.55` | Rate in seconds for terminal block cursor blinking. |
| `show_real_metrics` | `bool` | `true` | Pulls live CPU, RAM, battery, network, and storage from `/proc` and `/sys`. |
| `event_interval` | `float` | `3.5` | Seconds between new diagnostic event log entries. |
| `max_log_lines` | `int` | `12` | Maximum log lines maintained in the scrolling terminal backlog. |

---

### `[system]`

| Key | Type | Default | Description |
|---|---|---|---|
| `graph_history_points` | `int` | `50` | Number of historical samples plotted on the live area sparkline charts. |
| `update_interval` | `float` | `0.8` | Telemetry polling rate in seconds. |

---

### `[visualizer]`

| Key | Type | Default | Description |
|---|---|---|---|
| `style` | `string` | `"spectrum"` | Audio visualization style (`"spectrum"` equalizer). |
| `bar_count` | `int` | `36` | Number of frequency spectrum equalizer bars. |
| `auto_switch_on_play` | `bool` | `true` | Automatically switch to visualizer mode if media playback begins while screensaver is active. |
| `fallback_mode` | `string` | `"selected"` | Action when audio pauses: `"selected"` (reverts back to user's selected visual mode), `"idle"` (stays on visualizer showing paused track), or any mode name. |

---

### `[aurora]`

| Key | Type | Default | Description |
|---|---|---|---|
| `speed` | `float` | `0.25` | Speed multiplier for undulating light wave ribbons. |
| `wave_count` | `int` | `4` | Number of flowing cubic spline wave ribbons rendered. |
| `dust_count` | `int` | `60` | Number of floating ambient dust particles. |

---

## Creating Custom Themes

To create a custom palette, create a file in `~/.config/omarchy-screensaver/themes/<my-theme>.toml`:

```toml
name = "neon-synth"
description = "High-contrast synthwave palette"

[colors]
background = "#0d0b18"
darker_background = "#07060e"
lighter_background = "#19162e"
foreground = "#e0e6ed"
bright_foreground = "#ffffff"
muted = "#5c548a"
accent = "#ff007f"
primary = "#00f0ff"
secondary = "#ffe600"
red = "#ff2a6d"
green = "#05ffa1"
yellow = "#ffe600"
blue = "#00f0ff"
magenta = "#b537f2"
cyan = "#00f0ff"
orange = "#ff6c00"
```

Activate the theme in `config.toml`:
```toml
[general]
theme = "neon-synth"
```

Or switch themes instantly via the menu or CLI:
```bash
omarchy-screensaver-select theme neon-synth
```

---

## Interactive Menus & Quick Selection

Instead of manually editing `config.toml`, you can use the built-in menu interfaces:

1. **Omarchy Top-Bar Menu**: Open `Style -> Screensaver` in the Omarchy menu (`omarchy-menu toggle screensaver`) to click any visual mode or theme with live checkmarks.
2. **Floating HUD**: Run `omarchy-menu-screensaver` to open a quick modal selector.
3. **Interactive TUI**: Run `omarchy-screensaver-menu` to use the full-screen terminal manager.
4. **CLI Control**:
   - `omarchy-screensaver-select mode <clock|particles|terminal|system|visualizer|aurora>`
   - `omarchy-screensaver-select theme <auto|cyberpunk|matrix|aurora|osaka|minimal>`
   - `omarchy-screensaver-select rotation toggle`

