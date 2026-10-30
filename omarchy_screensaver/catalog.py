"""Single display catalogue for native and terminal screensaver browsers."""
GROUPS = {
    'quiet': ('Quiet Focus', '󰒲', 'Slow, spacious scenes for your desk'),
    'space': ('Space & Motion', '󰐎', 'Orbits, geometry and distant horizons'),
    'digital': ('Digital & Live', '󰎈', 'Circuits, music and live system displays'),
}
# key, label, icon, short description, collection
MODES = [
    ('eclipse', 'Eclipse', '󰖔', 'A lunar silhouette with a breathing solar corona', 'quiet'),
    ('ink_flow', 'Ink Flow', '󰘔', 'Layered silk filaments folding through darkness', 'quiet'),
    ('rain', 'Rain on Glass', '󰖖', 'Quiet droplets, soft night lights and reflections', 'quiet'),
    ('clock', 'Floating Clock', '󱑂', 'Clean typography, orbital halo and date', 'quiet'),
    ('aurora', 'Aurora', '󰒲', 'Slow luminous ribbons and drifting stardust', 'quiet'),
    ('topography', 'Topography', '󰮈', 'Living islands traced by nested contour lines', 'quiet'),
    ('celestial_orbit', 'Celestial Orbit', '󰇯', 'Elliptical planetary paths and fading trails', 'space'),
    ('singularity', 'Singularity', '󰇯', 'A dark core surrounded by swirling matter', 'space'),
    ('geometry', 'Tesseract', '󰦪', 'A rotating four-dimensional wireframe', 'space'),
    ('quantum_helix', 'Quantum Helix', '󰘔', 'Continuous double strands with depth and dust', 'space'),
    ('particles', 'Constellation', '󰘔', 'Drifting particles joined by delicate filaments', 'space'),
    ('warp', 'Starfield Warp', '󰐎', 'Perspective stars and flowing light trails', 'space'),
    ('synthwave', 'Synthwave Horizon', '󰾏', 'A distant striped sun over a wireframe landscape', 'space'),
    ('cyber_nexus', 'Cyber Nexus', '󰑮', 'Honeycomb circuitry with travelling signals', 'digital'),
    ('matrix', 'Matrix Rain', '󰅟', 'Cascading Katakana and phosphor trails', 'digital'),
    ('visualizer', 'Audio Visualizer', '󰎈', 'Live spectrum, falling peaks and low/mid/high activity', 'digital'),
    ('system', 'System Cockpit', '󰓅', 'Staggered gauge startup and daily/lifetime SSD telemetry', 'digital'),
    ('terminal', 'Diagnostic Stream', '', 'A borderless stream of system activity', 'digital'),
]
THEMES = [('auto', 'Follow Desktop', 'Use your current desktop colours'),
          ('minimal', 'Monochrome', 'Soft silver and charcoal'),
          ('osaka', 'Osaka Night', 'Muted amber and violet'),
          ('aurora', 'Nordic Aurora', 'Cool emerald and arctic hues'),
          ('cyberpunk', 'Cyberpunk', 'Electric cyan and magenta'),
          ('matrix', 'Matrix', 'Classic phosphor green')]
