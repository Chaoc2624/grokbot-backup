"""Offline tests: fake creds, mocked HTTP. Never touches the real webhook or iLink."""
import json, os, sys, tempfile, unittest
from unittest import mock

TMP = tempfile.mkdtemp(prefix="wechat-test-")
os.environ["WECHAT_STATE_DIR"] = TMP
os.environ["ILINK_CREDS"] = os.path.join(TMP, "ilink_creds.json")
for k in ("WECHAT_ROUTINE_WEBHOOK_URL", "WECHAT_ROUTINE_WEBHOOK_KEY"):
    os.environ.pop(k, None)  # guarantee no real webhook can be hit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, ilink, forwarder as F, reply as R, media as M  # noqa: E402
import base64, io, urllib.error, urllib.parse  # noqa: E402

BOUND, OTHER = "boss@im.wechat", "stranger@im.wechat"


def msg(mid, frm=BOUND, text="hi", mtype=1, ctx="CTX", voice=None):
    items = [{"type": 3, "voice_item": {"text": voice}}] if voice else [{"type": 1, "text_item": {"text": text}}]
    return {"message_id": mid, "from_user_id": frm, "message_type": mtype, "context_token": ctx,
            "create_time_ms": 1760000000000, "item_list": items}


def reset():
    import shutil
    for f in os.listdir(TMP):
        fp = os.path.join(TMP, f)
        shutil.rmtree(fp) if os.path.isdir(fp) else os.remove(fp)


class TestMarkdown(unittest.TestCase):
    def test_strip(self):
        md = ("# Title\n**bold** and *it* and `code` ~~x~~\n- item\n* star item\n> quote\n"
              "See [docs](https://a.b/c) and ![img](https://i.png)\n---\n"
              "| A | B |\n|---|:--:|\n| 1 | 2 |\n```py\nx = 1\n```\nsnake_case_name stays")
        out = R.strip_markdown(md)
        for bad in ("**", "#", "`", "[docs]", "](", "|", "~~", "---"):
            self.assertNotIn(bad, out, bad)
        self.assertIn("Title", out)
        self.assertIn("bold and it and code x", out)
        self.assertIn("docs https://a.b/c", out)
        self.assertIn("A  B\n1  2", out)
        self.assertIn("x = 1", out)
        self.assertIn("- star item", out)
        self.assertIn("snake_case_name stays", out)
        self.assertIn("img https://i.png", out)

    def test_chinese_and_plain(self):
        self.assertEqual(R.strip_markdown("你好，**主人**！"), "你好，主人！")
        self.assertEqual(R.strip_markdown("2 * 3 = 6"), "2 * 3 = 6")


class TestSplit(unittest.TestCase):
    def test_split(self):
        self.assertEqual(R.split_text("short"), ["short"])
        t = ("段落" * 1500 + "\n\n") * 4  # ~12k chars
        parts = R.split_text(t)
        self.assertTrue(all(len(p) <= 4000 for p in parts))
        self.assertEqual("".join(p.replace("\n", "") for p in parts), t.replace("\n", ""))
        hard = "x" * 9001
        p2 = R.split_text(hard)
        self.assertEqual([len(p) for p in p2], [4000, 4000, 1001])


