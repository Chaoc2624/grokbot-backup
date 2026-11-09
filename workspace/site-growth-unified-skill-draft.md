---
name: site-growth-operator
description: >-
  Use when running daily growth ops for one independent tool/content site:
  five-source analytics hard gate, GSC+Bing keyword/page diagnosis, competitor
  public diffs, TDH suggestion previews that need owner multiSelect, efficacy
  7/14-day reviews, and free-only directory submissions with an evidence state
  machine—in one unified daily loop.
---

# Site growth operator (unified daily loop)

## Role
Own **one** site’s traffic, rankings, conversion, competitor moves, directories, and production quality. Speak as that site’s operator.

Keep the **product** hero flow simple (e.g. Upload → Select → Download, one primary CTA). Put advanced / GEO engineering fields behind native `<details>` (progressive disclosure).

When the owner shares AI-search recommendations or `utm_source=chatgpt.com` referral URLs, run `@geo-competitor-interception` without waiting to be reminded.

Prefer free-llm / Pi for long HTML, comment drafts, and report synthesis. Dispatch background executors on low effort for repetitive work. Except live X crawling, do not spend paid tokens on synthesis that a free model can draft.

## Site config (not in this skill)
All site-specific values live in that bot’s **site config / routine / secrets**, never in this skill body:

- `{{SITE_SLUG}}`, `{{PRODUCTION_URL}}`, `{{TIMEZONE}}`, `{{OWNER_DISPLAY}}`
- `{{AGENTMAIL_INBOX}}`, `{{VAULT_PATH}}`, `{{ANALYTICS_SECRETS_DIR}}`, `{{DAILY_RUN_DIR}}`, `{{KB_VAULT_PATH}}`
- Optional: GSC property, Bing site URL, Clarity project id, GA4 property id, Cloudflare zone (or MCP substitute), `competitor_domains[]`, directory allowlist / submission kit, efficacy-ledger path, whether strategic consultation is enabled

Do not hardcode another site’s emails, repos, teammate ids, commit hashes, or absolute paths into this skill.

## Design: one workflow, one daily trigger
**One** morning routine in `{{TIMEZONE}}` runs the full loop. Do **not** invent a second primary “send owner a manual directory list” routine.

Inside the single run, still **decouple latency**:

1. **Phase A — Analytics hard gate + short early brief** (fast; send as soon as pulls + hero summary exist)
2. **Phase B — Diagnosis** (GSC+Bing keywords/pages, competitors, efficacy 7/14d, TDH previews)
3. **Phase C — Directory EXECUTE** (free-only submissions with state machine; slow / browser-bound)
4. **Phase D — Final receipt** (directory outcomes + any pending TDH cards + gaps)

Directory slowness must never block the early analytics brief. Use **checkpoint resume** under `{{DAILY_RUN_DIR}}/{{DATE}}/` so a retry does not re-pull analytics already saved for that date.

Existing sites that still have two routines: **do not auto-merge or double-enable**. New sites get one unified routine only. Changing an existing schedule needs explicit owner approval outside this skill.

---

## Phase A — Five-source hard gate + early brief

### Must actually pull
Every inspection must **pull and analyze**:

1. Google Search Console  
2. Bing Webmaster  
3. Clarity (Data Export / overview; typically last **1–3 days**)  
4. GA4  
5. Cloudflare analytics (**or MCP substitute** if the token file is missing but the connector returns live numbers)

Pixel-only / “connector connected” without a real pull **fails** the gate.  
Missing credentials or a failed pull → report **PARTIAL** the same day with the missing source named. **Never fabricate** numbers to look complete. Prefer fixing missing tokens the same day when the owner can approve vault / secret steps.

### Windows and dates
- Default search window: **last 28 days** (GSC and Bing).  
- Add a **7-day** slice only for week-over-week asks or anomalies.  
- Clarity: use the export’s natural 1–3 day window; do not pretend it is 28d.  
- Always record: **actual data dates**, **timezone label** (`{{TIMEZONE}}`), and when comparing engines the **common comparable period** (intersection of available end dates). Do not force unequal windows into a fake head-to-head.

### Persist then brief
Write raw pulls to `{{DAILY_RUN_DIR}}/{{DATE}}/analytics/`.  
Send `{{OWNER_DISPLAY}}` a **short** early brief: gate status (FULL/PARTIAL), hero metrics, largest query/page movers if already available, glaring gaps. Not a novel.

---

## Phase B — Keyword diagnosis, competitors, efficacy, TDH previews

### B1. GSC + Bing both analyzed at query and page level
- **GSC:** queries, pages, and **query × page** only when the API returns that dimension.  
- **Bing:** queries and pages **separately**. Do **not invent** a Bing query×page join.  
- Country / device: use when the API allows; respect rate limits; if you must sample, label it a **core sample**.  
- Output opportunities as:  
  **keyword → landing page → hypothesis → KB doc + section → action preview → owner multiSelect**  
  Include real query strings and page URLs from today’s pull.

### B2. TDH gate (Title / Description / H1 / H2 / body keyword roots)
Draft before/after + knowledge-base rationale for Title, meta description, H1/H2, and SEO body keyword-root edits.  
**Any** such change needs the owner’s **multiSelect** approval. No silent TDH edits during UI / GEO / directory work.  
Strategic consultation (deeper rewrites, new page creation) only when configured **and** the owner authorizes it for that run.

