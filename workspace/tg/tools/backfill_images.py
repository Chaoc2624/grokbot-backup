#!/usr/bin/env python3
"""Add 'image' fields to an already fetched data file (read-only: get_messages by id + file download).
  tools/backfill_images.py data/2026-10-21/hourly/14.json [--out /tmp/x.json]   (default: rewrite in place)
Media go to $TG_MEDIA_DIR or /workspace/tg/media.
"""
import asyncio, json, os, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, BASE)
from tgnet import make_client
import tg_media

async def main(src, out):
    d = json.load(open(src)); n = 0
    c = make_client(os.path.expanduser('~/.tg/halo')); await c.connect()
    if not await c.is_user_authorized(): sys.exit('session not authorized')
    try:
        for g in d['groups']:
            ids = [m['id'] for m in g['messages'] if (m.get('media') or '').split(':')[0] in ('photo', 'file') and 'image' not in m]
            if not ids: continue
            ent = await c.get_entity(g['id']); by = {m['id']: m for m in g['messages']}
            for i in range(0, len(ids), 100):
                for tm in await c.get_messages(ent, ids=ids[i:i + 100]):
                    if tm is None: continue
                    img = await tg_media.capture(c, tm, g['key'], by[tm.id]['time'][:10])
                    if img: by[tm.id]['image'] = img; n += 1
                    print(g['key'], tm.id, 'ok' if img else '-', file=sys.stderr, flush=True)
            print(g['key'], len(ids), file=sys.stderr)
    finally:
        await c.disconnect()
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=1); print(out, n, 'images')

a = sys.argv[1:]; src = a[0]; out = a[a.index('--out') + 1] if '--out' in a else src
asyncio.run(main(src, out))
