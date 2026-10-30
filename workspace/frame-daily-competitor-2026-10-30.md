# Daily competitor intelligence — frame-extractor.app

- **Date:** 2026-10-30 Asia/Shanghai (UTC+8)
- **Scope:** homepage HTTP, sitemap.xml, pricing probes, blog/guides dates, SERP spot-check
- **Prior:** `/workspace/frame-daily-competitor-2026-10-28.md` (no 2026-10-29 file found)
- **Raw:** `/workspace/frame-daily-runs/2026-10-30-competitor-raw/` + archive `/workspace/competitor-snapshots/2026-10-30/`

---

## RED items

**None.** Quiet day.

- No paid-tier / dollar pricing on any of the 5 (Schema.org `Offer` price=`0` USD or free; getframes “premium/subscription/paywall” hits are anti-paywall copy only).
- No >5% price change vs Oct 28 baseline (still free forever).
- Sitemap URL counts **unchanged** vs 2026-10-28 for all five; **zero** added/removed locs.
- Newest sitemap `lastmod` still **2026-09-12** (extractvideoframes); others stale Aug 2026.
- No new high-value tool/blog routes; no recent blog publish dates.

---

## Sitemap count vs 2026-10-28

| Competitor | 2026-10-28 | 2026-10-30 | Δ |
|---|---:|---:|---|
| frame-extractor.com | 13 | 13 | 0 |
| framify.video | 9 | 9 | 0 |
| getframesfromvideo.com | 8 | 8 | 0 |
| framesfromvideo.com | 42 | 42 | 0 |
| www.extractvideoframes.com | 14 | 14 | 0 |

---

## Per-competitor (material only)

### 1. https://frame-extractor.com — HTTP 200 (21 495 B)

- Sitemap **200** / 13 locale shells; lastmod all `2026-08-30`; `/pricing` **404**; `/blog` **404**.
- Home byte delta vs Oct 28 (+176 B) = **Cloudflare challenge script churn only** (free-llm confirm: no pricing/feature/page/blog change).

### 2. https://framify.video — HTTP 200 (71 354 B)

- Sitemap **200** / 9 URLs; lastmod all `2026-08-23`; Schema `price: 0` USD; `/pricing` **404**; `/blog` **404**.
- Home **byte-identical** to Oct 28 snapshot.

### 3. https://getframesfromvideo.com — HTTP 200 (82 238 B)

- Sitemap **200** / 8 URLs; newest lastmod `2026-08-16`; Schema `price: 0`; `/pricing` **404**; `/blog` **404**.
- Home **byte-identical** to Oct 28. Still free (“no account, subscription, payment, or premium tier”).

### 4. https://framesfromvideo.com — HTTP 200 (68 417 B)

- Sitemap **200** / 42 URLs; lastmod all `2026-08-31`; Schema `price: 0` + `isAccessibleForFree:true`.
- `/pricing` **200** but SPA shell == home (no paid CTA). `/blog` soft-200 same shell; real hub `/guides/` (guides page lastmod/date still **2026-08-31**).
- Home **byte-identical** to Oct 28. Live Photo + contact-sheet + device how-tos still deepest matrix among peers (watch, not RED).

### 5. https://extractvideoframes.com → www — HTTP 200 (38 663 B)

- Apex redirects to www; sitemap **200** / 14 URLs; lastmod all `2026-09-12`; Schema `price: 0`; `/pricing` **404**; `/blog` **404**.
- Home **byte-identical** to Oct 28 `*-home-final.html`.

---

## WebSearch: `extract frames from video online` (2026-10-30)

Tools **actually returned** in this search (top 5 links only; do not invent ranks beyond what the tool listed):

1. https://frame-extractor.online/ — Video Frame Extractor (not our `.app`; not in core-5)
2. https://framesgrabber.com/ — frame grabber (newcomer watch)
3. https://framify.video/ — Framify (**tracked**)
4. https://www.anytool.tech/video-to-frames — AnyTool
5. https://vidshift.io/extract-frames/ — VidShift

**Not present** in this WebSearch top-5 list: `frame-extractor.app`, `frame-extractor.com`, `getframesfromvideo.com`, `framesfromvideo.com`, `extractvideoframes.com`.

---

## Watch / non-RED (unchanged)

1. framesfromvideo.com Live Photo + contact-sheet + device how-tos (42 routes) — still the SEO-depth leader.
2. framify.video iPhone / CapCut how-to landers.
3. getframesfromvideo.com tool intents (frame-by-frame / sprite / gif-to-frames / video-screenshot).
4. SERP newcomers **frame-extractor.online**, **framesgrabber.com**, **anytool.tech**, **vidshift.io** — monitor for GEO fan-out; not RED (no pricing / no new core-5 pages).

---

## Method

- `curl` home + sitemap + `/pricing|/plans|/price` + blog/guides status/size
- Schema.org Offer / free-copy scrape; sitemap loc set diff vs Oct 28 snapshots
- `free-llm` on frame-extractor.com HTML diff (CF noise only)
- WebSearch once for query above; report only returned URLs
