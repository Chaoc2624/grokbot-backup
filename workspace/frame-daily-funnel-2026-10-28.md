# [日报] Funnel Inspector — `https://frame-extractor.app`

- **生成时间**: 2026-10-28T09:00:47.883378+08:00（box clock = Asia/Shanghai (UTC+8)）
- **URL**: https://frame-extractor.app
- **总评**: **WARN**
- **Flags**: 1

## Flags（仅异常）

- 🔴 `L1_drift_compare_WARN rc=2 err=usage: drift_compare.py [-h] [--skip-cwv] [--baseline-id BASELINE_ID] url
drift_compare.py: error: unrecognized arguments: --json
`

## Layers

### ✅ `L1_http`
- sitemap URL count: **43**
- ✅ `homepage` → HTTP 200 (170ms)
- ✅ `llms_txt` → HTTP 200 (178ms)
- ✅ `robots_txt` → HTTP 200 (219ms)
- ✅ `sitemap_xml` → HTTP 200 (198ms)

### ✅ `L1_claude_seo`
- ⚠ L1_drift_compare_WARN rc=2 err=usage: drift_compare.py [-h] [--skip-cwv] [--baseline-id BASELINE_ID] url
drift_compare.py: error: unrecognized arguments: --json


### ✅ `L1.5_indexnow`

### ✅ `L1.8_backlinks`

### ✅ `L2_L4_api_hooks`

### ✅ `L4.5_efficacy_ledger`
- rows parsed: 13
- due 7d: 0
- due 14d: 0

## V2 五步升级检查

- `1_api_free_llm_inspector`: True
- `2_l25_intent_velocity_fingerprint`: frontend: require architecture agent
- `3_l35_video_decode_error`: frontend: require architecture agent
- `4_l45_sample_video_share_hook`: frontend: require architecture agent
- `5_efficacy_ledger_7d_14d`: True

chitecture agent
- `5_efficacy_ledger_7d_14d`: True


## free-llm 异常摘要

(none)

## vs baseline / anomalies

- GSC/GA4/Clarity/CF GraphQL: **auth blockers** — no live metrics; cannot compute >20% click/impression deltas vs 2026-10-26 baseline (GSC 28d: 71/1892/3.8%/pos11.6; Bing 3m: 297/7157/4.15%; CF RUM Sep: 760 visits). GSC cache under `/workspace/gsc-frame-extractor` is still Oct 26 screenshots (+ Bing Oct 27).
- Funnel overall: **WARN** (same class as 2026-10-27) — `L1_drift_compare_WARN` (`drift_compare.py` rejects `--json`).
- L1 HTTP: PASS — homepage/llms/robots/sitemap 200; sitemap **43** URLs (flat vs yesterday).
- L1.5 IndexNow: PASS (`e9b5cbe548134dd38e985f7a354589ee`).
- L1.8 backlinks: PASS (ledger live≈84, pending≈166).
- L2–L4 API hooks: skipped — missing `CLOUDFLARE_API_TOKEN`+`ZONE_ID`, `CLARITY_API_TOKEN`, `GOOGLE_APPLICATION_CREDENTIALS` / GA4 property.
- L4.5 efficacy ledger: **no** +7d/+14d due today; next windows **2026-11-02** / **2026-11-09** (all Oct 26 ship rows still 观察中).
- No assertable metric anomaly >20% without authenticated pulls.
