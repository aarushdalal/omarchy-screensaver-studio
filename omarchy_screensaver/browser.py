"""A compact collection browser using the existing native Omarchy selector."""
import subprocess
import sys
import tomllib
from pathlib import Path
from .catalog import GROUPS, MODES, THEMES


class MenuCancelled(Exception):
    """Escape closes the studio; explicit Back rows navigate between pages."""


def choose(title, rows):
    """Rows contain icon, unique label, detail and a private action token."""
    result = subprocess.run(['omarchy-menu-select', title, '--', '--width', '780', '--height', '520'],
                            input='\n'.join('\t'.join(row[:3]) for row in rows) + '\n',
                            text=True, capture_output=True)
    if result.returncode or not result.stdout.strip():
        raise MenuCancelled()
    selected = result.stdout.strip()
    for icon, label, detail, token in rows:
        if selected in (label, label + '\t' + detail, icon + '\t' + label, icon + '\t' + label + '\t' + detail):
            return token
    return None


def run(*args):
    return subprocess.run(list(args), check=False).returncode


def state():
    try:
        with (Path.home() / '.config/omarchy-screensaver/config.toml').open('rb') as f:
            return tomllib.load(f).get('general', {})
    except (OSError, ValueError):
        return {}


def browse(group, preview=False):
    while True:
        current = state().get('mode', 'clock')
        rows = [(icon, label + ('  ✓' if key == current else ''), detail, key)
                for key, label, icon, detail, collection in MODES if group == 'all' or collection == group]
        rows.append(('󰁍', 'Back', 'Return to Screensaver Studio', 'back'))
        title = ('Preview · ' if preview else '') + (GROUPS[group][0] if group in GROUPS else 'All Screensavers')
        mode = choose(title, rows)
        if mode is None or mode == 'back':
            return
        if preview:
            run('omarchy-screensaver-preview', mode, '12')
            continue
        if run('omarchy-screensaver-select', 'mode', mode) == 0:
            return True


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else ''
    if page in ('--themes', 'themes'):
        theme = choose('Colour Palette', [('󰏘', label, detail, key) for key, label, detail in THEMES])
        if theme:
            run('omarchy-screensaver-select', 'theme', theme)
        return
    if page in ('--preview-picker', 'preview-picker'):
        browse('all', preview=True)
        return
    if page in GROUPS:
        browse(page)
        return
    while True:
        cfg = state()
        current = cfg.get('mode', 'clock')
        # Every screensaver is directly searchable here; no collection drill-down.
        ordered = sorted(MODES, key=lambda row: row[0] != current)
        rows = [(icon, label + ('  ✓' if key == current else ''), detail, 'mode:' + key)
                for key, label, icon, detail, group in ordered]
        rows.extend([
            ('󱄄', 'Preview Screensavers', 'Try any design for 12 seconds without selecting', 'preview'),
            ('󰏘', 'Follow Desktop Colours' + ('  ✓' if cfg.get('theme', 'auto') == 'auto' else ''),
             'Keep every scene matched to your active desktop palette', 'desktop-colours'),
            ('󰑖', 'Auto-Rotation · ' + ('On' if cfg.get('rotation') else 'Off'),
             'Cycle through your configured rotation list', 'rotation'),
            ('󰐥', 'Start Selected Screensaver', 'Open your selection fullscreen', 'start'),
            ('⚙', 'Settings', 'Open screensaver settings', 'settings'),
        ])
        action = choose('Choose Screensaver · type a name to search', rows)
        if action is None:
            return
        if action.startswith('mode:'):
            if run('omarchy-screensaver-select', 'mode', action[5:]) == 0:
                return
        elif action == 'preview':
            browse('all', preview=True)
        elif action == 'desktop-colours':
            if run('omarchy-screensaver-select', 'theme', 'auto') == 0:
                return
        elif action == 'rotation':
            run('omarchy-screensaver-select', 'rotation', 'toggle')
        elif action == 'start':
            run('omarchy-launch-screensaver', 'force')
            return
        elif action == 'settings':
            run('omarchy-launch-config-editor', str(Path.home() / '.config/omarchy-screensaver/config.toml'))
            return


if __name__ == '__main__':
    try:
        main()
    except MenuCancelled:
        pass
