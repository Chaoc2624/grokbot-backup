"""Read-only image capture for TG messages (no AI analysis).

Downloads photos and image documents (jpeg/png/webp; no stickers, gifs, videos) and stores
  <MEDIA>/<date>/<chat>/<msgid>.jpg        max 1280 px, JPEG q80
  <MEDIA>/<date>/<chat>/<msgid>_t.jpg      max 320 px,  JPEG q70
MEDIA = $TG_MEDIA_DIR or /workspace/tg/media. Paths in records are relative to MEDIA's parent ("media/...").
Already existing files are reused (dedupe by chat+msgid). Uses only file download (upload.GetFile): never sends/marks read.
"""
import asyncio, io, os, logging
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
log = logging.getLogger('tg_media')
BASE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.environ.get('TG_MEDIA_DIR') or os.path.join(BASE, 'media')
MAX_DOC = 8 * 1024 * 1024          # skip image documents bigger than this
IMG_MIME = ('image/jpeg', 'image/png', 'image/webp')
BIG, SMALL = 1280, 320
TIMEOUT = 45                         # seconds per download; a stuck download is skipped

def is_image(m):
    md = m.media
    if isinstance(md, MessageMediaPhoto) and md.photo: return True
    if isinstance(md, MessageMediaDocument) and md.document:
        d = md.document
        if d.mime_type not in IMG_MIME or d.size > MAX_DOC: return False
        names = {type(a).__name__ for a in d.attributes or []}
        return not names & {'DocumentAttributeSticker', 'DocumentAttributeVideo', 'DocumentAttributeAnimated'}
    return False

def rel(p): return os.path.relpath(p, os.path.dirname(MEDIA))

async def capture(client, m, chat_key, date):
    """Return {'path','thumb','w','h','bytes'} or None."""
    if not is_image(m): return None
    from PIL import Image
    d = os.path.join(MEDIA, date, chat_key); big = os.path.join(d, f'{m.id}.jpg'); sm = os.path.join(d, f'{m.id}_t.jpg')
    if not (os.path.exists(big) and os.path.exists(sm)):
        try:
            raw = await asyncio.wait_for(client.download_media(m, file=bytes), TIMEOUT)
            im = Image.open(io.BytesIO(raw)); im.load()
            if im.mode not in ('RGB', 'L'):
                bg = Image.new('RGB', im.size, 'white')
                bg.paste(im.convert('RGBA'), mask=im.convert('RGBA').split()[-1]); im = bg
            os.makedirs(d, exist_ok=True)
            a = im.copy(); a.thumbnail((BIG, BIG)); a.save(big + '.tmp', 'JPEG', quality=80, optimize=True); os.replace(big + '.tmp', big)
            b = im.copy(); b.thumbnail((SMALL, SMALL)); b.save(sm + '.tmp', 'JPEG', quality=70, optimize=True); os.replace(sm + '.tmp', sm)
        except Exception as e:
            log.warning('image %s/%s failed: %s', chat_key, m.id, e); return None
    from PIL import Image
    with Image.open(big) as im: w, h = im.size
    return {'path': rel(big), 'thumb': rel(sm), 'w': w, 'h': h, 'bytes': os.path.getsize(big) + os.path.getsize(sm)}
