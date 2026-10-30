# Screensaver Studio 1.8.1

A clearer Aurora Flow audio visualizer and a staged cockpit startup.

## Audio Visualizer

Track information has its own readable space above the spectrum. Live bars now have falling peak caps, with low/mid/high activity meters and quieter aurora ribbons behind them. All colours follow the desktop palette. Audio without media-player metadata is still visualized; silence releases the measured bars to zero. A short quiet grace period prevents fallback flicker between tracks. Paused track metadata is hidden when another source supplies live sound.

The native audio worker is shared across listeners, so switching modes or closing one display does not interrupt another. Any configured 8–64 bars span the full captured frequency range. Empty player lookups are cached too.

## Staged instrument startup

The cockpit starts CPU first, then graphics and memory. Temperature, storage, load and battery follow with their own delays. Each gauge still revs to full, returns to zero and settles on its real value. Dimmed cards show WAITING, CHECK or LIVE; activity charts and detailed telemetry appear as later components. The complete sequence takes about 5.4 seconds.

The existing half-second telemetry refresh, daily/lifetime SSD readings, theme selection and study-mode controls remain available. Markdown guides explain the visualizer and every cockpit field.

## Refreshed previews and validation

Both updated displays have fresh Full HD MP4 and WebM recordings, animated README previews and posters. Public recordings are silent, with generic workstation identity in the cockpit footer.

33 rendering, telemetry, audio lifecycle, frequency coverage, signal-state and selection checks pass. Both installed modes were checked on the desktop. The cockpit capture checks window ownership and overlays throughout; the visualizer clip records its native renderer using live desktop audio and actual metadata. Live music capture stayed active after releasing one of two listeners. The media is decoded and reviewed before publication.