class TestForwarder(unittest.TestCase):
    def setUp(self):
        reset()
        self.posts = []
        self.fw = F.Forwarder(http_post=lambda p: (self.posts.append(p), 200)[1], sleep=lambda s: None)

    def test_whitelist_dedupe_context(self):
        batch = [msg("1", text="a"), msg("2", frm=OTHER, text="secret-stranger", ctx="BAD"),
                 msg("1", text="a"), msg("3", mtype=2, text="bot echo"), msg("4", voice="语音转文字")]
        with self.assertLogs("wechat-forwarder", "INFO") as cm:
            q = self.fw.handle_msgs(batch, BOUND)
        self.assertEqual([p["message_id"] for p in q], ["1", "4"])
        self.assertEqual(q[1]["text"], "语音转文字")
        self.assertEqual(set(q[0]), {"source", "from_user_id", "message_id", "text", "time"})
        self.assertEqual(q[0]["source"], "wechat")
        logs = "\n".join(cm.output)
        self.assertIn("non-bound sender", logs)
        self.assertNotIn("secret-stranger", logs)
        self.assertNotIn(OTHER, logs)
        ctx = C.read_json(C.CONTEXT)
        self.assertEqual(ctx["context_token"], "CTX")
        self.assertEqual(oct(os.stat(C.CONTEXT).st_mode & 0o777), "0o600")
        # dedupe survives restart
        fw2 = F.Forwarder(http_post=lambda p: 200, sleep=lambda s: None)
        self.assertEqual(fw2.handle_msgs([msg("1"), msg("4", voice="v")], BOUND), [])

    def test_no_allowed_user_fails_closed(self):
        self.assertEqual(self.fw.handle_msgs([msg("9")], ""), [])

    def test_flush_and_retry(self):
        self.fw.handle_msgs([msg("1")], BOUND)
        self.fw.flush_pending(force=True)
        self.assertEqual(len(self.posts), 1)
        self.assertEqual(C.read_json(C.PENDING), [])

    def test_retry_backoff_then_pending(self):
        calls, sleeps = [], []
        fw = F.Forwarder(http_post=lambda p: (calls.append(1), 503)[1], sleep=sleeps.append)
        fw.handle_msgs([msg("7")], BOUND)
        fw.flush_pending(force=True)
        self.assertEqual(len(calls), 6)
        self.assertEqual(sleeps, [1, 2, 4, 8, 16])
        self.assertEqual(len(C.read_json(C.PENDING)), 1)  # kept for later

    def test_retry_recovers(self):
        seq = iter([500, OSError("net"), 200])
        def post(p):
            v = next(seq)
            if isinstance(v, Exception):
                raise v
            return v
        fw = F.Forwarder(http_post=post, sleep=lambda s: None)
        fw.handle_msgs([msg("8")], BOUND)
        fw.flush_pending(force=True)
        self.assertEqual(C.read_json(C.PENDING), [])

    def test_missing_env_no_leak(self):
        fw = F.Forwarder(sleep=lambda s: None)  # real webhook_post, env is unset -> no network
        fw.handle_msgs([msg("5")], BOUND)
        fw.flush_pending(force=True)
        self.assertEqual(len(fw.pending), 1)

    def test_run_loop_cursor_and_stale_token(self):
        C.write_json(C.CREDS, {"bot_token": "T1", "baseurl": "https://x", "ilink_user_id": BOUND})
        calls = []
        def gu(cursor, **kw):
            calls.append(cursor)
            if len(calls) == 1:
                return {"ret": 0, "msgs": [msg("11")], "get_updates_buf": "B1"}
            if len(calls) == 2:
                return {"ret": 0, "msgs": [], "get_updates_buf": ""}
            raise ilink.IlinkError("x", ret=-14)
        n = {"s": 0}
        def sl(s):
            n["s"] += 1
            if n["s"] > 2:
                fw.running = False
        fw = F.Forwarder(get_updates=gu, http_post=lambda p: (self.posts.append(p), 200)[1], sleep=sl)
        fw.run()
        self.assertEqual(calls, ["", "B1", "B1"])  # empty buf not persisted
        self.assertEqual(C.read_json(C.CURSOR)["get_updates_buf"], "B1")
        self.assertEqual(C.get_status(), "expired")
        self.assertEqual(len(calls), 3)  # stopped polling after -14
        self.assertEqual([p["message_id"] for p in self.posts], ["11"])


class TestReply(unittest.TestCase):
    def setUp(self):
        reset()

    def run_main(self, text="**hi**"):
        with self.assertRaises(SystemExit) as cm:
            R.main(["reply.py", text]); raise SystemExit(0)
        return cm.exception.code

    def test_no_creds(self):
        self.assertEqual(self.run_main(), 3)

    def test_no_context(self):
        C.write_json(C.CREDS, {"bot_token": "T", "ilink_user_id": BOUND})
        self.assertEqual(self.run_main(), 4)

    def _ready(self):
        C.write_json(C.CREDS, {"bot_token": "T", "ilink_user_id": BOUND})
        C.save_context(msg("1"))

    def test_send_ok_plain_and_split(self):
        self._ready()
        sent = []
        with mock.patch.object(ilink, "send_text", lambda to, ctx, t, **kw: sent.append((to, ctx, t)) or {"ret": 0}):
            self.assertEqual(self.run_main("**粗体** " + "y" * 5000), 0)
        self.assertEqual(len(sent), 2)
        self.assertTrue(all(s[0] == BOUND and s[1] == "CTX" for s in sent))
        self.assertTrue(sent[0][2].startswith("粗体 "))

    def test_error_codes(self):
        self._ready()
        for ret, code in ((-14, 14), (-2, 2), (-99, 1)):
            def boom(*a, **k):
                raise ilink.IlinkError("x", ret=ret)
            with mock.patch.object(ilink, "send_text", boom):
                self.assertEqual(self.run_main(), code, ret)


