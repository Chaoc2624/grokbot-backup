"""
Inbound image download for the WeChat bridge (port of the official plugin's
cdn/pic-decrypt.ts, cdn/aes-ecb.ts, cdn/cdn-url.ts and media/media-download.ts).

Images arrive as item_list entries of type 2 (image_item). The bytes live on the
WeChat CDN, AES-128-ECB encrypted (PKCS7). Key source, as in the plugin:
  image_item.aeskey (hex, preferred)  else  image_item.media.aes_key (base64 of 16 raw
  bytes, or base64 of a 32-char hex string). No key -> plain (unencrypted) download.
URL: image_item.media.full_url if present, else
  {CDN_BASE_URL}/download?encrypted_query_param=<urlencoded encrypt_query_param>.

Outbound HTTPS GET only. Nothing here ever logs or returns URLs, query params or keys.
"""
from __future__ import annotations

import base64
import binascii
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import common as C
import ilink

MEDIA_DIR = os.path.join(C.STATE_DIR, "media")
MAX_BYTES = 100 * 1024 * 1024          # plugin WEIXIN_MEDIA_MAX_BYTES
TIMEOUT_S = 30.0


class MediaError(Exception):
    """Message is always safe to log / forward (no URL, no key, no content)."""


# --------------------------------------------------------------------------- crypto

def parse_aes_key(aes_key_b64: str) -> bytes:
    """pic-decrypt.ts parseAesKey: base64(16 raw bytes) or base64(32 hex chars)."""
    try:
        d = base64.b64decode(aes_key_b64 + "=" * (-len(aes_key_b64) % 4))
    except (binascii.Error, ValueError):
        raise MediaError("aes_key is not valid base64") from None
    if len(d) == 16:
        return d
    if len(d) == 32 and re.fullmatch(rb"[0-9a-fA-F]{32}", d):
        return bytes.fromhex(d.decode("ascii"))
    raise MediaError(f"aes_key decodes to {len(d)} bytes (need 16 raw or 32 hex)")


def image_key_b64(img: dict) -> str | None:
    """media-download.ts: image_item.aeskey (hex) preferred, else media.aes_key."""
    hexkey = (img.get("aeskey") or "").strip()
    if hexkey:
        try:
            return base64.b64encode(bytes.fromhex(hexkey)).decode()
        except ValueError:
            raise MediaError("image_item.aeskey is not valid hex") from None
    return ((img.get("media") or {}).get("aes_key") or None)


def decrypt_aes_ecb(ct: bytes, key: bytes) -> bytes:
    """aes-ecb.ts decryptAesEcb: AES-128-ECB with PKCS7 padding."""
    if len(key) != 16:
        raise MediaError("AES key must be 16 bytes")
    if not ct or len(ct) % 16:
        raise MediaError(f"ciphertext length {len(ct)} is not a positive multiple of 16")
    dec = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    padded = dec.update(ct) + dec.finalize()
    try:
        unp = padding.PKCS7(128).unpadder()
        return unp.update(padded) + unp.finalize()
    except ValueError:
        raise MediaError("decrypt failed (bad padding / wrong key)") from None


def encrypt_aes_ecb(pt: bytes, key: bytes) -> bytes:
    """Counterpart of decrypt_aes_ecb (used by tests)."""
    p = padding.PKCS7(128).padder()
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(p.update(pt) + p.finalize()) + enc.finalize()


# --------------------------------------------------------------------------- download

def build_cdn_download_url(encrypt_query_param: str, cdn_base: str = ilink.CDN_BASE_URL) -> str:
    """cdn-url.ts buildCdnDownloadUrl."""
    return f"{cdn_base}/download?encrypted_query_param={urllib.parse.quote(encrypt_query_param, safe='')}"


def fetch_bytes(url: str, timeout: float = TIMEOUT_S, max_bytes: int = MAX_BYTES) -> bytes:
    if urllib.parse.urlsplit(url).scheme not in ("https", "http"):
        raise MediaError("refusing non-http(s) media URL")
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": ilink.BOT_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            buf = bytearray()
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                buf += chunk
                if len(buf) > max_bytes:
                    raise MediaError(f"media larger than {max_bytes // (1024 * 1024)} MB")
            return bytes(buf)
    except urllib.error.HTTPError as e:
        raise MediaError(f"CDN HTTP {e.code}") from None
    except urllib.error.URLError as e:
        raise MediaError(f"CDN network error ({type(e.reason).__name__})") from None
    except (TimeoutError, OSError) as e:
        raise MediaError(f"CDN network error ({type(e).__name__})") from None


_MAGIC = ((b"\xff\xd8\xff", "jpg"), (b"\x89PNG\r\n\x1a\n", "png"), (b"GIF87a", "gif"),
          (b"GIF89a", "gif"), (b"BM", "bmp"))


def sniff_ext(data: bytes) -> str:
    for sig, ext in _MAGIC:
        if data.startswith(sig):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[4:8] == b"ftyp" and data[8:12] in (b"heic", b"heix", b"mif1", b"msf1", b"hevc"):
        return "heic"
    return "bin"


def _safe_id(mid: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", str(mid)).strip("_")
    return s[:80] or "msg"


def save_private(data: bytes, mid: str, n: int) -> str:
    os.makedirs(MEDIA_DIR, mode=0o700, exist_ok=True)
    os.chmod(MEDIA_DIR, 0o700)
    path = os.path.join(MEDIA_DIR, f"{_safe_id(mid)}_{n}.{sniff_ext(data)}")
    tmp = f"{path}.tmp.{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    return os.path.abspath(path)


def download_image(img: dict, mid: str, n: int, cdn_base: str = ilink.CDN_BASE_URL) -> str:
    """Download (+decrypt) one image_item and save it. Returns the absolute path."""
    media = img.get("media") or {}
    eqp, full = media.get("encrypt_query_param"), media.get("full_url")
    if not eqp and not full:
        raise MediaError("image has no CDN reference")
    key_b64 = image_key_b64(img)
    url = full or build_cdn_download_url(eqp, cdn_base)
    data = fetch_bytes(url)
    if key_b64:
        data = decrypt_aes_ecb(data, parse_aes_key(key_b64))
    if not data:
        raise MediaError("empty image")
    return save_private(data, mid, n)


def image_items(msg: dict) -> list[dict]:
    return [it.get("image_item") or {} for it in (msg.get("item_list") or [])
            if it.get("type") == ilink.ITEM_IMAGE]


def download_message_images(msg: dict, mid: str, log=None) -> tuple[list[str], str | None]:
    """All image items of one message -> (paths, error-or-None). Partial success allowed."""
    paths, errs = [], []
    imgs = image_items(msg)
    for n, img in enumerate(imgs, 1):
        try:
            p = download_image(img, mid, n)
        except MediaError as e:
            err = str(e)
        except Exception as e:  # noqa: BLE001 - never let a bad image kill the forwarder
            err = type(e).__name__
        else:
            paths.append(p)
            if log:
                log.info("image %d/%d of %s saved (%d bytes)", n, len(imgs), mid, os.path.getsize(p))
            continue
        errs.append(f"image {n}: {err}")
        if log:
            log.warning("image %d/%d of %s failed: %s", n, len(imgs), mid, err)
    return paths, ("; ".join(errs) or None)
