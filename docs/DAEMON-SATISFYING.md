# DAEMON Satisfying — 2.0.0-beta.1

This preview adds 24 procedural modes alongside the original 18. Select **DAEMON Satisfying** in the existing Screensaver Studio menu, or run a timed preview:

```sh
omarchy-screensaver-preview harmonograph 10
```

The collection uses GTK4 GLArea and system GLES3. Methods include retained pendulum drawing, feedback-buffer waves and dye transport, explicit gear and construction meshes, and A* circuit routing. Ink is fluid-inspired transport, not an incompressible fluid solver. Metallic effects use controlled implicit volumes, not simulated viscosity or surface tension. Ribbons and folds use prescribed geometry, not cloth or paper physics.

Actual evidence covers sampled Radeon rendering of all 24 modes and a ten-second native studio preview: 225 render callbacks, initialized GPU engine, no reported GL errors, preserved fixture PID/ambient markers, and clean process exit. CPU regression/integration tests also pass. These checks do not certify final visual quality, live lock/unlock, theme-change events, DPMS, multi-monitor behavior, long runtimes or power use.

## Current limitations

- Origami currently folds an accordion sheet; the intended additional sculptures are incomplete.
- Marble Machine has three continuous closed routes. Elevators, spiral courses and richer mechanical transfers remain incomplete.
- Some effects still need independent motion and comfort review, including ink refinement.
- Favorites, disabled entries, playlists, parameters and preset import/export have a settings backend. A complete controls UI is not included. Playlist storage alone does not replace the existing Studio rotation controller.
- Secure locking remains the existing compositor/idle service's responsibility. No authentication or lock timing is changed by this collection.
- Full profile/power and extended stability validation is pending. Metallic-fluid internal resolution is capped by profile to limit HiDPI raymarching cost. Software rendering is unsupported for validated playback.

## Advanced settings

```sh
omarchy-satisfying-settings --help
omarchy-satisfying-settings --show
omarchy-satisfying-settings --quality balanced
omarchy-satisfying-settings --toggle-favorite harmonograph
omarchy-satisfying-settings --disable infinite_origami
omarchy-satisfying-settings --set-param harmonograph line_width=1.5
omarchy-satisfying-settings --export ~/satisfying-backup.json
```

Settings live in `~/.config/omarchy-screensaver/satisfying.json`. Most collection settings apply when a mode is next created. Existing mode/palette/rotation settings remain in the normal Studio configuration. Theme accents reuse the existing palette owner; there is no second theme manager.

No desktop captures, private terminal records, account data or credentials are included in the release. This beta is not final acceptance of the full 24-effect creative brief.
