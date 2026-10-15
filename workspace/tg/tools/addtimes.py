#!/usr/bin/env python3
"""Add each speech line's original message time to digest files (only where the match is unambiguous).

  tools/addtimes.py 2026-10-08 digests/2026-10-08/hourly/19.json [more.json ...] [--dry-run]

A speech line '> 发言人：原话 · 原话2' gets a trailing time token:
  > 发言人：原话 · 原话2 {{2026-10-08 19:05:12}}            first message's time
  > 发言人：原话 · 原话2 {{2026-10-08 19:05:12~19:06:40}}   + last message's time (if also unambiguous)
Matching: the first ' · ' piece (==marks== / 【群标签】 removed, '…' parts all required) must be found in exactly
ONE raw message (data/<D>/hourly/*.json + data/<D>/HH-HH.json, deduped by message id) of that group, inside
the line's hours ('**HH:00–HH:00**' divider, else the file's window; daily = whole day) and from a sender whose
name matches. Otherwise the line is left without a time. Lines that already have {{…}} are kept as they are.
"""
import json, os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatfmt import SPEECH, MARK
from order import order_content   # newest-first topics / oldest-first lines / 涉及商家 (SUMMARY_RULES 二·排序)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK = re.compile(r'\s*\{\{[^{}\n]{4,40}\}\}\s*$')
TAGS = re.compile(r'(\s*【([^】]{1,24})】)+\s*$')
n = lambda s: re.sub(r'\s+', '', s or '').lower()

def load_msgs(date):
    seen, out = set(), []
    files = sorted(glob.glob(os.path.join(BASE, 'data', date, 'hourly', '[0-9][0-9].json'))) + \
            sorted(glob.glob(os.path.join(BASE, 'data', date, '[0-9][0-9]-[0-9][0-9].json')))
    for f in files:
        for g in json.load(open(f)).get('groups', []):
            for m in g.get('messages', []):
                k = (g['key'], m['id'])
                if k in seen or not m.get('time'): continue
                seen.add(k)
                out.append({'g': g['key'], 'id': m['id'], 'time': m['time'], 'h': int(m['time'][11:13]),
                            's': n(m.get('sender')), 't': n((m.get('text') or '') + ' ' + (m.get('media') or ''))})
    return out

def find(msgs, grp, hours, name, piece):
    subs = [n(x) for x in re.split(r'…|\.\.\.', piece)]
    subs = [x for x in subs if len(x) >= 2]
    if not subs or re.fullmatch(r'\[[^\]]{1,8}\]', piece.strip()): return None
    nm = n(name)
    c = {m['id']: m for m in msgs if (grp is None or m['g'] == grp) and m['h'] in hours
         and (nm in m['s'] or (m['s'] and m['s'] in nm)) and all(x in m['t'] for x in subs)}
    return next(iter(c.values())) if len(c) == 1 else None

def stamp(date, content, grp, hours0, msgs, tag2key, st):
    out, hours, inv, hgrp = [], hours0, False, None
    for line in content.split('\n'):
        t = line.strip()
        m = re.match(r'^\*\*(\d{1,2}):\d{2}\s*[–-]\s*(\d{1,2}):(\d{2})\*\*$', t)
        if m:
            a, b, mm = int(m.group(1)), int(m.group(2)), int(m.group(3)); hours = range(a, b + (1 if mm else 0)); inv = False
        if re.match(r'^#{1,4}\s.*网上核验', t): inv = True
        elif t.startswith('###'):
            inv = False; tg = re.search(r'【([^】]{1,24})】', t); hgrp = tag2key.get(tg.group(1)) if tg else None
        sp = SPEECH.match(t) if t.startswith('>') and not inv else None
        if not sp or TOK.search(t):
            out.append(line); continue
        name, text = sp.group(1).strip(), sp.group(2)
        tm = TAGS.search(text); lt = None
        if tm:
            lt = tag2key.get(re.findall(r'【([^】]{1,24})】', tm.group(0))[-1]); text = text[:tm.start()]
        g = grp if grp != 'all' else (lt or hgrp)
        pieces = [MARK.sub(r'\1', p) for p in text.split(' · ')]
        first = find(msgs, g, hours, name, pieces[0])
        st['lines'] += 1
        if not first:
            st['miss'] += 1; out.append(line); continue
        tok = first['time']
        if len(pieces) > 1:
            last = find(msgs, g, hours, name, pieces[-1])
            if last and last['time'] > first['time']: tok += '~' + last['time'][11:]
        st['hit'] += 1
        out.append(line.rstrip() + ' {{' + tok + '}}')
    return '\n'.join(out)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; dry = '--dry-run' in sys.argv
    date, files = args[0], args[1:]
    msgs = load_msgs(date)
    tag2key = {g['tag']: g['key'] for g in json.load(open(os.path.join(BASE, 'groups.json')))}
    tot = {'lines': 0, 'hit': 0, 'miss': 0}
    for f in files:
        d = json.load(open(f)); w = d.get('window', 'daily')
        hours = range(24) if w == 'daily' else range(*(int(x) for x in w.split('-')))
        st = {'lines': 0, 'hit': 0, 'miss': 0}
        for it in d.get('items', []):
            c = it.get('content') or ''
            it['content'] = order_content(stamp(date, c, it.get('group') or 'all', hours, msgs, tag2key, st))
        for k in tot: tot[k] += st[k]
        print(f"{f}: {st['hit']} timed, {st['miss']} left without (of {st['lines']} untimed speech lines)")
        if not dry:
            tmp = f + '.tmp'; json.dump(d, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, f)
    print(f"total: {tot['hit']} timed, {tot['miss']} left without")

if __name__ == '__main__':
    main()
