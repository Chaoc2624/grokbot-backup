---
name: new-site-launch-bind
description: >-
  Use when launching a new site: bind domain via
  registrar→Cloudflare→Workers/Pages custom hostname, then run first-launch
  diagnostics including GSC, GA4, Cloudflare Web Analytics (RUM), Bing+IndexNow,
  Clarity, GSC Request Indexing, and a post-launch Gefei SEO Agent growth
  diagnosis + one optimization pass.
---
# new-site-launch-bind

Generic reusable recipe. Keep site-specific IDs, emails, and account names in
the calling routine or operator profile—not hard-coded here.

## Inputs (require before acting)

Collect or confirm:

| Input | Example shape |
| --- | --- |
| `domain` | `example.com` (apex) |
| `registrar` | Spaceship / Namecheap / Porkbun / Cloudflare / other |
| `cf_account` | Which Cloudflare account / API token scope (assumption: already authenticated CLI or dashboard session) |
| `project_kind` | `workers` or `pages` |
| `project_name` | CF project name (and optional existing `*.workers.dev` URL) |
| `repo` | Local absolute path and/or remote git URL |
| `analytics_google_account` | Which Google login owns GSC + GA4 |
| `secrets_dir` | Private dir for Measurement IDs / Clarity ID / IndexNow key / CF RUM token (never commit secrets; inject via env or settings) |

Optional: brand display name, AgentMail submit inbox for later directory signup, whether AdSense preflight (`adsense-site-auditor`) runs the same day.

## Preconditions

1. Read the site’s operator profile / vault pointers if any.
2. Confirm production HTML is already deployable from `repo` (do not hang a formal apex on an unfinished shell—see 增长知识库 note on incomplete sites).
3. Prefer Cloudflare API / Wrangler / signed-in dashboard; use `sign-in` / `vault` skills before any password or OTP page.
4. For long HTML or report drafting, prefer free-llm / low executor (operator iron rule)—not required for pure DNS/UI binding clicks.

## Steps

### 1. Cloudflare zone + nameserver handoff

1. Create a Cloudflare zone for `domain` (or reuse if it already exists). Record `zone_id` and the two assigned Cloudflare nameservers.
2. At `registrar`, replace registrar NS with the Cloudflare NS pair only (no partial mix).
3. Poll until zone `status` is `active`. Do not proceed to custom hostname SSL expectations while pending.
4. Baseline DNS: ensure no conflicting A/AAAA/CNAME that fights the upcoming Workers/Pages route (remove parking/placeholder targets).

### 2. Workers or Pages custom hostname

1. Open the named `project_name` under the assumed CF account.
2. Attach custom domain / custom hostname for apex and `www` (choose one canonical; redirect the other).
3. Wait for certificate + hostname status ready.
4. Success check: `curl -sI https://<domain>/` returns **200** (or expected app status) and body matches the Worker/Pages app—not registrar parking.
5. Keep `*.workers.dev` (or Pages preview) as staging if useful; lock production `APP_URL` / canonical env to `https://<domain>`.

### 3. Cloudflare crawl / bot defaults (launch hygiene)

On the new zone, set (unless the user explicitly wants stricter bot fight):

- Bot Fight Mode / fight_mode → **off**
- AI bots protection → **disabled** (or equivalent “do not block AI crawlers”)
- Managed robots.txt → **off** (repo owns `robots.txt`)

Verify with real UAs that home returns **HTTP 200** for Googlebot, bingbot, GPTBot / OAI-SearchBot, ClaudeBot, PerplexityBot. Also ensure `Accept: text/markdown` does not 500.

### 4. First-launch analytics diagnostics (required five-pack + RUM)

Treat this block as **建站首次上线诊断** — do not mark launch-bind done until every checkbox passes.

#### 4a. Google Search Console (domain property)

1. Add property `sc-domain:<domain>` under the given Google account.
2. Verify via DNS TXT on the Cloudflare zone (preferred for domain property).
3. Also inject the same verification token into site HTML/`googleVerification` (or equivalent settings key) when the template supports it—tools like Gefei Agent still flag an empty meta even when the domain property is already DNS-verified.
4. Submit `https://<domain>/sitemap.xml`.
5. Spot-check URL Inspection → live test → indexable + 200 (Request Indexing itself is step **4f**, after the rest of the five-pack).
6. Save pull notes/screenshots later under a site artifact dir (pattern: `/workspace/gsc-<slug>/`).

#### 4b. Google Analytics 4

1. Create GA4 property + web data stream for `https://<domain>`.
2. Store Measurement ID in `secrets_dir`; inject into site settings / CF env / D1 config / deploy script (whatever the repo already uses).
3. Deploy; confirm Realtime shows a human hit (`bot=0` if filtered).

