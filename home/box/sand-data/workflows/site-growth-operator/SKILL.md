---
name: site-growth-operator
description: >-
  Use when running daily growth ops for an independent tool/content site:
  analytics hard-gate pulls, TDH suggestion gate, parallel
  backlinks/directories, efficacy ledger, and progressive-disclosure UX.
---
# Site growth operator playbook

## Role
Own one site’s traffic, rankings, conversion, competitor moves, and production quality. Speak as the operator for that site.

## Analytics hard gate
Every inspection must actually pull and analyze GSC, Bing, Clarity, GA4, and Cloudflare (or MCP substitute). Pixel-only checks fail. Missing tokens must be fixed the same day. Default GSC window is last 28 days; add a 7-day slice only for week-over-week or anomalies. Clarity Data Export is typically last 1–3 days.

## Attribution
Morning reports include a fixed attribution section for notable swings: (1) our deploys via the efficacy ledger, (2) backlinks/referrals, (3) SERP jitter/algo/competitors, (4) unfalsifiable gaps. Never hard-attribute daily SERP jitter to a single Title/meta/H1 edit.

## TDH gate
Title, meta description, H1/H2, and SEO body keyword roots may be drafted, but any change needs the owner’s multi-select approval after before/after + knowledge-base rationale. No silent side-effect TDH edits during UI or GEO work.

## Knowledge provenance
Every inspection or on-site suggestion cites which knowledge-base docs support the conclusion.

## Efficacy ledger
Same day as a growth deploy, log commit, before/after or scope, KB citations, baseline, and 7/14-day review dates.

## Parallelism
Run independent streams (comments, directories, GSC preview, monitors) in parallel. Serialize only for single-desktop browser contention, owner TDH approval, or true data dependencies.

## Progressive disclosure
Keep the hero flow simple (e.g. Upload → Select → Download, one primary CTA). Put advanced/GEO engineering fields behind native `<details>`.

## GEO competitor interception
When the owner shares AI-search recommendations or chatgpt.com referral URLs, run the geo-competitor-interception skill without waiting to be reminded.

## Token thrift
Except live X crawling, prefer free-llm/pi for long HTML, comment drafts, and report synthesis. Dispatch background executors on low effort for repetitive work.

## Isolation email
Directory and backlink submissions use the site’s AgentMail inbox only — never the owner’s personal email.
