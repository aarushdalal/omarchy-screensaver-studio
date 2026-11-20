# Screensaver Studio showcase

Watch all 42 modes in the [searchable browser gallery](https://aarushdalal.github.io/omarchy-screensaver-studio/) or download one silent 1920×1080 VP9 WebM per mode from [v2.0.0-beta.7](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/tag/v2.0.0-beta.7). The [README catalogue](../README.md#showcase-gallery) lists every mode ID and links to its player and download.

Each WebM is a video preview. To run the live screensavers, install the [tagged source](../README.md#installation) and open the mode browser or run a timed preview.

```sh
omarchy-menu-screensaver
omarchy-screensaver-preview fractal_bloom 10
```

## Recording details

Most WebMs are about five seconds long and show the theme and settings used for the November showcase. System Cockpit and Diagnostic Stream use copies with generic labels in place of workstation identity. Fractal Bloom uses a nine-second offscreen capture of the released GPU renderer after the branches start growing. Its capture uses an opaque black backdrop. The 24 DAEMON Satisfying scenes are still [procedural prototypes](DAEMON-SATISFYING.md).

Both gallery pages, `index.html` and `docs/index.html`, have explicit playback controls and pause the previous video when another one starts. The 18 classic modes also have alternate MP4 recordings and animated GIF excerpts. Some of these older captures show a different palette or build. The earlier 1.8.1 System Cockpit demo shows its seven-gauge layout and staggered startup, and the Audio Visualizer demo shows spectrum peaks and band activity. Both are available from the [v1.8.1 release](https://github.com/aarushdalal/omarchy-screensaver-studio/releases/tag/v1.8.1).

Repository showcase media is checked against `tools/approved-preview-media.json`. Run `python3 tools/build_showcase.py` to regenerate both HTML pages and the README catalogue from the application registry. Run `python3 tools/release_privacy_check.py` before publishing repository changes.