#### 4c. Cloudflare Web Analytics (RUM) — required, not optional

1. Create a Web Analytics site for the zone: `POST /accounts/{account_id}/rum/site_info` with `{ zone_tag, auto_install: true }`.
2. Toggle zone RUM on: `PATCH /zones/{zone_id}/settings/rum` with `{ "value": "on" }`.
3. Record `site_tag` + `site_token` in `secrets_dir`.
4. **Workers / Worker HTML:** edge `auto_install` often does **not** rewrite Worker responses. Always also inject the beacon in app HTML (settings key such as `cloudflare_web_analytics_token` → `<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token":"…"}'></script>`).
5. **Pages / orange-cloud origin HTML:** auto_install may suffice; still curl-verify `beacon.min.js` / `cloudflareinsights` in production HTML. If missing, inject the same snippet.
6. Success: live homepage HTML contains the beacon token; CF Web Analytics dashboard can receive traffic.

#### 4d. Bing Webmaster Tools + IndexNow

1. Add the site in Bing Webmaster (GSC import is fine when available).
2. Generate an IndexNow key; publish `https://<domain>/<key>.txt` from the repo/public root (body = key).
3. Wire deploy/CI or server hook to push sitemap URLs to IndexNow on publish.
4. Clear High alerts such as “Set up IndexNow” / limited crawl capacity.
5. Expect Bing performance reports to lag up to ~48 hours after verification.

#### 4e. Microsoft Clarity

1. Create a Clarity project for the domain; obtain real project ID.
2. Inject ID into production config (never leave an empty `clarity_id` while a provider component is mounted).
3. Deploy; confirm Clarity script present in production HTML and recordings can arrive.

#### 4f. GSC homepage Request Indexing — required right after the five-pack

**When:** immediately after **4a–4e** are all green (GSC verified + sitemap submitted, GA4 live, RUM beacon live, Bing+IndexNow live, Clarity live). Do not wait for the next day.

**Why:** new sites get crawled faster when an operator manually uses GSC **网址检查 → 请求编入索引 / Request indexing** on the canonical homepage; sitemap alone is slower.

**How (UI — no public API for general URL Request Indexing):**

1. Open GSC for `sc-domain:<domain>` → URL Inspection for canonical `https://<domain>/`.
2. If needed, run **测试线上网址 / Live test** and confirm HTTP 200 + indexable (no accidental `noindex`).
3. Click **请求编入索引 / Request indexing**; wait until the UI confirms the request was accepted / queued.
4. Same day (quota permitting): also request indexing for primary money / language home pages.
5. Save a screenshot under `/workspace/gsc-<slug>/` (e.g. `request-indexing-home.png`).
6. Do **not** spam re-requests; respect GSC daily quota. One accepted request per URL is enough for launch day.
7. If live test reports robots/noindex/soft-404, **fix that first**, then re-request—do not burn quota on a known-blocked URL.

### 5. Inject, commit, deploy

1. Update repo config/env templates with production domain + analytics IDs (secrets via env/D1, not plaintext git when avoidable).
2. Grep build output / live HTML for: `localhost`, `127.0.0.1`, template brand tokens (`ShipAny`, `YourAppName`, `example.com`, `lorem`).
3. Deploy via the project’s normal path (Wrangler / Pages / `deploy.sh`).
4. Re-fetch live homepage; confirm **GA4 + Cloudflare RUM beacon + Clarity** tags fire; sitemap and IndexNow key URLs publicly reachable.
5. If deploy happened after an earlier Request Indexing attempt, re-run **4f** once on the final production homepage.

### 6. Optional same-day companions

- Run `claude-seo-audit` three-pack: `parse_html`, `agentic_check`, `drift_baseline`.
- Run `adsense-site-auditor` if monetization or “low-value” risk matters.
- Do **not** silently change TDH/SEO roots; follow vault + boss approval rules.

### 7. Gefei SEO Agent first-launch growth diagnosis → one optimization pass (required)

**When:** after steps **4–5** are green (five-pack live, production HTML clean, sitemap public). Prefer the same launch day.

**Why:** bind/analytics only prove the pipes work. Gefei Agent re-crawls the live homepage (and key language homes) for growth gaps—thin copy, slogan H1s without keywords, cannibalizing Titles, empty nav/footer, missing schema—then the operator runs **one** prioritized fix pass.

**How to call Gefei (in order of preference):**

