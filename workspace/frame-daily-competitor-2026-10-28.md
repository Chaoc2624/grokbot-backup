# Daily competitor intelligence — frame-extractor.app

- **Date:** 2026-10-28 Asia/Shanghai (UTC+8)
- **Scope:** homepage HTTP, sitemap.xml (cap 15 high-value paths), pricing, blogs
- **Prior:** `/workspace/frame-daily-competitor-2026-10-27.md`
- **Raw sitemaps:** `/workspace/competitor-snapshots/2026-10-28/`

---

## RED items

**None.**

- No paid-tier / dollar pricing on any of the 5 (Schema.org `Offer` price=`0` USD or free).
- No >5% price change vs baseline (still free forever).
- Sitemap URL counts **unchanged** vs 2026-10-27 for all five.
- No sitemap `lastmod` newer than **2026-09-12** (extractvideoframes); others stale Aug 2026.
- No new high-value tool/blog routes detected.

---

## Sitemap count vs yesterday

| Competitor | 2026-10-27 | 2026-10-28 | Δ |
|---|---:|---:|---|
| frame-extractor.com | 13 | 13 | 0 |
| framify.video | 9 | 9 | 0 |
| getframesfromvideo.com | 8 | 8 | 0 |
| framesfromvideo.com | 42 | 42 | 0 |
| www.extractvideoframes.com | 14 | 14 | 0 |

---

## Per-competitor

### 1. https://frame-extractor.com

| Field | Value |
|---|---|
| Homepage HTTP | **200** (21 319 B) |
| Sitemap | **200** — **13** URLs (locale shells only) |
| Pricing | `/pricing` **404**; free |
| lastmod | all `2026-08-30` |
| Blog | `/blog` **404** |

**High-value paths:** `/en` `/ar` `/es` `/fr` `/de` `/hi` `/it` `/pl` `/pt` `/zh` `/tw` `/ja` `/ko`

**vs prior:** Stable; same-name `.com` dilution risk unchanged.

### 2. https://framify.video

| Field | Value |
|---|---|
| Homepage HTTP | **200** (71 354 B) |
| Sitemap | **200** — **9** URLs |
| Pricing | `/pricing` **404**; Schema `price: 0` |
| lastmod | all `2026-08-23` |
| Blog | `/blog` **404** |

**High-value paths:** `/extract-frames-from-video-online` `/extract-frames-from-video` `/extract-frame-from-mp4` `/how-to-save-a-frame-from-a-video-iphone` `/how-to-save-a-single-frame-from-video-capcut` (+ contact/privacy/terms)

**vs prior:** No new URLs; iPhone/CapCut how-tos still the interception watchlist.

### 3. https://getframesfromvideo.com

| Field | Value |
|---|---|
| Homepage HTTP | **200** (82 238 B) |
| Sitemap | **200** — **8** URLs |
| Pricing | `/pricing` **404**; Schema `price: 0` |
| lastmod | newest `2026-08-16` |
| Blog | `/blog` **404** |

**High-value paths:** `/` `/es` `/video-screenshot` `/frame-by-frame-video-viewer` `/video-to-sprite-sheet` `/gif-to-frames` (+ privacy/terms)

**vs prior:** Unchanged; continue comment/directory interception on overlapping intents.

### 4. https://framesfromvideo.com

| Field | Value |
|---|---|
| Homepage HTTP | **200** (68 417 B) |
| Sitemap | **200** — **42** URLs |
| Pricing | `/pricing` **200** but SPA shell = home; Schema `price: 0` (no paid CTA) |
| lastmod | all `2026-08-31` |
| Blog | `/blog` **200** but same SPA shell as home (not in sitemap); real content hub is `/guides/` |

**High-value non-locale paths (sample):**  
`/extract-frames-from-video/` `/video-frame-extractor/` `/video-to-live-photo/` `/image-to-live-photo/` `/video-contact-sheet-generator/` `/extract-frames-every-second/` `/extract-video-frames-on-iphone/` (+ mac/windows/android) `/mp4-to-live-photo/` `/guides/`

**vs prior:** No sitemap growth; Live Photo + device-guide programmatic SEO still deepest among peers.

### 5. https://extractvideoframes.com → https://www.extractvideoframes.com/

| Field | Value |
|---|---|
| Apex | **308 → www** |
| Homepage HTTP | **200** (38 663 B on www) |
| Sitemap | **200** — **14** URLs |
| Pricing | `/pricing` **404**; Schema `price: 0` |
| lastmod | all `2026-09-12` (newest among five) |
| Blog | `/blog` **404** |

**High-value paths:** `/gif-frame-extractor` `/gif-to-sprite-sheet` `/sprite-sheet-splitter` `/timecode-calculator` `/video-fps-checker` `/frame-by-frame-video-viewer` `/video-to-sprite-sheet` (+ about/contact/legal)

**vs prior:** Unchanged count; GIF/sprite/utility niche still distinct.

---

## Watch / non-RED follow-ups

1. Keep monitoring **framesfromvideo.com** Live Photo + contact-sheet + device how-tos (42 routes) for any new `lastmod` / URL adds.
2. **framify.video** iPhone / CapCut how-to intent pages — still worth interception landers (TDH changes need user + SEO总参谋).
3. **getframesfromvideo.com** tool intents (`frame-by-frame`, sprite, gif-to-frames, video-screenshot) — parity + comment interception.
4. No pricing wars; all free → differentiation stays feature depth + GEO trust, not paywall.

---

## Method

- `curl` homepage / robots / sitemap / pricing / blog status codes + body sizes
- Schema.org Offer price scrape
- Diff URL counts vs 2026-10-27 competitor report
