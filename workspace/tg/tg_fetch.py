#!/usr/bin/env python3
"""Read-only Telegram group fetcher (Asia/Shanghai windows).

  tg_fetch.py --window last3h            # most recent *completed* 3-hour window (e.g. 18-21 at 21:05)
  tg_fetch.py --window current           # window containing now, up to now (marked partial)
  tg_fetch.py --date 2026-10-08 --window 15-18
  tg_fetch.py --date 2026-10-08 --all    # every 3-hour window of that day up to now (one pass per group)
  tg_fetch.py --start "2026-10-08 18:00" --end "2026-10-08 19:30" --out /tmp/x.json
  tg_fetch.py --window lasthour          # last *completed* hour -> data/<date>/hourly/<HH>.json
                                         #   (at 00:xx this is 23-24 of the previous day)
  tg_fetch.py --date 2026-10-08 --hours 18-20   # hourly files for hours 18,19 (end exclusive)
  tg_fetch.py --split-local data/2026-10-08/15-18.json   # no network: split a fetched 3h file into hourly files

Writes /workspace/tg/data/YYYY-MM-DD/HH-HH.json (HH-HH = window, e.g. 18-21).
Never sends, never marks read (no ReadHistory / ReadAcknowledge calls), never joins/leaves.
"""
import argparse, asyncio, json, os, sys, time, logging
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tgnet import make_client
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetForumTopicsRequest
from telethon.tl.types import (MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage,
                               User, Channel, Chat, MessageService)

