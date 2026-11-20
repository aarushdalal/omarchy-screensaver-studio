#!/usr/bin/env python3
"""Rebuild the static gallery and README links from the current scene catalogue.

Media conversion/review is separate. This command never approves media checksums.
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from omarchy_screensaver.catalog import GROUPS, MODES

VERSION = (ROOT / 'VERSION').read_text().strip()
SHOWCASE = ROOT / 'assets/showcase'
RELEASE_RENDERED = {'fractal_bloom'}
PAGES = 'https://aarushdalal.github.io/omarchy-screensaver-studio/'
REPO = 'https://github.com/aarushdalal/omarchy-screensaver-studio'
RELEASE = f'{REPO}/releases/tag/v{VERSION}'
DOWNLOADS = f'{REPO}/releases/download/v{VERSION}'

STYLE = '''
:root{color-scheme:dark;--bg:#090c10;--panel:#10161c;--text:#e5eae7;--muted:#94a6a0;--accent:#9bbcaf;--line:#28362f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,sans-serif}a{color:var(--accent);text-underline-offset:4px}a:hover{color:white}a:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:5px}main{max-width:1280px;margin:auto;padding:70px 28px 48px}.eyebrow,.tag{font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}header{padding:0 0 42px;border-bottom:1px solid var(--line)}h1{font-size:clamp(42px,7vw,78px);line-height:1.05;letter-spacing:-.055em;margin:20px 0}header p{font-size:18px;max-width:710px;color:var(--muted)}nav{display:flex;gap:24px;flex-wrap:wrap;margin-top:28px}.toolbar{display:flex;justify-content:space-between;align-items:end;gap:24px;padding:34px 0 24px}.toolbar label{display:block;font-size:12px;color:var(--muted);margin-bottom:8px}input{background:#11191a;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:13px 16px;font:inherit;width:min(450px,75vw)}#count{color:var(--muted);font-size:13px;white-space:nowrap}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:var(--panel);border:1px solid var(--line);border-radius:17px;overflow:hidden;scroll-margin-top:24px}article:target{border-color:var(--accent)}article[hidden]{display:none}.cardhead{padding:23px 24px 19px;display:flex;align-items:center;gap:12px;justify-content:space-between}h2{font-size:19px;font-weight:600;line-height:1.3;margin:0;letter-spacing:-.02em}video{display:block;width:100%;aspect-ratio:16/9;background:black;object-fit:contain}.cardbody{padding:16px 24px 22px}.cardbody p{margin:0;color:var(--muted);font-size:14px;min-height:46px}.downloads{display:flex;gap:16px;margin-top:13px;font-size:12px}footer{margin-top:42px;border-top:1px solid var(--line);padding-top:24px;color:var(--muted);font-size:12px}footer p{max-width:820px}#empty{color:var(--muted)}@media(max-width:740px){main{padding:40px 18px}.gallery{grid-template-columns:1fr}.toolbar{align-items:start;flex-direction:column;gap:12px}.cardhead,.cardbody{padding-left:19px;padding-right:19px}}@media(prefers-reduced-motion:no-preference){article{transition:border-color .18s ease}}
'''
SCRIPT = '''
const search=document.querySelector('#scene-search');
const cards=[...document.querySelectorAll('article[data-search]')];
search.addEventListener('input',()=>{const query=search.value.trim().toLowerCase();let count=0;for(const card of cards){card.hidden=!card.dataset.search.includes(query);if(!card.hidden)count++}document.querySelector('#count').textContent=count+' of '+cards.length+' scenes';document.querySelector('#empty').hidden=count!==0});
for(const video of document.querySelectorAll('video'))video.addEventListener('play',()=>{for(const other of document.querySelectorAll('video'))if(other!==video)other.pause()});
'''


def gallery(prefix):
    cards = []
    assets = prefix + 'assets/showcase/'
    for key, name, _, detail, group in MODES:
        esc = html.escape
        search = ' '.join((name, key, detail, GROUPS[group][0])).lower()
        webm = f'{assets}{key}.webm'
        if key in RELEASE_RENDERED:
            webm = f'{DOWNLOADS}/{key}.webm'
        sources = [f'<source src="{webm}" type="video/webm">']
        links = [f'<a href="{webm}">WebM video</a>']
        if (SHOWCASE / f'{key}.mp4').is_file():
            sources.append(f'<source src="{assets}{key}.mp4" type="video/mp4">')
            links.append(f'<a href="{assets}{key}.mp4">MP4 video</a>')
        if (SHOWCASE / f'previews/{key}.gif').is_file():
            links.append(f'<a href="{assets}previews/{key}.gif">Animated preview</a>')
        cards.append(f'''<article id="{key}" data-search="{esc(search, quote=True)}">
<div class="cardhead"><h2>{esc(name)}</h2></div>
<video controls muted playsinline preload="none" poster="{assets}previews/{key}.jpg" aria-label="{esc(name)} recorded preview">
{''.join(sources)}
<a href="{webm}">Download {esc(name)} recording</a></video>
<div class="cardbody"><p>{esc(detail)}</p><div class="downloads">{''.join(links)}</div></div></article>''')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Watch all {len(MODES)} Screensaver Studio scenes, including the DAEMON Satisfying procedural collection.">
<title>Screensaver Studio {VERSION} · All {len(MODES)} recorded previews</title><style>{STYLE}</style></head>
<body><main><header><div class="eyebrow">Omarchy community · Version {VERSION}</div><h1>Motion for a<br>quieter desktop.</h1><p>{len(MODES)} screensavers across Quiet Focus, Space &amp; Motion, Digital &amp; Live, and DAEMON Satisfying.</p>
<nav aria-label="Project links"><a href="{REPO}#readme">Read the guide</a><a href="{RELEASE}">Release and downloads</a><a href="{REPO}/blob/main/docs/CONFIGURATION.md">Controls &amp; settings</a></nav></header>
<section aria-label="Recorded screensavers"><div class="toolbar"><div><label for="scene-search">Find a screensaver</label><input id="scene-search" type="search" placeholder="Search Clock, Eclipse, Rain…" autocomplete="off"></div><span id="count" aria-live="polite">{len(MODES)} scenes · click play to watch</span></div><p id="empty" hidden>No matching scenes. Try another name.</p><div class="gallery">{''.join(cards)}</div></section>
<footer><p>Silent previews from different builds and palettes. Install Screensaver Studio to run the live modes.</p><p><a href="{REPO}/blob/main/docs/SHOWCASE.md">Recording details</a> · <a href="{REPO}/blob/main/docs/RELEASE-PRIVACY.md">Release privacy</a> · Independent community project; not an official Omarchy product.</p></footer></main><script>{SCRIPT}</script></body></html>'''


def main():
    for key, *_ in MODES:
        for leaf in [f'{key}.webm', f'previews/{key}.jpg']:
            if not (SHOWCASE / leaf).is_file():
                raise SystemExit('Missing showcase media: ' + leaf)

    (ROOT / 'index.html').write_text(gallery('') + '\n')
    (ROOT / 'docs/index.html').write_text(gallery('../') + '\n')
    lines = [
        '## Showcase Gallery',
        '',
        f'**{len(MODES)} screensavers across four collections.** Choose a name to watch it in the [browser gallery]({PAGES}) or download its silent WebM from [v{VERSION}]({RELEASE}).',
        '',
        'To run the live screensavers, follow [Installation](#installation). After installing, run `omarchy-menu-screensaver` to browse the collection or `omarchy-screensaver-preview <mode-id> 10` to play a timed preview.',
    ]
    for group, (label, _, _) in GROUPS.items():
        lines.extend([
            '', f'### {label}', '',
            '| Screensaver | Mode ID | Preview | Description |', '|---|---|---|---|',
        ])
        for key, name, _, detail, mode_group in MODES:
            if mode_group != group:
                continue
            title = f'[{name}]({PAGES}#{key})'
            if (SHOWCASE / f'previews/{key}.gif').is_file():
                title += f'<br>[![{name} preview](assets/showcase/previews/{key}.gif)]({PAGES}#{key})'
            lines.append(f'| {title} | `{key}` | [WebM]({DOWNLOADS}/{key}.webm) | {detail} |')
    lines.extend(['', 'See [recording details](docs/SHOWCASE.md) for capture provenance and formats.', ''])

    readme = ROOT / 'README.md'
    text = readme.read_text()
    start = text.index('## Showcase Gallery')
    end = text.index('\n---\n\n## Requirements', start)
    readme.write_text(text[:start] + '\n'.join(lines) + text[end:])
    print(f'Updated both gallery pages and all {len(MODES)} README preview links.')


if __name__ == '__main__':
    main()