# ----------------------------------------------------------------------------- images
KEY = bytes(range(16))
PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-image-bytes" * 50
JPG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 33
EQP = "SECRET_EQP+/=abc"


def img_item(eqp=EQP, aeskey_hex=None, aes_key=None, full_url=None):
    media = {"encrypt_query_param": eqp} if eqp else {}
    if aes_key:
        media["aes_key"] = aes_key
    if full_url:
        media["full_url"] = full_url
    it = {"media": media}
    if aeskey_hex:
        it["aeskey"] = aeskey_hex
    return {"type": 2, "image_item": it}


def img_msg(mid, items, frm=BOUND):
    return {"message_id": mid, "from_user_id": frm, "message_type": 1, "context_token": "CTX",
            "create_time_ms": 1760000000000, "item_list": items}


class FakeCDN:
    """Stands in for urllib.request.urlopen inside media.py."""
    def __init__(self, routes):
        self.routes, self.urls = routes, []

    def __call__(self, req, timeout=None):
        url = req.full_url
        self.urls.append(url)
        v = self.routes.get(url, self.routes.get("*"))
        if isinstance(v, int):
            raise urllib.error.HTTPError(url, v, "err", {}, None)
        if v is None:
            raise urllib.error.URLError(OSError("no route"))
        return io.BytesIO(v)


class TestImageCrypto(unittest.TestCase):
    def test_roundtrip_and_key_formats(self):
        ct = M.encrypt_aes_ecb(PNG, KEY)
        self.assertNotEqual(ct[:8], PNG[:8])
        self.assertEqual(M.decrypt_aes_ecb(ct, KEY), PNG)
        raw_b64 = base64.b64encode(KEY).decode()
        hex_b64 = base64.b64encode(KEY.hex().encode()).decode()
        self.assertEqual(M.parse_aes_key(raw_b64), KEY)
        self.assertEqual(M.parse_aes_key(hex_b64), KEY)
        with self.assertRaises(M.MediaError):
            M.parse_aes_key(base64.b64encode(b"x" * 20).decode())
        # image_item.aeskey (hex) preferred over media.aes_key
        it = img_item(aeskey_hex=KEY.hex(), aes_key=base64.b64encode(b"z" * 16).decode())["image_item"]
        self.assertEqual(M.parse_aes_key(M.image_key_b64(it)), KEY)
        with self.assertRaises(M.MediaError):
            M.decrypt_aes_ecb(ct, b"w" * 16)  # wrong key -> padding error
        self.assertEqual(M.build_cdn_download_url("a+b/c=", "https://cdn/c2c"),
                         "https://cdn/c2c/download?encrypted_query_param=a%2Bb%2Fc%3D")


