# Daily competitor intelligence — frame-extractor.app

- **Date:** 2026-10-27 Asia/Shanghai (UTC+8)
- **Scope:** homepage HTTP, sitemap.xml (cap 15 high-value paths), pricing, notable features
- **Prior baseline:** Oct 26 notes in `/workspace/chatgpt-5-competitors-reverse-report.md` + `/workspace/chatgpt-5-competitors-geo-teardown.md` (no prior `frame-daily-competitor-*.md` found)
- **Raw sitemaps archived:** `/workspace/competitor-snapshots/2026-10-27/`

---

## RED items

**None.**

- No paid-tier / dollar pricing found on any of the 5 competitors (all Schema.org `Offer` price=`0` USD or explicit “free / no paywall / no premium”).
- No >5% price change vs baseline (baseline = free forever; still free).
- Sitemap URL counts for `framify.video` (9) and `getframesfromvideo.com` (8) **unchanged** vs Oct 26 reverse-report baseline.
- No sitemap `lastmod` newer than 2026-09-12 across the five (stale relative to today).

---

## Per-competitor

### 1. https://frame-extractor.com

| Field | Value |
|---|---|
| Homepage HTTP | **200** (21 319 B, ~0.12s) |
| robots.txt | 200 — `Sitemap: /sitemap.xml` |
| Sitemap | **200** — **13** URLs (locale shells only) |
| Pricing page | `/pricing` **404**; no paid CTA; free tool (simple-tools.dev) |
| lastmod | all `2026-08-30` |

**High-value paths (all 13):**
`/en` `/ar` `/es` `/fr` `/de` `/hi` `/it` `/pl` `/pt` `/zh` `/tw` `/ja` `/ko`

**vs prior:** Locale matrix stable; no new tool/blog routes. Same-name `.com` dilution risk vs our `.app` still applies (noted Oct 26 GEO teardown).

**Notable features (1–3):**
- Multi-locale SPA shell (`English / العربية / … / 한국어`) with feature-request hook
- Minimal marketing surface — tool-first, little programmatic SEO depth
- Brand ownership under `simple-tools.dev`

---

### 2. https://framify.video

| Field | Value |
|---|---|
| Homepage HTTP | **200** (71 354 B) |
| robots.txt | 200 — absolute sitemap |
| Sitemap | **200** — **9** URLs (**same as Oct 26**) |
| Pricing | `/pricing` **404**; Schema `price: 0` USD |
| lastmod | all `2026-08-23` |

**High-value paths (cap 15, all non-legal):**
1. `/extract-frames-from-video-online`
2. `/extract-frames-from-video`
3. `/extract-frame-from-mp4`
4. `/how-to-save-a-frame-from-a-video-iphone`
5. `/how-to-save-a-single-frame-from-video-capcut`
6. `/` (+ `/contact` `/privacy` `/terms`)

**vs prior:** No new URLs since Oct 26 baseline (still 9).

**Notable features:**
- Browser-local extractor with FPS / exact-count framing (llms.txt historically mirrors ChatGPT fan-out copy)
- Strong how-to SEO for **iPhone** + **CapCut** frame-save intents
- MP4-focused landing + “video to frames right in your browser” Quick-Answer style H1s

---

### 3. https://getframesfromvideo.com  (brand: FramesFromVideo)

| Field | Value |
|---|---|
| Homepage HTTP | **200** (82 238 B) |
| robots.txt | 200 |
| Sitemap | **200** — **8** URLs (**same as Oct 26**) |
| Pricing | `/pricing` **404**; copy: “no account, subscription, payment, or premium tier”; Schema `price:0` |
| lastmod | newest `2026-08-16` (tool pages) |

**High-value paths:**
1. `/frame-by-frame-video-viewer`
2. `/video-screenshot`
3. `/video-to-sprite-sheet`
4. `/gif-to-frames`
5. `/es`
6. `/` (+ privacy/terms)

**vs prior:** URL set unchanged vs Oct 26 reverse-report.

**Notable features:**
- Mode matrix: FPS / every-N-seconds / exact-time + ordered ZIP
- Differentiated tool pages: frame-by-frame viewer, sprite sheet (+ JSON/CSS coords historically), GIF→frames
- Explicit anti-paywall positioning (“No signup · No paywall”)

---

### 4. https://framesfromvideo.com

| Field | Value |
|---|---|
| Homepage HTTP | **200** (68 417 B) |
| robots.txt | 200 — `Sitemap: https://framesfromvideo.com/sitemap.xml` |
| Sitemap | **200** — **42** URLs (programmatic SEO + i18n + Live Photo suite) |
| “Pricing” `/pricing` `/plans` `/blog` | Soft **200** SPA catch-alls; **canonical → `/`**; **no $ prices** (Schema `price:0`, `isAccessibleForFree:true`) |
| lastmod | all `2026-08-31` |

