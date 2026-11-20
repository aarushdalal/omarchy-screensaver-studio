# Screensaver Studio release notes

## 2.0.0-beta.7 — Complete showcase downloads & lock screen blur alignment

The 2.0 beta ships 42 installable modes across four collections. The [beta.7 prerelease](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/tag/v2.0.0-beta.7) aligns the wallpaper backdrop with the native lock screen method (fast half-resolution downsampling, 12px Gaussian blur, bilinear upscale, zero black blend dimming, and direct reuse of `~/.cache/omarchy/lockscreen/background-blur.png`), adds CAVA audio spectrum smoothing, and adds 42 individual WebM previews. Use the release’s **Source code** archive or a clone of the tag to install the live screensavers. See the [mode catalogue](../README.md#showcase-gallery) for names and launch IDs, and [recording details](SHOWCASE.md) for the preview formats and capture scope.

## Screensaver Studio 1.9.0 — Background-only glass

Adds `[display] background_opacity`, bounded to 0–1. The default is 1.0; 0.68 is the current recommended dark glass setting for a configured desktop. GTK window/drawing backgrounds are transparent, while each mode replaces its base paint using Cairo SOURCE. Repeated frames no longer accumulate toward opaque black, and foreground text, cockpit gauges and effects retain their normal opacity.

Keep compositor window opacity at 100% and enable its blur. Config changes are picked up by the existing reload path; a newly installed renderer is loaded on the next screensaver launch. No live apps are restarted by these changes.

All 37 rendering, telemetry, audio and configuration tests pass, including new pixel tests for alpha, retained foreground opacity and repeated-frame replacement. Installed CSS parsed cleanly. Live wallpaper/blur appearance was deferred to avoid opening the screensaver over ongoing work; existing showcase captures describe version 1.8.1 and earlier.
