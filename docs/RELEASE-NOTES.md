# Screensaver Studio 1.8.0

18 theme-aware screensavers, a direct searchable selector, and a clearer animated System Cockpit.

## New scenes

- Eclipse: a lunar silhouette and breathing corona.
- Ink Flow: layered filaments folding through darkness.
- Rain on Glass: quiet droplets, night lights and reflections.

## System Cockpit

A labelled startup sweep revs all seven gauges to full, back to zero, then real values. Seven gauges separate CPU/GPU/memory load from CPU temperature, storage capacity, normalized load and battery charge. Telemetry refreshes every half-second. Larger text, smooth value needles, recent-peak markers, per-core bars and processor/network histories make the hierarchy easier to read. Tracked daily disk reads/writes and lifetime SMART read/write/command counters with an endurance estimate supplement storage telemetry. Linux CPU/memory/I/O pressure joins the detailed power, disk and runtime rows. Missing sensors remain unavailable, and modeled electrical values are labelled as estimates.

## Selection and visual fixes

All 18 modes appear directly in the searchable native selector. Selecting applies and closes it; previews are separate. Running windows apply valid mode, palette and rotation edits without restarting, and reselecting a saved mode restores it after a temporary visualizer toggle. Desktop palette following works on Omarchy and DaemonOS/Caelestia. The initial size/resize path, fractional-scale effects, long media titles, Cyber Nexus circuits and orbital/helix/topographic scenes are refined.

## Fresh previews

All 18 user-recorded showcases have animated README previews and browser players at both gallery entry points. The Full HD cockpit recording includes the final larger-text layout, startup sweep and all storage fields in both MP4 and WebM. The Markdown telemetry guide explains every instrument and field. Public clips are silent; source metadata and workstation identity are removed from release copies. Original local recordings are retained separately.

## Validation

26 local regression checks cover rendering, palette changes, direct selection, live configuration, telemetry deltas, pressure semantics, peak markers and unavailable sensors. Native selection, live palette changes and the updated cockpit recording were checked on the local Hyprland desktop. Media streams, duration, links and playback are validated for this release. No new full login/logout, physical second-monitor or fingerprint-authentication test was performed.
