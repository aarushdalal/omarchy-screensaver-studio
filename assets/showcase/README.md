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
| `aurora` | [`showcase_screensaver_aurora.webm`](showcase_screensaver_aurora.webm) | Multi-octave harmonic spline ribbons with stardust motes |
| `clock` | [`showcase_screensaver_clock.webm`](showcase_screensaver_clock.webm) | Floating typographic clock with orbital aura & telemetry |
| `geometry` | [`showcase_screensaver_geometry.webm`](showcase_screensaver_geometry.webm) | 4D rotating tesseract with chromatic depth glow |
| `matrix` | [`showcase_screensaver_matrix.webm`](showcase_screensaver_matrix.webm) | 3D parallax Katakana digital rain & phosphor decay |
| `particles` | [`showcase_screensaver_particles.webm`](showcase_screensaver_particles.webm) | Volumetric cosmic constellation with wandering attractor |
| `singularity` | [`showcase_screensaver_singularity.webm`](showcase_screensaver_singularity.webm) | Kerr rotating black hole with Doppler accretion disk |
| `system` | [`showcase_screensaver_system.webm`](showcase_screensaver_system.webm) | Holographic telemetry HUD with tachometers & Bezier sparklines |
| `terminal` | [`showcase_screensaver_terminal.webm`](showcase_screensaver_terminal.webm) | Diagnostic kernel & procfs metric waterfall |
| `visualizer` | [`showcase_screensaver_visualizer.webm`](showcase_screensaver_visualizer.webm) | Real-time PipeWire audio spectrum equalizer bars |
| `warp` | [`showcase_screensaver_warp.webm`](showcase_screensaver_warp.webm) | Relativistic 3D starfield hyperspace jump streaks |