**High-value paths (top 15):**
1. `/video-to-live-photo/`
2. `/image-to-live-photo/`
3. `/mp4-to-live-photo/`
4. `/gif-to-live-photo/`
5. `/photo-to-moving-photo/`
6. `/extract-frame-at-timestamp/`
7. `/extract-frames-every-second/`
8. `/extract-fixed-number-of-frames/`
9. `/video-contact-sheet-generator/`
10. `/video-storyboard-maker/`
11. `/video-thumbnail-maker/`
12. `/extract-frames-from-mp4/` `/extract-frames-from-mov/` `/extract-frames-from-webm/`
13. `/extract-frames-from-video-on-mac/` `/…-windows/` `/…-iphone/` `/…-android/`
14. `/video-to-jpg/` `/video-to-png/` `/video-to-webp/`
15. `/guides/`

**vs prior:** Not quantified in Oct 26 ChatGPT-top5 table (that tracked `getframesfromvideo.com`); **first daily snapshot = 42 URLs**. Distinct domain from getframes*, heavier Live Photo + device-guide programmatic SEO.

**Notable features:**
- **Video/Image → Live Photo** paired ZIP bundle (still + motion + manifest) — unique vs our current product
- Interval / target-count (≤240) / exact-timestamp modes + contact sheet + JPG/PNG/WebP
- 13 locale roots (`/zh/` `/es/` … `/vi/`) + OS how-to landers

---

### 5. https://extractvideoframes.com → www

| Field | Value |
|---|---|
| Homepage HTTP | **200** (38 663 B; Host points to `www.extractvideoframes.com`) |
| robots.txt | 200 — Sitemap on **www** |
| Sitemap | **200** — **14** URLs |
| Pricing | `/pricing` **404**; Schema `price:0` USD |
| lastmod | all `2026-09-12` (newest among the five) |

**High-value paths:**
1. `/gif-frame-extractor`
2. `/gif-to-sprite-sheet`
3. `/sprite-sheet-splitter`
4. `/video-to-sprite-sheet`
5. `/frame-by-frame-video-viewer`
6. `/video-fps-checker`
7. `/timecode-calculator`
8. `/` (+ about/contact/legal/affiliate)

**vs prior:** No prior daily count; utility-suite pattern (FPS checker, timecode calc, sprite tools) — adjacent SEO, not pure extractor.

**Notable features:**
- Exact + batch + “Best Frames” / one-frame-per-scene modes (homepage copy)
- GIF ↔ sprite tooling cluster
- Utility calculators (FPS, timecode) as long-tail magnets

---

## Newcomers (WebSearch 2026-10-27)

All probed **HTTP 200** (not in the core-5 list; watchlist):

| Newcomer | Signal |
|---|---|
| **https://framecatcher.app** (+ `/tools/extract-frames-from-video`) | Auto **shot-boundary** first/mid/last frames; contact sheet / GIF / palette / ZIP; local |
| **https://pilko.studio** | “Last updated **2026-09-20**”; histogram/pixel-diff scene detect, SRT/VTT, overlays, grid, open-source |
| **https://www.frameripper.com** (`/tool`) | Evenly spaced N frames → ZIP; JPEG/PNG/WebP; offline-after-load; 10k frame cap |
| **https://vixframe.com** | Single/batch/range; **PNG/JPG/WebP/AVIF**; local ZIP |
| Still live (Oct 26 set) | `videoframe-extractor.com`, `frameclipper.com` |

---

## Chase Todo (3)

1. **Intercept `framesfromvideo.com` Live Photo + contact-sheet programmatic URLs** — ship comparison / feature landers (or product gap notes for 架构总工) for `video-to-live-photo`, `video-contact-sheet-generator`, device how-tos (`…-on-iphone|mac|windows|android`); they have **42** indexed routes vs our thinner matrix.
2. **Watchlist → GEO counter for Pilko Studio + FrameCatcher** — scene-change / shot-boundary / SRT-driven capture is the only clear feature delta vs our PTS loupe; draft Answer-First comparison bullets for llms.txt + blog “best browser extractors” so AI lists don’t skip `.app`.
3. **Keep pressure on `getframesfromvideo.com` tool-page intents** — `/frame-by-frame-video-viewer`, `/video-to-sprite-sheet`, `/gif-to-frames`, `/video-screenshot` still only 8 URLs but high ChatGPT/Bing fan-out value; finish on-site dedicated routes + continue comment/directory parity (already started Oct 26).

---

## Method notes

- Tools: `curl` HTTP/status + sitemap download; WebFetch on FFV pricing; WebSearch for newcomers; prior baselines from Oct 26 competitor MD reports.
- Soft-200 caveat: `framesfromvideo.com/{pricing,plans,blog}` return homepage HTML with canonical `/` — treat as **no dedicated pricing/blog**, not as paid plans.
- `framesfromvideo.com/sitemap_index.xml` returns homepage HTML (not a real index); real map is `/sitemap.xml`.
