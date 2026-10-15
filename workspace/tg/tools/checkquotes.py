#!/usr/bin/env python3
"""Check chat-format speech lines against the raw Telegram data.

  tools/checkquotes.py 2026-10-08 19     specs/2026-10-08-19.spec      # one hour
  tools/checkquotes.py 2026-10-08 15-18  digests/2026-10-08/3h/15-18.json
  tools/checkquotes.py 2026-10-08 day    digests/2026-10-08/daily.json  # whole day, any group

Every '> 发言人：原话' line (outside '--- 核验' / 网上核验 blocks) is split on ' · ' and '…'; each piece,
with ==markers== and trailing 【群标签】 removed, must appear verbatim (whitespace ignored) in the messages of
that group in that window, and should come from a sender whose name matches. Pieces that are only
'[图片]' / '[链接]' style placeholders are skipped. Also lints prose lines and 「」 inside speech lines.
Exit code 1 if any piece is not found.
"""
import json, os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatfmt import SPEECH, MARK, TAG, lint
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
date, win, path = sys.argv[1], sys.argv[2], sys.argv[3]
if win == 'day': hours = range(24)
elif '-' in win: a, b = (int(x) for x in win.split('-')); hours = range(a, b)
else: hours = [int(win)]
n = lambda s: re.sub(r'\s+', '', s or '').lower()
msgs = {}          # group -> [(sender_norm, text_norm)]
for h in hours:
    f = os.path.join(BASE, 'data', date, 'hourly', f'{h:02d}.json')
    if not os.path.exists(f): continue
    for g in json.load(open(f))['groups']:
        for m in g['messages']:
            msgs.setdefault(g['key'], []).append((n(m.get('sender')), n((m.get('text') or '') + ' ' + (m.get('media') or ''))))
for f in sorted(glob.glob(os.path.join(BASE, 'data', date, '[0-9][0-9]-[0-9][0-9].json'))):   # earlier 3h fetches
    for g in json.load(open(f)).get('groups', []):
        for m in g['messages']:
            if int(m['time'][11:13]) in hours:
                msgs.setdefault(g['key'], []).append((n(m.get('sender')), n((m.get('text') or '') + ' ' + (m.get('media') or ''))))
allm = [x for v in msgs.values() for x in v]

def blocks():
    if path.endswith('.json'):
        d = json.load(open(path))
        for it in d['items']:
            yield it['group'], (it.get('content') or '').split('\n')
    else:
        cur, buf = None, []
        for line in open(path):
            if line.startswith('=== '):
                if cur: yield cur, buf
                cur, buf = line[4:].split('|')[0].strip(), []
            elif cur: buf.append(line.rstrip('\n'))
        if cur: yield cur, buf

bad = warn = 0
for grp, lines in blocks():
    pool = allm if grp == 'all' else msgs.get(grp, [])
    inv = False
    for line in lines:
        t = line.strip()
        if t in ('--- 核验', '---核验', '--- verify') or re.match(r'^#{1,4}\s.*网上核验', t): inv = True; continue
        if re.match(r'^(###|##|\*\*\d)', t): inv = False
        if inv or not t or t == '无重要内容': continue
        w = lint(t)
        if w: print(f'[{grp}] lint: {w}: {t[:70]}'); warn += 1
        m = SPEECH.match(t) if t.startswith('>') else None
        if not m: continue
        name, text = n(m.group(1)), MARK.sub(r'\1', re.sub(r'(\s*【[^】]{1,24}】)+\s*$', '', re.sub(r'\s*\{\{[^{}\n]{4,40}\}\}\s*$', '', m.group(2))))
        for piece in re.split(r' · |…|\.\.\.', text):
            p = n(piece)
            if len(p) < 2 or re.fullmatch(r'\[[^\]]{1,8}\]', piece.strip()): continue
            hits = [s for s, x in pool if p in x]
            if not hits:
                print(f'[{grp}] NOT FOUND ({m.group(1).strip()}): {piece.strip()[:80]}'); bad += 1
            elif not any(name in s or s in name for s in hits):
                print(f'[{grp}] speaker? "{m.group(1).strip()}" — found under another sender: {piece.strip()[:60]}'); warn += 1
print(f'{bad} piece(s) not found, {warn} warning(s)' if bad or warn else 'all speech lines verbatim')
sys.exit(1 if bad else 0)
