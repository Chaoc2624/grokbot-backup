# Frame daily health — 2026-10-28

- **Date:** 2026-10-28 Asia/Shanghai (UTC+8)
- **Window:** ~08:57–09:00
- **Target:** https://frame-extractor.app
- **Verdict:** **OK** (core surface green; known locale gaps only)

---

## Summary

| Check | Result |
|---|---|
| Homepage | **200** (~102 713 B, ~0.99s) |
| Locales ja/de/fr/it/es | **200** |
| Locales pl / nl-NL / zh-hant (hreflang extras) | **200** |
| Locale /ko | **301 → /** (not a dedicated KO landing) |
| Locales /pt /zh /ru | **404** (not in sitemap; known) |
| 11 tool landers | **all 200** |
| /terms-of-service /privacy-policy | **200** |
| /sitemap.xml | **200** — **43** `<loc>` (unchanged vs 10-27) |
| /llms.txt /llms-full.txt | **200** (4 562 / 10 755 B) |
| IndexNow key `e9b5cbe548134dd38e985f7a354589ee.txt` | **200** (body = key, 32 B) |
| Placeholders `localhost:3000` / `ShipAny` / `YourAppName` | **0 / 0 / 0** |
| GA4 `G-7J7WCQ7V35` | **present** (config payload) |
| Clarity `z3ok33tl46` | **present** (script + config) |
| CF Web Analytics beacon (`cloudflareinsights` / `data-cf-beacon`) | **not in HTML** (site still served via Cloudflare `cf-ray`; RUM may be dashboard-only) |
| `data-testid=ssr-workbench-controls` | **present** |
| `try-sample-video-btn` | **present** |
| `Accept: text/markdown` | **200** (CT still `text/html`; Vary Accept noted by claude-seo; `/index.md` 404) |

---

## HTTP matrix

### Locales
| Path | Status |
|---|---|
| `/` | 200 |
| `/ja` | 200 |
| `/de` | 200 |
| `/fr` | 200 |
| `/it` | 200 |
| `/es` | 200 |
| `/pl` | 200 |
| `/nl-NL` | 200 |
| `/zh-hant` | 200 |
| `/ko` | **301 → /** |
| `/pt` | **404** |
| `/zh` | **404** |
| `/ru` | **404** |

### Tools (all 200)
`/mp4-frame-extractor` `/mov-frame-extractor` `/video-to-jpg` `/video-to-png` `/extract-frames-from-video-every-second` `/4k-video-frame-extractor` `/video-contact-sheet` `/frame-by-frame-video-viewer` `/video-screenshot` `/first-last-frame-extractor` `/ai-video-frame-extractor`

### Legal / meta
| Path | Status | Notes |
|---|---|---|
| `/terms-of-service` | 200 | |
| `/privacy-policy` | 200 | |
| `/sitemap.xml` | 200 | 43 URLs, 37 388 B |
| `/llms.txt` | 200 | 4 562 B |
| `/llms-full.txt` | 200 | 10 755 B |
| `/e9b5cbe548134dd38e985f7a354589ee.txt` | 200 | IndexNow |

---

## WARN / notes (non-blocking)

1. `/pt` `/zh` `/ru` 404 — expected, not in sitemap (same as 10-27).
2. `/ko` 301→`/` — KO not a real locale shell; hreflang list does not advertise `/ko`.
3. CF Web Analytics JS beacon absent from raw HTML — edge is Cloudflare; cannot confirm RUM injection from curl alone.
4. Markdown content negotiation returns HTML body (status 200 OK per checklist); no `/index.md` sibling.

## FAIL items

**None.**

## Artifacts

- Raw homepage + sitemap: `/workspace/tmp-health-2026-10-28/`
- This report: `/workspace/frame-daily-health-2026-10-28.md`
