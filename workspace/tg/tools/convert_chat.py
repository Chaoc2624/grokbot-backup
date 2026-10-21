#!/usr/bin/env python3
"""One-off converter: old prose fragments ('X 说「…」') -> chat format, rebuilt from the raw messages.

  tools/convert_chat.py 2026-10-08 digests/2026-10-08/3h/12-15.json 12-15 [--out FILE]
  tools/convert_chat.py 2026-10-08 digests/2026-10-08/daily.json day

For every bullet: quotes 「…」 and URLs are located in the window's raw messages; quote-less clauses
'名 说 …' are fuzzy-matched to that sender's messages. The matched messages are emitted verbatim (long
ones trimmed with …) as '> 发言人：原话' lines in time order. Unmatched clauses are reported on stderr.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatfmt import canon
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
date, src, win = sys.argv[1], sys.argv[2], sys.argv[3]
out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else src
hours = range(24) if win == 'day' else (range(*map(int, win.split('-'))) if '-' in win else [int(win)])
groups = json.load(open(os.path.join(BASE, 'groups.json')))
tag2key = {g['tag']: g['key'] for g in groups}; key2tag = {g['key']: g['tag'] for g in groups}
n = lambda s: re.sub(r'\s+', '', s or '').lower()
MS = {}
for h in hours:
    f = os.path.join(BASE, 'data', date, 'hourly', f'{h:02d}.json')
    if not os.path.exists(f): continue
    for g in json.load(open(f))['groups']:
        for m in g['messages']:
            m = dict(m); m['g'] = g['key']; m['nt'] = n(m.get('text')); MS.setdefault(g['key'], []).append(m)
# also earlier 3h fetches (data/<D>/AA-BB.json): messages later deleted from Telegram are still quotable
import glob
_seen = {(k, m['id']) for k, v in MS.items() for m in v}
for f in sorted(glob.glob(os.path.join(BASE, 'data', date, '[0-9][0-9]-[0-9][0-9].json'))):
    for g in json.load(open(f)).get('groups', []):
        for m in g['messages']:
            if int(m['time'][11:13]) in hours and (g['key'], m['id']) not in _seen:
                m = dict(m); m['g'] = g['key']; m['nt'] = n(m.get('text')); MS.setdefault(g['key'], []).append(m); _seen.add((g['key'], m['id']))
LOG = []

def bigr(s):
    s = re.sub(r'[\s，。、,.!?！？：:；;「」()（）]+', '', s.lower()); return {s[i:i + 2] for i in range(len(s) - 1)}

def render(m, q=None):
    t = re.sub(r'\s*\n\s*', ' ', (m.get('text') or '').strip())
    if not t:
        t = '[图片]' if (m.get('media') or '').startswith('photo') else f"[{(m.get('media') or '媒体')[:8]}]"
    lim = 60 if m.get('sender_bot') or re.search(r'bot\b|Bot\b|Group ?Help', m.get('sender') or '') else 130
    if len(t) <= lim: return t
    if q:
        i = t.lower().find(q.lower())
        if i >= 0:
            a = max(0, i - 25); b = min(len(t), i + len(q) + 45)
            return ('…' if a else '') + t[a:b].strip() + ('…' if b < len(t) else '')
    urls = re.findall(r'https?://\S+', t)
    cut = lim - 10
    for um in re.finditer(r'https?://\S+', t):
        if um.start() < cut < um.end(): cut = um.start()
    s = t[:cut].rstrip() + '…'
    for u in urls:
        if u not in s: s += ' ' + u
    return s

def senders(pool):
    return sorted({m.get('sender') or '' for m in pool if m.get('sender')}, key=len, reverse=True)

def convert_bullet(body, pool):
    """body = bullet text without topic. returns list of (msg, quote) matched."""
    found = {}
    names = senders(pool)
    # quotes
    for qm in re.finditer(r'「([^」]+)」', body):
        q = qm.group(1); nq = n(q)
        cands = [m for m in pool if nq and nq in m['nt']]
        if not cands:
            # quote may join two messages; try halves split on spaces
            parts = [p for p in re.split(r'…|\.\.\.|\s+|，', q) if len(n(p)) >= 2]
            for p in parts:
                c2 = [m for m in pool if n(p) in m['nt']]
                if c2: found.setdefault(c2[0]['id'], (c2[0], p))
            if not parts or not any(n(p) in m['nt'] for p in parts for m in pool): LOG.append(f'quote not found: {q[:50]}')
            continue
        before = body[:qm.start()]
        best = None
        for m in cands:   # prefer the sender named closest before the quote
            nm = m.get('sender') or ''
            pos = max(before.rfind(nm), before.rfind(nm.strip(' .')))
            if best is None or pos > best[0]: best = (pos, m)
        m = best[1]; found.setdefault(m['id'], (m, q))
    # urls
    for u in re.findall(r'https?://[^\s）)，。]+', body):
        for m in pool:
            if u in (m.get('text') or '') or u in ' '.join(m.get('urls') or []):
                found.setdefault(m['id'], (m, None)); break
    # quote-less clauses
    for cl in re.split(r'[；;。]', re.sub(r'「[^」]*」', '「」', body)):
        if '「」' in cl or len(cl.strip()) < 6: continue
        c = cl.strip().lstrip('，, ')
        c = re.sub(r'^(群主|管理员)', '', c)
        nm = next((x for x in names if c.startswith(x) or c.startswith(x.strip(' .'))), None)
        if not nm: LOG.append(f'no speaker: {c[:50]}'); continue
        rest = c[len(nm):].strip()
        rest = re.sub(r'^(也|又|还|就)?(说|问|提到|表示|回|贴出|发了?|推广|讲|转发)', '', rest)
        rb = bigr(rest)
        if len(rb) < 3: continue
        bs = None
        for m in pool:
            if (m.get('sender') or '') != nm: continue
            mb = bigr(m.get('text') or '')
            if not mb: continue
            sc = len(rb & mb) / len(rb)
            if bs is None or sc > bs[0]: bs = (sc, m)
        if bs and bs[0] >= 0.3: found.setdefault(bs[1]['id'], (bs[1], None))
        else: LOG.append(f'unmatched ({nm}): {rest[:50]}')
    return sorted(found.values(), key=lambda x: (x[0]['time'], x[0]['id']))

def lines_for(matched, tag=False):
    outl, last = [], None
    for m, q in matched:
        nm = (m.get('sender') or '?').strip()
        t = render(m, q)
        sfx = f" 【{key2tag.get(m['g'], m['g'])}】" if tag else ''
        if outl and last == (nm, m['g']):
            outl[-1] = outl[-1][:len(outl[-1]) - len(sfx)] + ' · ' + t + sfx if sfx else outl[-1] + ' · ' + t
        else:
            outl.append(f'> {nm}：{t}{sfx}')
        last = (nm, m['g'])
    return [canon(x) for x in outl]

def convert(content, gkey):
    pool = [m for k, v in MS.items() for m in v] if gkey == 'all' else MS.get(gkey, [])
    res = []
    for raw in content.split('\n'):
        t = raw.strip()
        if not t: res.append(''); continue
        if re.match(r'^\*\*\d{1,2}:\d{2}', t) or t.startswith('#'): res.append(t); continue
        body = re.sub(r'^[-*•]\s*', '', t)
        tm = re.match(r'^\*\*([^*]+)\*\*\s*(?:[（(](\d+)\s*条\s*/\s*(\d+)\s*人[)）])?\s*[：:]?\s*', body)
        topic, cnt = None, ''
        if tm:
            topic = tm.group(1).strip(); body = body[tm.end():]
            if tm.group(2): cnt = f' ({tm.group(2)} 条 / {tm.group(3)} 人)'
        if topic == '话题活跃成员':
            res.append('~ 话题活跃成员（近 7 天话题消息）：' + re.sub(r'（近 7 天 (\d+) 条，?主要聊 ?([^）]*)）', r' \1（\2）', re.sub(r'（(\d+) 条，([^）]*)）', r' \1（\2）', body)).strip('。'))
            continue
        tags = re.findall(r'【([^】]+)】', body)
        sub = pool
        if gkey == 'all' and tags:
            ks = [tag2key[x] for x in tags if x in tag2key]
            if ks: sub = [m for m in pool if m['g'] in ks]
        matched = convert_bullet(re.sub(r'【[^】]+】', '', body), sub)
        if not matched:
            LOG.append(f'BULLET DROPPED: {t[:70]}'); continue
        if topic in (None, '其他'): topic = '其他话题' if topic else '讨论'
        res.append(f'### {topic}{cnt}')
        res += lines_for(matched, tag=(gkey == 'all'))
    s = '\n'.join(res)
    return re.sub(r'\n{3,}', '\n\n', s).strip()

d = json.load(open(src))
for it in d['items']:
    c = it.get('content') or ''
    if not c.strip() or c.strip() == '无重要内容': continue
    LOG.clear()
    it['content'] = convert(c, it['group'])
    for l in LOG: print(f"[{it['group']}] {l}", file=sys.stderr)
json.dump(d, open(out, 'w'), ensure_ascii=False, indent=1)
print('wrote', out)