TZ = timezone(timedelta(hours=8))
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')
SESSION = os.path.expanduser('~/.tg/halo')
LOGF = os.path.expanduser('~/.tg/fetch.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler(LOGF), logging.StreamHandler(sys.stderr)])
for n in ('telethon',): logging.getLogger(n).setLevel(logging.WARNING)
logging.getLogger('telethon.client.users').setLevel(logging.INFO)   # 'Sleeping for Ns on flood wait' lines
log = logging.getLogger('tg_fetch')

def windows_of_day(day):
    d0 = datetime.combine(day, datetime.min.time(), TZ)
    return [(d0 + timedelta(hours=h), d0 + timedelta(hours=h + 3)) for h in range(0, 24, 3)]

def wlabel(s, e):
    eh = 24 if (e.date() > s.date() and e.hour == 0) else e.hour
    return f'{s.hour:02d}-{eh:02d}'

def display_name(ent):
    if ent is None: return None
    if isinstance(ent, User):
        n = ' '.join(x for x in (ent.first_name, ent.last_name) if x) or (ent.username or str(ent.id))
        return n
    return getattr(ent, 'title', None) or str(getattr(ent, 'id', ''))

def media_desc(m):
    md = m.media
    if md is None: return None
    if isinstance(md, MessageMediaPhoto): return 'photo'
    if isinstance(md, MessageMediaWebPage):
        wp = md.webpage
        return 'webpage: ' + ' | '.join(x for x in (getattr(wp, 'site_name', None), getattr(wp, 'title', None), getattr(wp, 'url', None)) if x)
    if isinstance(md, MessageMediaDocument):
        doc = md.document
        name = None; kind = 'file'
        for a in getattr(doc, 'attributes', []) or []:
            t = type(a).__name__
            if t == 'DocumentAttributeFilename': name = a.file_name
            elif t == 'DocumentAttributeSticker': kind = 'sticker'
            elif t == 'DocumentAttributeVideo': kind = 'video'
            elif t == 'DocumentAttributeAudio': kind = 'voice' if getattr(a, 'voice', False) else 'audio'
            elif t == 'DocumentAttributeAnimated': kind = 'gif'
        return kind + (f': {name}' if name else '')
    return type(md).__name__.replace('MessageMedia', '').lower()

def msg_link(ent, mid):
    u = getattr(ent, 'username', None)
    if u: return f'https://t.me/{u}/{mid}'
    return f'https://t.me/c/{ent.id}/{mid}'

def urls_of(m):
    out = []
    for e, txt in (m.get_entities_text() if m.entities else []):
        t = type(e).__name__
        if t == 'MessageEntityTextUrl': out.append(e.url)
        elif t == 'MessageEntityUrl': out.append(txt)
    return out

def topic_of(m):
    r = m.reply_to
    if r is None or not getattr(r, 'forum_topic', False): return 1          # General topic
    return r.reply_to_top_id or r.reply_to_msg_id

async def forum_topics(client, ent):
    """topic id -> title (read-only GetForumTopics)."""
    out = {1: 'General'}
    try:
        res = await client(GetForumTopicsRequest(peer=ent, offset_date=None, offset_id=0, offset_topic=0, limit=100))
        for t in res.topics:
            if getattr(t, 'title', None): out[t.id] = t.title
    except Exception as e:
        log.warning('forum topics failed for %s: %s', getattr(ent, 'title', ent), e)
    return out

FLOOD = []   # (group title, seconds) seen this run

async def fetch_group(client, g, start, end, ent=None):
    ent = ent or await client.get_entity(g['id'])
    is_forum = bool(getattr(ent, 'forum', False))
    topics = await forum_topics(client, ent) if is_forum else {}
    msgs = []
    tries = 0
    while True:
        try:
            msgs = []
            async for m in client.iter_messages(ent, offset_date=end, wait_time=1):
                if m.date < start: break
                if isinstance(m, MessageService): continue
                sender = m.sender
                fwd = None
                if m.fwd_from:
                    fwd = m.fwd_from.from_name or (display_name(m.forward.sender or m.forward.chat) if m.forward else None) or 'forwarded'
                msgs.append({
                    'id': m.id,
                    'time': m.date.astimezone(TZ).strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': display_name(sender) or m.post_author or (str(m.sender_id) if m.sender_id else None),
                    'sender_id': m.sender_id,
                    'sender_username': getattr(sender, 'username', None),
                    'sender_bot': bool(getattr(sender, 'bot', False)),
                    'text': m.message or '',
                    'media': media_desc(m),
                    'urls': urls_of(m),
                    'reply_to': m.reply_to_msg_id,
                    'fwd_from': fwd,
                    'link': msg_link(ent, m.id),
                })
                if is_forum:
                    tid = topic_of(m); msgs[-1]['topic'] = topics.get(tid, f'topic {tid}')
            break
        except FloodWaitError as e:
            tries += 1
            log.warning('FloodWait %ss on %s (try %d)', e.seconds, g['title'], tries); FLOOD.append((g['title'], e.seconds))
            if tries > 3: raise
            await asyncio.sleep(e.seconds + 2)
    msgs.reverse()
    # attach short quote of replied-to message when it is inside the window
    by_id = {m['id']: m for m in msgs}
    for m in msgs:
        r = by_id.get(m['reply_to'])
        if r: m['reply_to_text'] = (r['sender'] or '') + ': ' + (r['text'] or r['media'] or '')[:120]
    return ent, msgs

def split(msgs, s, e):
    fs, fe = s.strftime('%Y-%m-%d %H:%M:%S'), e.strftime('%Y-%m-%d %H:%M:%S')
    return [m for m in msgs if fs <= m['time'] < fe]

def hourly_path(s):
    return os.path.join(DATA, s.strftime('%Y-%m-%d'), 'hourly', f'{s.hour:02d}.json')

def split_local(path):
    """Write data/<date>/hourly/<HH>.json from an already fetched window file (no Telegram access)."""
    d = json.load(open(path)); w = d['window']
    s = datetime.strptime(w['start'], '%Y-%m-%d %H:%M').replace(tzinfo=TZ)
    e = datetime.strptime(w['end'], '%Y-%m-%d %H:%M').replace(tzinfo=TZ)
    out = []
    h = s
    while h < e:
        he = h + timedelta(hours=1)
        if he > e and w.get('partial'): break          # don't emit an incomplete hour
        doc = {'window': {'date': h.strftime('%Y-%m-%d'), 'label': wlabel(h, he), 'start': h.strftime('%Y-%m-%d %H:%M'),
                          'end': he.strftime('%Y-%m-%d %H:%M'), 'partial': False},
               'generated_at': d.get('generated_at'), 'split_from': os.path.relpath(path, BASE), 'groups': []}
        for g in d['groups']:
            sub = split(g['messages'], h, he)
            doc['groups'].append(dict(g, count=len(sub), messages=sub))
        p = hourly_path(h); os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(doc, open(p, 'w'), ensure_ascii=False, indent=1)
        print(p, ' '.join(f"{g['key']}={g['count']}" for g in doc['groups']))
        out.append(p); h = he
    return out

async def run(ranges, out_override=None, hourly=False):
    groups = json.load(open(os.path.join(BASE, 'groups.json')))
    now = datetime.now(TZ)
    gstart = min(s for s, _ in ranges); gend = min(max(e for _, e in ranges), now)
    client = make_client(SESSION)
    client.flood_sleep_threshold = 120   # Telethon sleeps automatically for FloodWait <= 120 s
    await client.connect()
    if not await client.is_user_authorized():
        log.error('session not authorized'); sys.exit(2)
    results = {}
    try:
        # resolve entities from the session cache; list dialogs (slow over HTTP) only if something is missing
        ents, missing = {}, []
        for g in groups:
            try: ents[g['key']] = await client.get_entity(g['id'])
            except Exception: missing.append(g)
        if missing:
            log.info('entity cache miss for %s; listing dialogs', [g['key'] for g in missing])
            try:
                await client.get_dialogs(limit=None)   # read-only
            except Exception as e:
                log.warning('get_dialogs failed: %s', e)
            for g in missing:
                try: ents[g['key']] = await client.get_entity(g['id'])
                except Exception as e: log.warning('cannot resolve %s: %s', g['title'], e)
        t_all = time.time()
        for g in groups:
            t0 = time.time()
            try:
                ent, msgs = await fetch_group(client, g, gstart, gend, ents.get(g['key']))
                results[g['key']] = (g, ent, msgs, None)
                log.info('%s: %d msgs %s..%s in %.1fs', g['title'], len(msgs), gstart, gend, time.time() - t0)
            except Exception as e:
                log.exception('fetch failed for %s', g['title'])
                results[g['key']] = (g, None, [], f'{type(e).__name__}: {e}')
        log.info('fetched %d groups in %.1fs; FloodWaits: %s', len(groups), time.time() - t_all, FLOOD or 'none')
    finally:
        await client.disconnect()
    written = []
    for s, e in ranges:
        partial = e > now
        doc = {'window': {'date': s.strftime('%Y-%m-%d'), 'label': wlabel(s, e),
                          'start': s.strftime('%Y-%m-%d %H:%M'), 'end': min(e, now).strftime('%Y-%m-%d %H:%M'),
                          'partial': partial},
               'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'), 'groups': []}
        for g, ent, msgs, err in results.values():
            sub = split(msgs, s, e)
            doc['groups'].append({'key': g['key'], 'id': g['id'], 'title': getattr(ent, 'title', None) or g['title'],
                                  'type': g.get('type'), 'tag': g.get('tag'), 'order': g.get('order'),
                                  'username': getattr(ent, 'username', None), 'count': len(sub),
                                  'error': err, 'messages': sub})
        path = out_override or (hourly_path(s) if hourly else os.path.join(DATA, s.strftime('%Y-%m-%d'), wlabel(s, e) + '.json'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(doc, open(path, 'w'), ensure_ascii=False, indent=1)
        written.append(path)
        print(path, ' '.join(f"{g['key']}={g['count']}" for g in doc['groups']), 'PARTIAL' if partial else '')
    return written

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', help='last3h | lasthour | current | HH-HH')
    ap.add_argument('--hours', help='H1-H2: hourly files for hours H1..H2-1 of --date')
    ap.add_argument('--split-local', help='split an existing fetched window file into hourly files (no network)')
    ap.add_argument('--date', help='YYYY-MM-DD (default today, Asia/Shanghai)')
    ap.add_argument('--all', action='store_true', help='all 3h windows of --date up to now')
    ap.add_argument('--start'); ap.add_argument('--end'); ap.add_argument('--out')
    a = ap.parse_args()
    now = datetime.now(TZ)
    day = datetime.strptime(a.date, '%Y-%m-%d').date() if a.date else now.date()
    hourly = False
    if a.split_local:
        split_local(a.split_local); return
    if a.window == 'lasthour':
        cur = now.replace(minute=0, second=0, microsecond=0)
        ranges = [(cur - timedelta(hours=1), cur)]; hourly = True
    elif a.hours:
        h1, h2 = (int(x) for x in a.hours.split('-'))
        d0 = datetime.combine(day, datetime.min.time(), TZ)
        ranges = [(d0 + timedelta(hours=h), d0 + timedelta(hours=h + 1)) for h in range(h1, h2)
                  if d0 + timedelta(hours=h) < now]; hourly = True
    elif a.start:
        s = datetime.strptime(a.start, '%Y-%m-%d %H:%M').replace(tzinfo=TZ)
        e = datetime.strptime(a.end, '%Y-%m-%d %H:%M').replace(tzinfo=TZ) if a.end else now
        ranges = [(s, e)]
    elif a.all:
        ranges = [w for w in windows_of_day(day) if w[0] < now]
    elif a.window == 'last3h':
        cur = now.replace(minute=0, second=0, microsecond=0, hour=now.hour - now.hour % 3)
        ranges = [(cur - timedelta(hours=3), cur)]
    elif a.window == 'current':
        cur = now.replace(minute=0, second=0, microsecond=0, hour=now.hour - now.hour % 3)
        ranges = [(cur, cur + timedelta(hours=3))]
    elif a.window:
        h1, h2 = (int(x) for x in a.window.split('-'))
        d0 = datetime.combine(day, datetime.min.time(), TZ)
        ranges = [(d0 + timedelta(hours=h1), d0 + timedelta(hours=h2))]
    else:
        ap.error('need --window, --all or --start')
    asyncio.run(run(ranges, a.out, hourly))

if __name__ == '__main__':
    main()
