# Recorded showcases — 1.8.1

The gallery contains fresh recordings of all 18 Screensaver Studio modes from 30–31 October 2026. Eclipse, Ink Flow and Rain on Glass are new. The System Cockpit recording was refreshed again after its seven-gauge layout, larger-text update, staggered instrument startup and daily/lifetime SSD fields. Aurora Flow was captured directly from the native Cairo renderer using live desktop audio and real player metadata, with its separated track information, peak caps and band-activity meters. The recording uses the supported idle fallback setting to stay on the visualizer during quiet moments; the saved user configuration is unchanged.

- `assets/showcase/<mode>.webm`: silent 1920×1080 VP9 recording for the browser gallery.
- `assets/showcase/<mode>.mp4`: silent H.264 with fast-start playback (1920×1080 for System Cockpit and Audio Visualizer, 960×540 for other modes).
- `assets/showcase/previews/<mode>.gif`: looping 480×270, 12 FPS excerpt for GitHub README previews.
- `assets/showcase/previews/<mode>.jpg`: 960×540 still poster.
- `index.html` and `docs/index.html`: searchable galleries with explicit video controls, no autoplay and both video formats.

Most original clips are about five seconds; the refreshed cockpit clip is sixteen seconds and the visualizer is twelve seconds. The README links each GIF to the corresponding GitHub Pages player. Playback starts only after the viewer chooses it, and starting another video pauses the previous one. Both gallery locations work from a static server; the docs page uses the matching relative asset paths.

Audio streams and source metadata are removed from the published copies. Workstation identity is replaced with generic demo labels in the system footer and terminal header throughout their clips. The other telemetry and visuals remain the recorded output; estimates are labelled in the cockpit itself. Original local recordings are retained outside the public repository.

Published video/GIF/JPEG files are reviewed and recorded by SHA-256 in `tools/approved-preview-media.json`. The release privacy check rejects changed or unreviewed media. `python3 tools/build_showcase.py` rebuilds the HTML pages and README links from the 18-mode catalogue; it does not approve media checksums. Run `python3 tools/release_privacy_check.py` before publication.