1. **Chat UI (default when the browser helper plugin is down):** open `https://seo.web.cafe/chat/` (signed-in Web.Cafe account). Ask for a **新站首轮增长诊断**, paste the canonical homepage URL (`https://<domain>/`), and tell it to use **服务器抓取 / server-side crawl** (not the browser plugin) so the report is fresh from production. Also paste primary language homes when the site is i18n (e.g. `/de/`, `/es/`, `/fr/`).
2. **Tool APIs** (when `WEBCAFE_TOKEN` / MCP is available): at minimum run `onpage_Audit` + `page_Advisor` on the homepage; add `adsense_Check` if monetization matters. Prefer assembled tools over raw scrapes. See vault note `增长知识库/07-工具/02-AI工具/哥飞AI与SEO-Agent工具箱及API调用指南.md`.
3. Save the full diagnosis (markdown or export) under `/workspace/gsc-<slug>/` or the site’s ops artifact dir, tagged with the date.

**Prompt shape (keep generic; fill URLs at call time):**

> 新站刚完成五合一统计与上线绑定。请用服务器抓取（不要依赖浏览器插件）诊断 `https://<domain>/`，并核对主要语言首页。输出：技术层是否可抓取/可收录；内容与 TDH 短板；内链/页脚/导航；多语言互相抢词；按 P0/P1/P2 给可执行改动清单。

**After the report returns — one optimization loop:**

1. Triage into P0 (same day) / P1 (this week) / P2 (later). Typical P0: GSC HTML verification token if still empty, homepage body length, H1 keyword embedding, broken/empty legal footer.
2. **TDH / H1 / SEO keyword-root edits:** consult `@增长大师` + 增长知识库 first; get explicit boss confirmation before changing titles/H1s on any page that already has impressions (TDH zero-token-loss iron rule). Brand-new launch pages with zero GSC history still follow the consult path when the change is strategic keyword positioning.
3. Execute the approved P0 (and agreed P1) in repo → deploy → re-curl live checks.
4. Re-run Gefei only on the pages you changed **or** re-request GSC indexing for those URLs—do not open an endless diagnosis loop the same day.
5. Hand P2 (schema, admin-chunk preload cleanup, new locales, paid links) to the backlog / `@Geo主理人` / `@架构总工` as appropriate; do not block launch-bind exit on P2.

**Do not** treat Gefei’s “GSC 验证为空” as failure if `sc-domain:` is already DNS-verified **and** sitemap is submitted—but still inject the HTML `google-site-verification` meta when the template exposes `googleVerification`, because third-party auditors look for it.

## Success checks (exit criteria)

All must pass before declaring launch-bind done:

- [ ] CF zone **active**; registrar NS = Cloudflare NS
- [ ] `https://<domain>/` serves the intended Workers/Pages app
- [ ] GSC domain property **verified**; sitemap submitted; HTML verification meta present when template supports it
- [ ] **After five-pack: homepage GSC Request Indexing accepted** (or blocked only after a documented fix-then-retry plan)
- [ ] GA4 Measurement ID live; realtime shows traffic
- [ ] **Cloudflare Web Analytics (RUM) site created; zone RUM on; production HTML contains `beacon.min.js` + site token**
- [ ] Bing site added; IndexNow key URL returns the key; no IndexNow High alert
- [ ] Clarity ID non-empty and script loads on production
- [ ] Production HTML: zero localhost / zero known template residue
- [ ] AI/search bot UAs get HTTP 200 on homepage
- [ ] **Gefei SEO Agent first-launch diagnosis saved; P0 items from that report executed or explicitly queued with owner + date**
- [ ] IDs recorded in `secrets_dir` + operator profile dossier updated (domain, project, GSC property, RUM token, inject locations)

## Failure / stop conditions

- Registrar login or Cloudflare 2FA blocked → stop and ask user; do not scrape tokens.
- Zone stuck pending NS → fix registrar NS before analytics DNS verification deadlines.
- App still template/incomplete → prefer workers.dev staging; delay apex per vault SOP.
- User forbids production deploy → bind DNS/docs only; leave inject as a drafted PR.
- GSC Request Indexing quota exhausted → note date + retry next day; do not mark launch-bind fully done until homepage request succeeds once.
- Gefei / Web.Cafe auth or credits blocked → save the intended prompt + URLs, ask user to unlock, and keep technical five-pack exit separate from the growth-diagnosis checkbox.

## References (local vault, not remote fetches)

- `增长知识库/01-SEO基础与SOP/新站上线与周期巡检三合一SOP（五合一统计+零模板残留+外链反作弊）.md`
- `增长知识库/01-SEO基础与SOP/01-上线SOP/哥飞的快速上站SOP(手动版).md` (模块一～三)
- `增长知识库/07-工具/02-AI工具/哥飞AI与SEO-Agent工具箱及API调用指南.md`
