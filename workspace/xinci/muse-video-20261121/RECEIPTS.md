# Muse Video keyword data receipts (2026-11-21)

All times below also appear in raw files.

## Reused (not re-charged this turn)
- Prior Semrush US overview + 3x SerpApi google_light SERP (muse video / muse ai video / muse video generator)
  - Queried: 2026-11-21 04:30:07 UTC = 2026-11-21 12:30 Asia/Taipei
  - Cost then: $0.049 (4 x $0.001 Semrush overview + 3 x $0.015 SERP)
  - Raw: `raw_batch_semrush_serp_32ba1f2f.txt` (source asset 32ba1f2f9dd44cb49349e203af0e3764d5c02b63f866e3135ce85fe4a16f4120)
  - Slim copy: `reuse_semrush_serp_slim.json`
  - Parsed: `reused_raw_parsed.json`
- Prior SE Ranking KD attempt: 503, $0.00, not retried: `raw_seranking_kd_503.txt`

## New this turn
- Semrush US dedicated Keyword Difficulty (`get_semrush_keyword_difficulty`, database=us, phrase muse video;muse ai video;meta muse video)
  - Queried: 2026-11-21 12:43 Asia/Taipei (batch after Trends)
  - Cost: $0.015 (15000 micros)
  - Raw: `raw_semrush_kd_d5c77acc.txt`
- SerpApi Google Trends US, same 3 terms, 3 windows: `today 3-m`, `today 1-m`, `now 7-d`
  - Queried: 2026-11-21 04:42:59 UTC = 2026-11-21 12:42 Asia/Taipei
  - Cost: $0.045
- SerpApi google_light US SERP for `meta muse video` only
  - Same timestamp, cost $0.015
  - Combined raw: `raw_trends_serp_meta_91617fd0.txt`
  - Extracts: `raw_trends_extracted.json`, `trends_stats.json`, `raw_serp_meta_muse_video.json`

This-turn new spend: $0.075. Today AIsa before this turn: $0.22632; after: about $0.30132.

## Classification
- Input: `serp_classify_input.json`
- free-llm raw: `serp_classify_llm.json`
- Evidence-corrected: `serp_classify_corrected.json` and `serp_corrections.json`
