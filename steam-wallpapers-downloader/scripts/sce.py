#!/usr/bin/env python3
"""Search steamcardexchange.net and download a game's card/background/emoticon images.

  sce.py config [--root DIR]                  show / set the default download root
  sce.py search "<name>" [--limit N]          best-matching games (appid, title, link)
  sce.py info <appid|url> [...]               title + what would be downloaded
  sce.py download <appid|url> [...] [--root DIR] [--title NAME] [--dry-run]

Standard library only; runs on Linux, macOS and Windows.
"""
import argparse, difflib, html, json, os, re, sys, urllib.parse, urllib.request

BASE = 'https://www.steamcardexchange.net'
UA = {'User-Agent': 'Mozilla/5.0'}
APP = 'steam-wallpapers-downloader'
WIN_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


# ---------- config (default root folder, per user, per machine) ----------
def config_path():
    if os.name == 'nt':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.join(base, APP, 'config.json')


def load_root():
    try:
        with open(config_path(), encoding='utf-8') as f:
            return json.load(f).get('root')
    except (OSError, ValueError):
        return None


def suggested_root():
    return os.path.join(os.path.expanduser('~'), 'Pictures', 'wallpapers')


# ---------- site access ----------
def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def appid_of(s):
    m = re.search(r'appid-(\d+)', s) or re.fullmatch(r'\s*(\d+)\s*', s)
    if not m:
        sys.exit(f'Cannot find an appid in: {s}')
    return m.group(1)


def page(appid):
    return get(f'{BASE}/index.php?gamepage-appid-{appid}').decode('utf-8', 'replace')


def title_of(h):
    m = re.search(r'<title>\s*Showcase :: (.*?)\s*</title>', h, re.S)
    return html.unescape(m.group(1)).strip() if m else None


def san(n):
    """Make a name safe as a file/folder name on Linux, macOS and Windows."""
    n = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '-', html.unescape(n)).strip().rstrip('. ')
    if n.upper() in WIN_RESERVED:
        n += '_'
    return n or 'unnamed'


# ---------- page parsing ----------
# Sections are identified by their anchor id (series-1-cards, series-2-backgrounds, ...) so that
# only the trading-card series is used; game-specific extras (e.g. Counter-Strike chat/flair
# emoticons) and points-shop groups (animated stickers, avatar frames, ...) are left alone.
KINDS = {  # anchor suffix -> (output folder, filename suffix, label)
    'cards': ('Trading Cards', '', 'Trading Cards'),
    'backgrounds': ('Backgrounds', '', 'Backgrounds'),
    'badges': ('Emoticons', '', 'Badges'),
    'foilbadges': ('Emoticons', ' (Foil)', 'Foil Badges'),
    'emoticons': ('Emoticons', '', 'Emoticons'),
}
ITEM = '<div class="flex flex-col items-center p-5'


def build_jobs(h):
    """Return (jobs, groups_found, notes). job = (folder, url, name, suffix)."""
    marks = [(m.start(), m.group(1)) for m in
             re.finditer(r'<span class="tracking-wider font-league-gothic"><a href="#([^"]*)">', h)]
    marks.append((len(h), ''))
    jobs, found, notes = [], [], []
    for (s, anchor), (e, _) in zip(marks, marks[1:]):
        m = re.fullmatch(r'series-\d+-([a-z]+)', anchor)
        if not m or m.group(1) not in KINDS:
            continue
        kind = m.group(1)
        folder, suf, label = KINDS[kind]
        found.append(label)
        for block in h[s:e].split(ITEM)[1:]:
            nm = re.search(r'<div class="text-sm text-center break-(?:words|all)">([^<]+)</div>', block)
            if not nm:
                continue
            name = html.unescape(nm.group(1)).strip()
            if kind in ('cards', 'backgrounds'):
                # Full-size version: the "Wallpaper" arrow link (the image popup uses the same link).
                g = re.search(r'<a href="([^"]+)"[^>]*class="gallery-src"', block)
                if g:
                    url = g.group(1)
                else:  # no large version on the site: fall back to the item image itself
                    i = re.search(r'<img[^>]*src="([^"]+)"', block)
                    if not i:
                        notes.append(f'{label}: no image found for "{name}"')
                        continue
                    url = i.group(1).split('?')[0]
                    notes.append(f'{label}: "{name}" has no wallpaper version on the site; saved the small image')
            else:
                # Last image before the name: for emoticons the first one is the tiny chat preview.
                imgs = re.findall(r'<img[^>]*src="([^"]+)"', block[:nm.start()])
                if not imgs:
                    notes.append(f'{label}: no image found for "{name}"')
                    continue
                url = imgs[-1]
                if kind == 'emoticons':
                    name = name.strip(':')
                    name = name[:1].upper() + name[1:]
            jobs.append((folder, html.unescape(url), name, suf))
    return jobs, found, notes


def sniff_ext(data):
    if data[:3] == b'\xff\xd8\xff': return '.jpg'
    if data[:8] == b'\x89PNG\r\n\x1a\n': return '.png'
    if data[:6] in (b'GIF87a', b'GIF89a'): return '.gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP': return '.webp'
    return '.jpg'


# ---------- commands ----------
def cmd_config(a):
    p = config_path()
    if a.root:
        root = os.path.abspath(os.path.expanduser(a.root))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump({'root': root}, f, indent=2)
    print(f'config_file={p}\nroot={load_root() or "NOT SET"}\nsuggested_root={suggested_root()}')


