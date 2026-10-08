# Omarchy Screensaver Studio - Showcase Assets Directory

This directory stores automated visual assets and showcase recordings demonstrating all 10 native Wayland screensaver visual modes.

## Automated Recording

Videos in this directory are generated using the automated showcase suite:

```bash
# Record all discovered screensaver modes (auto-adapts to new modes)
omarchy-record-screensaver-showcase --all

# Record detached in background (safe to close terminal)
omarchy-record-screensaver-showcase --all --detach

# Record a specific mode
omarchy-record-screensaver-showcase --only warp
```

Each showcase video is recorded at **60 FPS in 1080p WebM/VP9** capturing ~5 seconds of live generative visual effects:
1. **Mode Switch**: Selected dynamically via `omarchy-screensaver-select mode <mode>`
2. **Ambient Trigger**: Triggered via exact `SUPER + I` toggle script (`omarchy-screensaver-toggle`)
3. **Capture**: 5.0 seconds of dynamic rendering on clean desktop
4. **Dismissal**: Dismissed symmetrically via `omarchy-screensaver-toggle`

---

## File Naming Convention

All screensaver mode showcase videos follow the standardized naming format:

```text
showcase_screensaver_<mode>.webm
```

### Visual Mode Video Inventory

| Mode | Showcase Video | Visual Description |
|---|---|---|
| `aurora` | [`aurora.webm`](aurora.webm) | Multi-octave harmonic spline ribbons with stardust motes |
| `celestial_orbit` | [`celestial_orbit.webm`](celestial_orbit.webm) | Gravitational multi-orbital planetary system with trajectory trails |
| `clock` | [`clock.webm`](clock.webm) | Floating typographic clock with orbital aura & telemetry |
| `cyber_nexus` | [`cyber_nexus.webm`](cyber_nexus.webm) | OLED true-black neural node constellation with data pulses |
| `geometry` | [`geometry.webm`](geometry.webm) | 4D rotating tesseract with chromatic depth glow |
| `matrix` | [`matrix.webm`](matrix.webm) | 3D parallax Katakana digital rain & phosphor decay |
| `particles` | [`particles.webm`](particles.webm) | Volumetric cosmic constellation with wandering attractor |
| `quantum_helix` | [`quantum_helix.webm`](quantum_helix.webm) | Dual counter-rotating quantum double-helix strands |
| `singularity` | [`singularity.webm`](singularity.webm) | Kerr rotating black hole with Doppler accretion disk |
| `synthwave` | [`synthwave.webm`](synthwave.webm) | 3D wireframe perspective neon horizon & gradient sun |
| `system` | [`system.webm`](system.webm) | Automotive digital cockpit HUD with tachometers, electricals & IOPS |
| `terminal` | [`terminal.webm`](terminal.webm) | Diagnostic kernel & procfs metric waterfall |
| `topography` | [`topography.webm`](topography.webm) | Fluid undulating topographic elevation contour lines |
| `visualizer` | [`visualizer.webm`](visualizer.webm) | Real-time PipeWire audio spectrum equalizer bars |
| `warp` | [`warp.webm`](warp.webm) | Relativistic 3D starfield hyperspace jump streaks |

