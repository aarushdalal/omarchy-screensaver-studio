#!/usr/bin/env python3
"""Rebuild the static gallery and README links from the current scene catalogue.

Media conversion/review is separate. This command never approves media checksums.
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from omarchy_screensaver.catalog import MODES

NEW = {'eclipse', 'ink_flow', 'rain'}
PAGES = 'https://aarushdalal.github.io/omarchy-screensaver-studio/'
REPO = 'https://github.com/aarushdalal/omarchy-screensaver-studio'

STYLE = '''
:root{color-scheme:dark;--bg:#090c10;--panel:#10161c;--text:#e5eae7;--muted:#94a6a0;--accent:#9bbcaf;--line:#28362f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,sans-serif}a{color:var(--accent);text-underline-offset:4px}a:hover{color:white}a:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:5px}main{max-width:1280px;margin:auto;padding:70px 28px 48px}.eyebrow,.tag{font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}header{padding:0 0 42px;border-bottom:1px solid var(--line)}h1{font-size:clamp(42px,7vw,78px);line-height:1.05;letter-spacing:-.055em;margin:20px 0}header p{font-size:18px;max-width:710px;color:var(--muted)}nav{display:flex;gap:24px;flex-wrap:wrap;margin-top:28px}.toolbar{display:flex;justify-content:space-between;align-items:end;gap:24px;padding:34px 0 24px}.toolbar label{display:block;font-size:12px;color:var(--muted);margin-bottom:8px}input{background:#11191a;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:13px 16px;font:inherit;width:min(450px,75vw)}#count{color:var(--muted);font-size:13px;white-space:nowrap}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:var(--panel);border:1px solid var(--line);border-radius:17px;overflow:hidden;scroll-margin-top:24px}article:target{border-color:var(--accent)}article[hidden]{display:none}.cardhead{padding:23px 24px 19px;display:flex;align-items:center;gap:12px;justify-content:space-between}h2{font-size:19px;font-weight:600;line-height:1.3;margin:0;letter-spacing:-.02em}.new{border:1px solid #415e50;border-radius:99px;padding:2px 9px;color:#b7d2c3;font-size:10px;letter-spacing:.1em}video{display:block;width:100%;aspect-ratio:16/9;background:black;object-fit:contain}.cardbody{padding:16px 24px 22px}.cardbody p{margin:0;color:var(--muted);font-size:14px;min-height:46px}.downloads{display:flex;gap:16px;margin-top:13px;font-size:12px}footer{margin-top:42px;border-top:1px solid var(--line);padding-top:24px;color:var(--muted);font-size:12px}footer p{max-width:820px}#empty{color:var(--muted)}@media(max-width:740px){main{padding:40px 18px}.gallery{grid-template-columns:1fr}.toolbar{align-items:start;flex-direction:column;gap:12px}.cardhead,.cardbody{padding-left:19px;padding-right:19px}}@media(prefers-reduced-motion:no-preference){article{transition:border-color .18s ease}}
'''
SCRIPT = '''
const search=document.querySelector('#scene-search');
const cards=[...document.querySelectorAll('article[data-search]')];
search.addEventListener('input',()=>{const query=search.value.trim().toLowerCase();let count=0;for(const card of cards){card.hidden=!card.dataset.search.includes(query);if(!card.hidden)count++}document.querySelector('#count').textContent=count+' of '+cards.length+' scenes';document.querySelector('#empty').hidden=count!==0});
for(const video of document.querySelectorAll('video'))video.addEventListener('play',()=>{for(const other of document.querySelectorAll('video'))if(other!==video)other.pause()});
'''


def gallery(prefix):
    cards = []
    for key, name, icon, detail, group in MODES:
        esc = html.escape
        assets = prefix + 'assets/showcase/'
        badge = '<span class="new">NEW</span>' if key in NEW else ''
        cards.append(f'''<article id="{key}" data-search="{esc((name+' '+key+' '+detail).lower(), quote=True)}">
<div class="cardhead"><h2>{esc(name)}</h2>{badge}</div>
<video controls muted playsinline preload="none" poster="{assets}previews/{key}.jpg" aria-label="{esc(name)} recorded preview">
<source src="{assets}{key}.webm" type="video/webm"><source src="{assets}{key}.mp4" type="video/mp4">
<a href="{assets}{key}.mp4">Download {esc(name)} recording</a></video>
<div class="cardbody"><p>{esc(detail)}</p><div class="downloads"><a href="{assets}{key}.mp4">MP4 video</a><a href="{assets}{key}.webm">Full HD WebM</a><a href="{assets}previews/{key}.gif">Animated preview</a></div></div></article>''')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Watch all 18 Screensaver Studio 1.8.1 scenes, including Eclipse, Ink Flow, Rain on Glass and the animated System Cockpit.">
<title>Screensaver Studio 1.8.1 · All 18 recorded previews</title><style>{STYLE}</style></head>
<body><main><header><div class="eyebrow">Omarchy community · Version 1.8.1</div><h1>Motion for a<br>quieter desktop.</h1><p>18 screensavers, matched to your desktop palette. Meet Eclipse, Ink Flow and Rain on Glass, plus a clearer animated system cockpit.</p>
<nav aria-label="Project links"><a href="{REPO}#readme">Read the guide</a><a href="{REPO}/releases/tag/v1.8.1">Get version 1.8.1</a><a href="{REPO}/blob/main/docs/CONFIGURATION.md">Controls &amp; settings</a></nav></header>
<section aria-label="Recorded screensavers"><div class="toolbar"><div><label for="scene-search">Find a screensaver</label><input id="scene-search" type="search" placeholder="Search Clock, Eclipse, Rain…" autocomplete="off"></div><span id="count" aria-live="polite">18 scenes · click play to watch</span></div><p id="empty" hidden>No matching scenes. Try another name.</p><div class="gallery">{''.join(cards)}</div></section>
<footer><p>Recordings from 30–31 October 2026. Playback is silent and starts only when you choose it. The refreshed cockpit preview shows its staggered startup; Aurora Flow shows the new spectrum layout. Workstation identity is replaced with demo labels in telemetry recordings.</p><p><a href="{REPO}/blob/main/docs/SHOWCASE.md">Recording details</a> · <a href="{REPO}/blob/main/docs/RELEASE-PRIVACY.md">Release privacy</a> · Independent community project; not an official Omarchy product.</p></footer></main><script>{SCRIPT}</script></body></html>'''


def main():
    for key, *_ in MODES:
        for leaf in [key + '.webm', key + '.mp4', 'previews/' + key + '.jpg', 'previews/' + key + '.gif']:
            if not (ROOT / 'assets/showcase' / leaf).is_file():
                raise SystemExit('Missing showcase media: ' + leaf)
    (ROOT / 'index.html').write_text(gallery(''))
    (ROOT / 'docs/index.html').write_text(gallery('../'))
    lines = ['## Showcase Gallery', '',
             '**18 recorded previews.** System Cockpit and Audio Visualizer are refreshed for version 1.8.1. Click an animated preview or **Watch video** to open its player. The three new scenes appear first.', '',
             '| Screensaver | Animated preview | Description |', '|---|---|---|']
    for key, name, icon, detail, group in MODES:
        title = name + (' · **New**' if key in NEW else '')
        lines.append(f'| {title} | [![{name} preview](assets/showcase/previews/{key}.gif)]({PAGES}#{key})<br>[Watch video]({PAGES}#{key}) | {detail} |')
    lines.extend(['', 'The System Cockpit clip shows the new seven-gauge dashboard, per-core activity, processor/network histories and resource pressure. All videos are silent; workstation identity is replaced with demo labels in the telemetry clips. See [recording details](docs/SHOWCASE.md).', ''])
    readme = ROOT / 'README.md'
    text = readme.read_text()
    a = text.index('## Showcase Gallery'); b = text.index('\n---\n\n## Requirements', a)
    readme.write_text(text[:a] + '\n'.join(lines) + text[b:])
    print('Updated root/docs galleries and all 18 README preview links.')


if __name__ == '__main__':
    main()