class TestImageForwarding(unittest.TestCase):
    def setUp(self):
        reset()
        self.posts = []
        self.fw = F.Forwarder(http_post=lambda p: (self.posts.append(p), 200)[1], sleep=lambda s: None)

    def test_bound_image_downloaded_decrypted_forwarded(self):
        url = M.build_cdn_download_url(EQP)
        cdn = FakeCDN({url: M.encrypt_aes_ecb(PNG, KEY)})
        with mock.patch.object(M.urllib.request, "urlopen", cdn), \
                self.assertLogs("wechat-forwarder", "INFO") as cm:
            q = self.fw.handle_msgs([img_msg("123", [img_item(aeskey_hex=KEY.hex())])], BOUND)
        self.assertEqual(cdn.urls, [url])
        self.assertTrue(url.startswith(ilink.CDN_BASE_URL + "/download?encrypted_query_param="))
        p = q[0]
        self.assertEqual(p["text"], "[图片]")
        self.assertNotIn("image_error", p)
        self.assertEqual(p["images"], [os.path.join(TMP, "media", "123_1.png")])
        self.assertTrue(os.path.isabs(p["images"][0]))
        with open(p["images"][0], "rb") as f:
            self.assertEqual(f.read(), PNG)
        self.assertEqual(oct(os.stat(p["images"][0]).st_mode & 0o777), "0o600")
        self.assertEqual(oct(os.stat(os.path.join(TMP, "media")).st_mode & 0o777), "0o700")
        logs = "\n".join(cm.output)
        for secret in (EQP, KEY.hex(), "encrypted_query_param", urllib.parse.quote(EQP, safe="")):
            self.assertNotIn(secret, logs)
        self.fw.flush_pending(force=True)
        self.assertEqual(self.posts[0]["images"], p["images"])
        self.assertEqual(C.read_json(C.PENDING), [])
        # dedupe: same message again -> no second download
        with mock.patch.object(M.urllib.request, "urlopen", cdn):
            self.assertEqual(self.fw.handle_msgs([img_msg("123", [img_item(aeskey_hex=KEY.hex())])], BOUND), [])
        self.assertEqual(len(cdn.urls), 1)

    def test_caption_full_url_and_multiple(self):
        hex_b64 = base64.b64encode(KEY.hex().encode()).decode()
        cdn = FakeCDN({"https://cdn.example/full1": M.encrypt_aes_ecb(JPG, KEY),
                       M.build_cdn_download_url("E2"): PNG})  # 2nd: no key -> plain download
        items = [img_item(eqp="E1", aes_key=hex_b64, full_url="https://cdn.example/full1"),
                 {"type": 1, "text_item": {"text": "看看这两张"}}, img_item(eqp="E2")]
        with mock.patch.object(M.urllib.request, "urlopen", cdn):
            p = self.fw.handle_msgs([img_msg("77", items)], BOUND)[0]
        self.assertEqual(p["text"], "看看这两张")
        self.assertEqual([os.path.basename(x) for x in p["images"]], ["77_1.jpg", "77_2.png"])
        self.assertEqual(cdn.urls[0], "https://cdn.example/full1")  # full_url preferred

    def test_download_failure_still_forwarded(self):
        cdn = FakeCDN({"*": 404})
        with mock.patch.object(M.urllib.request, "urlopen", cdn), \
                self.assertLogs("wechat-forwarder", "INFO") as cm:
            q = self.fw.handle_msgs([img_msg("55", [img_item(aeskey_hex=KEY.hex())])], BOUND)
        p = q[0]
        self.assertEqual(p["images"], [])
        self.assertEqual(p["image_error"], "image 1: CDN HTTP 404")
        self.assertEqual(p["text"], "[图片]")
        self.assertNotIn(EQP, "\n".join(cm.output) + json.dumps(p))
        # wrong key and network error also become image_error, never an exception
        cdn2 = FakeCDN({M.build_cdn_download_url("B"): M.encrypt_aes_ecb(PNG, b"q" * 16)})
        with mock.patch.object(M.urllib.request, "urlopen", cdn2):
            p2 = self.fw.handle_msgs([img_msg("56", [img_item(eqp="B", aeskey_hex=KEY.hex()),
                                                     img_item(eqp="C", aeskey_hex=KEY.hex())])], BOUND)[0]
        self.assertEqual(p2["images"], [])
        self.assertIn("image 1: decrypt failed", p2["image_error"])
        self.assertIn("image 2: CDN network error", p2["image_error"])
        self.fw.flush_pending(force=True)
        self.assertEqual([x["message_id"] for x in self.posts], ["55", "56"])

    def test_stranger_media_never_downloaded(self):
        cdn = FakeCDN({"*": M.encrypt_aes_ecb(PNG, KEY)})
        with mock.patch.object(M.urllib.request, "urlopen", cdn):
            q = self.fw.handle_msgs([img_msg("66", [img_item(aeskey_hex=KEY.hex())], frm=OTHER),
                                     dict(img_msg("67", [img_item(aeskey_hex=KEY.hex())]), message_type=2)],
                                    BOUND)
            q2 = self.fw.handle_msgs([img_msg("68", [img_item(aeskey_hex=KEY.hex())])], "")
        self.assertEqual(q + q2, [])
        self.assertEqual(cdn.urls, [])
        self.assertFalse(os.path.exists(os.path.join(TMP, "media")))

    def test_text_payload_unchanged(self):
        q = self.fw.handle_msgs([msg("90", text="plain")], BOUND)
        self.assertEqual(set(q[0]), {"source", "from_user_id", "message_id", "text", "time"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
