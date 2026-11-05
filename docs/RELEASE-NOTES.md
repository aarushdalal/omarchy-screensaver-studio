# Screensaver Studio 1.9.0 — Background-only glass

Adds `[display] background_opacity`, bounded to 0–1. The default is 1.0; 0.68 is the current recommended dark glass setting for a configured desktop. GTK window/drawing backgrounds are transparent, while each mode replaces its base paint using Cairo SOURCE. Repeated frames no longer accumulate toward opaque black, and foreground text, cockpit gauges and effects retain their normal opacity.

Keep compositor window opacity at 100% and enable its blur. Config changes are picked up by the existing reload path; a newly installed renderer is loaded on the next screensaver launch. No live apps are restarted by these changes.

All 37 rendering, telemetry, audio and configuration tests pass, including new pixel tests for alpha, retained foreground opacity and repeated-frame replacement. Installed CSS parsed cleanly. Live wallpaper/blur appearance was deferred to avoid opening the screensaver over ongoing work; existing showcase captures describe version 1.8.1 and earlier.