def rank(query, name):
    q, n = query.lower().strip(), name.lower()
    score = difflib.SequenceMatcher(None, q, n).ratio()
    if n == q: score += 3
    elif n.startswith(q): score += 2
    elif q in n: score += 1
    elif all(t in n for t in q.split()): score += 0.5
    return score


def cmd_search(a):
    data = get(f'{BASE}/api/request.php?SearchGame&' + urllib.parse.urlencode({'q': a.query})).decode('utf-8', 'replace')
    rows = [(i, html.unescape(n).strip()) for i, n in
            re.findall(r'gamepage-appid-(\d+)".*?<span[^>]*>([^<]+)</span>', data, re.S)]
    rows.sort(key=lambda r: -rank(a.query, r[1]))
    if not rows:
        print('No results.')
    for appid, name in rows[:a.limit]:
        print(f'{appid}\t{name}\t{BASE}/index.php?gamepage-appid-{appid}')
    if len(rows) > a.limit:
        print(f'({len(rows) - a.limit} more results not shown; use --limit to see them)')


def cmd_info(a):
    for g in a.games:
        appid = appid_of(g)
        h = page(appid)
        jobs, found, notes = build_jobs(h)
        counts = {}
        for folder, *_ in jobs:
            counts[folder] = counts.get(folder, 0) + 1
        print(f'appid={appid}\ttitle={title_of(h)}\tfiles={counts}\tgroups={found}')
        for n in notes: print('  NOTE:', n)


def download_one(game, root_base, title_override, dry):
    appid = appid_of(game)
    h = page(appid)
    title = title_override or title_of(h)
    if not title:
        return {'game': f'appid {appid}', 'error': 'could not read the game title (pass --title)'}
    jobs, found, notes = build_jobs(h)
    root = os.path.join(root_base, san(title))
    missing = [v[2] for v in KINDS.values() if v[2] not in found]
    r = {'game': f'{title} (appid {appid})', 'folder': root, 'ok': 0, 'skipped': [], 'failed': [],
         'missing': missing, 'notes': notes, 'planned': 0}
    seen = {}
    for folder, url, name, suf in jobs:
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
        if not re.fullmatch(r'\.(jpe?g|png|gif|webp)', ext):
            ext = ''  # extension unknown until downloaded
        stem = os.path.join(root, folder, san(name) + suf)
        if stem in seen:  # same name twice in one game (e.g. several series): keep both
            if seen[stem] == url:
                continue
            n = 2
            while f'{stem} ({n})' in seen: n += 1
            stem = f'{stem} ({n})'
        seen[stem] = url
        r['planned'] += 1
        d, base = os.path.split(stem)
        existing = [f for f in (os.listdir(d) if os.path.isdir(d) else [])
                    if os.path.splitext(f)[0] == base and (not ext or f.lower().endswith(ext))]
        if existing:
            r['skipped'].append(os.path.join(d, existing[0])); continue
        if dry:
            print(f'{stem}{ext or ".?"} <- {url}'); continue
        try:
            data = get(url)
            os.makedirs(d, exist_ok=True)
            with open(stem + (ext or sniff_ext(data)), 'wb') as f:
                f.write(data)
            r['ok'] += 1
        except Exception as ex:
            r['failed'].append((stem, str(ex)))
    return r


def cmd_download(a):
    root_base = a.root or load_root()
    if not root_base:
        print('NO_ROOT_CONFIGURED: ask the user where images should be saved '
              f'(suggest {suggested_root()}), then run: sce.py config --root "<folder>"')
        sys.exit(2)
    root_base = os.path.abspath(os.path.expanduser(root_base))
    if a.title and len(a.games) > 1:
        sys.exit('--title only works with a single game')
    results = []
    for g in a.games:
        try:
            results.append(download_one(g, root_base, a.title, a.dry_run))
        except Exception as ex:  # one broken game must not stop the batch
            results.append({'game': g, 'error': str(ex)})
    print('\n===== REPORT' + (' (dry run, nothing saved)' if a.dry_run else '') + ' =====')
    for r in results:
        print(f"\nGAME: {r['game']}")
        if 'error' in r:
            print('  ERROR:', r['error']); continue
        print(f"  folder: {r['folder']}")
        print(f"  planned={r['planned']} downloaded={r['ok']} skipped_existing={len(r['skipped'])} failed={len(r['failed'])}")
        if r['missing']: print('  groups this game does not have on the site:', ', '.join(r['missing']))
        for n in r['notes']: print('  NOTE:', n)
        for p in r['skipped']: print('  SKIPPED (already exists):', p)
        for p, e in r['failed']: print('  FAILED:', p, '->', e)
    if any(r.get('failed') or 'error' in r for r in results):
        sys.exit(1)


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows consoles may not default to UTF-8
        try: stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception: pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(required=True)
    s = sp.add_parser('config'); s.add_argument('--root'); s.set_defaults(f=cmd_config)
    s = sp.add_parser('search'); s.add_argument('query'); s.add_argument('--limit', type=int, default=5); s.set_defaults(f=cmd_search)
    s = sp.add_parser('info'); s.add_argument('games', nargs='+'); s.set_defaults(f=cmd_info)
    s = sp.add_parser('download'); s.add_argument('games', nargs='+'); s.add_argument('--root')
    s.add_argument('--title'); s.add_argument('--dry-run', action='store_true'); s.set_defaults(f=cmd_download)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
