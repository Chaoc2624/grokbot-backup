# Daily competitor intelligence — frame-extractor.app

- **Date:** 2026-11-02 Asia/Shanghai (UTC+8)
- **Scope:** homepage HTTP, sitemap.xml, pricing probes, SERP spot-check (task peers + legacy five)
- **Prior:** `/workspace/frame-daily-runs/2026-11-01-competitors.md` + `/workspace/frame-daily-competitor-2026-11-01.md`
- **Raw:** `/workspace/frame-daily-runs/2026-11-02-competitor-raw/`
- **LLM summarize:** `pi` → `/workspace/frame-daily-runs/2026-11-02-competitors-pi-summary.md`

---

## RED items

**None.** Quiet vs 2026-11-01 on pricing and high-value new pages.

- No paid-tier / dollar pricing on tracked peers (Schema.org `Offer` price=`0` / `0.00` or free-copy; stray `$` tokens in RSC payloads are flight IDs, not plan prices).
- No >5% price change (still free).
- Legacy sitemap URL counts **unchanged** vs 11-01: frame-extractor.com 13 / framify 9 / getframes 8 / framesfromvideo 42 / extractvideoframes 14.
- Homepages: framesfromvideo + extractvideoframes **byte-identical** to 11-01; frame-extractor.com same **21495 B**, sha Δ = Cloudflare challenge token pattern (same as prior days).
- frameripper sitemap newest lastmod still **2026-10-30** (41 locs) — depth watch, not same-day RED new-page.
- toframes.video 10 locs (tool+blog matrix) already noted as SERP peer on 11-01; no new lastmod after 2026-10-08.

**SERP note (not competitor RED):** primary query still missing our `.app`; `video frame extractor` slipped **#2 → #4**; `frame extractor` improved **#5 → #3**. New SERP peer **frameextract.com** / **openclip.app**.

---

## Sitemap count vs 2026-11-01

| Competitor | 2026-11-01 | 2026-11-02 | Δ |
|---|---:|---:|---|
| frame-extractor.com | 13 | 13 | 0 |
| framify.video | 9 | 9 | 0 |
| getframesfromvideo.com | 8 | 8 | 0 |
| framesfromvideo.com | 42 | 42 | 0 |
| www.extractvideoframes.com | 14 | 14 | 0 |
| framepeel.com (watch) | ~4 | 4 | 0 |
| toframes.video (watch) | — | 10 | baseline set |
| frame-extractor.online (watch) | — | 5 (via sitemap-0.xml) | baseline set |
| frameripper.com (watch) | — | 41 | baseline set |

---

## Per-competitor (material)

### Task peers

1. **https://www.framepeel.com** — HTTP 200 (20 322 B); sitemap 4 (home/privacy/terms/licenses); free browser copy; `/pricing` 404; `/blog` 404. Still #1 on all three SERP queries.
2. **https://toframes.video** — HTTP 200 (86 414 B); sitemap 10 incl. `/last-frame-extractor/`, `/first-frame-extractor/`, `/video-to-image-sequence/`, 2 blog guides; Schema price 0; free. Watch depth.
3. **https://frame-extractor.online** — HTTP 200 (19 683 B); sitemap index → sitemap-0 with **5** locs (home, about, extract-frames-from-video, privacy, terms); Schema price 0.
4. **https://www.frameripper.com** — HTTP 200 (58 974 B); sitemap **41** (heavy tool+blog matrix; lastmod thru 2026-10-30); Schema price 0.00; `/blog` 200. SEO-depth watch (not same-day RED).
5. **https://framify.video** — HTTP 200 (71 354 B); sitemap 9; lastmod 2026-08-23; Schema price 0; byte-size unchanged vs 11-01.

### Legacy five

6. frame-extractor.com — 200 / 13 / pricing 404 / CF-token sha churn only.
7. getframesfromvideo.com — 200 / 8 / price 0 / anti-paywall copy (unchanged size 82 238).
8. framesfromvideo.com — 200 / 42 / price 0 + isAccessibleForFree / home **byte-identical**.
9. extractvideoframes.com — 200 / 14 / price 0 / home **byte-identical**.

---

## WebSearch SERP (2026-11-02)

### `extract frames from video online`
1. https://www.framepeel.com/
2. https://frameextract.com/ (**new peer**)
3. https://frame-extractor.online/
4. https://framify.video/
5. https://openclip.app/tools/extract-frames-from-video (**new peer**)

**Our site:** https://frame-extractor.app/ — **NOT in top-5** (same absence as 11-01; was #5 on 10-31).

### `video frame extractor`
1. https://www.framepeel.com/
2. https://www.frameripper.com/
3. https://frameextract.com/
4. https://frame-extractor.app/ — **our site (#4)** (was #2 on 11-01)
5. https://framify.video/extract-frames-from-video

### `frame extractor`
1. https://www.framepeel.com/
2. https://videocontextapi.com/tools/extract-frames/
3. https://frame-extractor.app/ — **our site (#3)** (was #5 on 11-01)
4. https://tools.bdwriter.org/video-frame-extractor
5. https://framify.video/extract-frames-from-video

---

## Watch / non-RED

1. FramePeel still owns all three SERP #1 slots.
2. frameextract.com + openclip.app entered primary SERP — add to watch list.
3. frameripper 41-route matrix + `video frame extractor` #2 today.
4. Our `.app`: primary still out; mid-tail #2→#4 drop; short-tail #5→#3 gain.
5. framesfromvideo.com remains depth leader among legacy (42).

## Method
- curl home + sitemap + /pricing|/plans|/price + blog/guides (~09:02–09:04 Asia/Shanghai)
- nested sitemap fetch for frame-extractor.online/sitemap-0.xml
- Schema Offer / free-copy scrape; home sha vs 11-01 raw
- WebSearch three queries; report only returned URLs
- `pi` free-llm summary (not Grok) for HTML/sitemap digest