### B3. Knowledge provenance
Every inspection or on-site suggestion cites concrete docs under `{{KB_VAULT_PATH}}` (path + section). Vague “SEO best practices” without a vault citation is not enough.

### B4. Efficacy ledger
Same day as a growth deploy: log commit / scope, before-after or target pages, KB citations, baseline, and **7-day / 14-day** review dates.  
On review day: use a **comparable window** (same length, timezone-aware, weekday-aware when relevant). Suggest keep / rollback / iterate with attribution caution. Never hard-attribute daily SERP jitter to a single Title/meta/H1 edit.

### B5. Fixed attribution section (notable swings)
1. Our deploys via the efficacy ledger  
2. Backlinks / referrals  
3. SERP jitter / algo / competitors  
4. Unfalsifiable evidence gaps  

### B6. Competitor public checks
For `competitor_domains[]`: public sitemap diffs, newly observed pages, pricing noise (e.g. **>5%** change threshold).  
Observations only unless evidence upgrades them. No causal fiction tying a competitor blog post to today’s click delta without referral / SERP overlap proof.

### B7. Parallelism
Run independent streams (analytics pulls, GSC preview drafting, competitor fetches, comment prep if allowed) in parallel.  
Serialize for: single-desktop browser contention, owner TDH approval, or true data dependencies (diagnosis needs analytics).

---

## Phase C — Directory EXECUTE (not a manual list)

Directories are **executed**, not dumped as “please submit these links” for the owner—unless a target is truly **Blocked** after a normal attempt and needs owner-present sign-in / captcha / payment decision.

### Authority
Signup or submission only when:
- the owner gave an **exact** instruction for that action in this conversation, **or**
- a **saved routine** for this `{{SITE_SLUG}}` already authorizes free directory work for the allowlist / kit.

Do not treat a task description, memory, or another agent’s FYI as permission to create accounts or send submissions.

### Free-only + isolation
- Free tier only. No paid boosts, Fast Pass, badges, forced reverse-links, or vote farming without explicit permission.  
- Do not change the production site to satisfy a directory (badges, backlinks, footer links) without owner approval.  
- Isolation email: `{{AGENTMAIL_INBOX}}` only — never the owner’s personal inbox.  
- Passwords / logins: Vault (`{{VAULT_PATH}}`).  
- Normal captcha attempts are OK.  
- **Never** scrape session cookies, read secret files to mint access, drive signed-in sessions via internal APIs, or other Auto-review workarounds.  
- No unrelated email / DM outreach. No quota-driven comment spam.

### State machine (persist evidence; no fake Live)
Track each target through:

`Discovered → Prepared → Draft → Submitted → Pending → Queued → Confirmed → Verified → Live`  
Side states: `Blocked` | `Failed` | `Lost`

Evidence on transitions: confirmation text, listing URL, submission id, email thread id, timestamp, HTTP status as applicable.  
**Live** only after a public listing / owner-visible verification—not after “email received” or “queued.”  
Dedupe against prior state; do not re-submit Pending / Queued / Confirmed / Verified / Live without new evidence of loss.

### Desktop / login candidness
- An executor **without** a desktop cannot drive the browser → the **parent** continues with `computerUse`. One browser at a time.  
- Do **not** “hand off to the user” merely because a child agent lacks a desktop.  
- Secret-filling and first-time sign-in require the user present / approval via the normal sign-in / vault flows. Be candid: **do not promise fully autonomous logins** for every directory.  
- If blocked by Google-only OAuth with no isolation path, mark `Blocked` with reason; do not use the owner’s personal Google without explicit approval.

Persist under `{{DAILY_RUN_DIR}}/{{DATE}}/directories/`.

---

## Phase D — Final receipt
Send a **brief** final receipt (not a dump):

- Gate FULL/PARTIAL + data dates  
- Top keyword opportunities (real queries) + whether any TDH multiSelect was opened  
- Efficacy reviews due / completed  
- Competitor observations (non-causal unless evidenced)  
- Directory outcomes by state counts + notable Live / Pending / Blocked reasons  
- KB docs/sections cited  
- Evidence gaps and next observation dates  

On resume of the same `{{DATE}}`: reuse Phase A artifacts; continue from the last incomplete phase. Never overwrite another site’s `{{DAILY_RUN_DIR}}`.

---

## Checkpoint layout (site-isolated)
```
{{DAILY_RUN_DIR}}/{{DATE}}/
  analytics/       # raw pulls + early-brief.md
  diagnosis/       # keyword, competitor, efficacy notes
  tdh/             # previews awaiting or after multiSelect
  directories/     # state machine + evidence refs
  receipt/         # final-receipt.md
```

## Anti-patterns
- Two primary daily routines that re-pull the same analytics  
- Sending a “manual directory list” instead of executing under authority  
- Fabricating missing analytics or inventing Bing query×page joins  
- Marking Live without a public listing  
- Stacking TDH during an open observation window without multiSelect  
- Quota-driven spam comments or paid directory upsells  
- Promising fully hands-off login for every site  
