# Daily competitor intelligence — frame-extractor.app

- **Date:** 2026-11-01 Asia/Singapore (UTC+8)
- **Scope:** homepage HTTP, sitemap.xml, pricing probes, blog/guides dates, SERP spot-check
- **Prior:** `/workspace/frame-daily-runs/2026-10-31-competitors.md` + `/workspace/frame-daily-competitor-2026-10-31.md`
- **Raw:** `/workspace/frame-daily-runs/2026-11-01-competitor-raw/`

---

## RED items

**None.** Quiet day vs 2026-10-31 on tracked competitors.

- No paid-tier / dollar pricing on any of the 5 (Schema.org `Offer` price=`0` USD or free; getframes “premium/subscription/paywall” hits remain anti-paywall copy only; stray `$` tokens in RSC payloads are Next.js flight IDs, not prices).
- No >5% price change vs Oct 31 baseline (still free forever).
- Sitemap URL counts **unchanged** vs 2026-10-31 for all five; **zero** added/removed locs.
- Newest sitemap `lastmod` still **2026-09-12** (extractvideoframes); others stale Aug 2026.
- No new high-value tool/blog routes.
- Homepages: 4/5 **byte-identical** to 10-31; `frame-extractor.com` same 21 495 B, hash differs only in Cloudflare `__CF$cv$params` challenge token (content-identical aside from that).

**SERP note (not competitor RED):** our `.app` dropped out of WebSearch top-5 for `extract frames from video online` (was #5 on 10-31). See SERP section.

---

## Sitemap count vs 2026-10-31

| Competitor | 2026-10-31 | 2026-11-01 | Δ |
|---|---:|---:|---|
| frame-extractor.com | 13 | 13 | 0 |
| framify.video | 9 | 9 | 0 |
| getframesfromvideo.com | 8 | 8 | 0 |
| framesfromvideo.com | 42 | 42 | 0 |
| www.extractvideoframes.com | 14 | 14 | 0 |

---

## Per-competitor (material only)

### 1. https://frame-extractor.com — HTTP 200 (21 495 B)

- sha256 `2b635b5ded5aba2b80df7809166f33de5c04bc2118d3325d57086311bc2299d2` (Δ vs 10-31 = Cloudflare `__CF$cv$params` only; size Δ **0**).
- Sitemap **200** / 13 locale shells; lastmod all `2026-08-30`; `/pricing` **404**; `/blog` **404**.
- No Schema Offer / free-copy markers on home (unchanged pattern).

### 2. https://framify.video — HTTP 200 (71 354 B)

- Sitemap **200** / 9 URLs; lastmod all `2026-08-23`; Schema `price: 0` USD; `/pricing` **404**; `/blog` **404**.
- Home **byte-identical** to Oct 31.
- Present at **#5** on primary SERP query today (tracked).

### 3. https://getframesfromvideo.com — HTTP 200 (82 238 B)

- Sitemap **200** / 8 URLs; newest lastmod `2026-08-16`; Schema `price: 0`; `/pricing` **404**; `/blog` **404**.
- Home **byte-identical** to Oct 31. Still free (“no account / subscription / premium” anti-paywall copy).

### 4. https://framesfromvideo.com — HTTP 200 (68 417 B)

- Sitemap **200** / 42 URLs; lastmod all `2026-08-31`; Schema `price: 0` + `isAccessibleForFree:true`.
- `/pricing` **200** but SPA shell == home (no paid CTA). `/blog` soft-200; real hub `/guides/` (still **200**, 36 064 B, **byte-identical** to 10-31).
- Home **byte-identical** to Oct 31. Live Photo + contact-sheet + device how-tos still deepest matrix among peers (watch, not RED).

### 5. https://extractvideoframes.com → www — HTTP 200 (38 663 B)

- Apex redirects to www; sitemap **200** / 14 URLs; lastmod all `2026-09-12`; Schema `price: 0`; `/pricing` **404**.
- `/blog`: apex **308** → www → **404** (same soft pattern as 10-31 report).
- Home **byte-identical** to Oct 31.

---

## WebSearch: `extract frames from video online` (2026-11-01)

Tools **actually returned** in this search (top 5 links only; do not invent ranks beyond what the tool listed):

1. https://www.framepeel.com/ — FramePeel (**new SERP peer / watch**)
2. https://frame-extractor.online/ — Frame Extractor (`.online`, not our `.app`)
3. https://www.frameripper.com/ — FrameRipper
4. https://toframes.video/ — Video to Frames (**new SERP peer / watch**)
5. https://framify.video/ — Framify (**tracked**)

**Our site:** https://frame-extractor.app/ — **NOT in this WebSearch top-5** (was #5 on 2026-10-31).

**Not present** in this WebSearch top-5 list: `frame-extractor.com`, `getframesfromvideo.com`, `framesfromvideo.com`, `extractvideoframes.com`, and our `.app`.

---

## Optional SERP: `video frame extractor` (2026-11-01)

1. https://www.framepeel.com/ — FramePeel
2. https://frame-extractor.app/ — **our site (#2)**
3. https://framify.video/extract-frames-from-video — Framify lander
4. https://videocontextapi.com/tools/extract-frames/ — Video Context API
5. https://olovetools.com/en/framesnap/ — FrameSnap

## Optional SERP: `frame extractor` (2026-11-01)

1. https://www.framepeel.com/ — FramePeel
2. https://framify.video/ — Framify
3. https://wutools.com/video/extract-frames — WuTools
4. https://en.ud5.com/tool/webcodecs-video-frame-reader — UD5 WebCodecs
5. https://frame-extractor.app/ — **our site (#5)**

---

## Watch / non-RED

1. framesfromvideo.com Live Photo + contact-sheet + device how-tos (42 routes) — still the SEO-depth leader.
2. framify.video iPhone / CapCut how-to landers; held #5 on primary query.
3. getframesfromvideo.com tool intents (frame-by-frame / sprite / gif-to-frames / video-screenshot).
4. **FramePeel** (`framepeel.com`) — #1 on all three queries today; monitor GEO fan-out.
5. **toframes.video** — new primary-SERP #4; monitor.
6. Continuing peers: frame-extractor.online, frameripper.com, FrameSnap / WuTools / videocontextapi.
7. Our `.app` primary-query drop (#5 → absent) — watch next daily; still #2 on `video frame extractor` and #5 on `frame extractor`.

---

## Method

- `curl` home + sitemap + `/pricing|/plans|/price` + blog/guides status/size (2026-11-01 ~09:02 Asia/Singapore)
- Schema.org Offer / free-copy scrape; sitemap loc set diff vs Oct 31 snapshots (all empty)
- Homepage sha256 vs Oct 31 raw under `/workspace/frame-daily-runs/2026-10-31-competitor-raw/`
- WebSearch for primary + two optional queries; report only returned URLs
