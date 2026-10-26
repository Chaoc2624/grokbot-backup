---
name: claude-seo-audit
description: >-
  When auditing a website or page for technical SEO, GEO (AI search citation /
  llms.txt / WebMCP), E-E-A-T content quality, Schema.org, hreflang i18n, or
  pre/post-deploy SEO drift regression using the local claude-seo v2.5.0 toolkit
  (/workspace/claude-seo).
---
# Claude SEO & GEO Full-Stack Audit (`AgriciDaniel/claude-seo` v2.5.0)

Use this skill to run deterministic technical SEO, E-E-A-T content quality, Schema.org, hreflang/i18n, GEO (Generative Engine Optimization / AI citation readiness), Lighthouse Agentic Browsing (`llms.txt`, WebMCP), and SEO Drift baseline/regression checks on any URL.

## Installed Runtime on Cloud Computer
- **Repository Root**: `/workspace/claude-seo` (v2.5.0, Python 3.13 `.venv` + Playwright Chromium headless browser pre-installed)
- **CLI Launcher**: `/workspace/claude-seo/scripts/claude-seo` (also wrapped at `~/.local/bin/claude-seo`)
- **Sub-skills (`26`)**: `/workspace/claude-seo/skills/seo-*/SKILL.md`
- **Sub-agents (`19`)**: `/workspace/claude-seo/agents/seo-*.md`
- **Multi-platform instructions**: `/workspace/claude-seo/AGENTS.md` (compatible with Grok Bot, OpenAI Codex CLI, Claude Code, Pi CLI / DeepSeek / OpenRouter models, and Cursor)

## Core Execution Commands (Run via Shell)

### 1. Health Check
```bash
/workspace/claude-seo/scripts/claude-seo doctor
```

### 2. Technical HTML & On-Page Audit
```bash
# Fetch and parse title, meta, headings, canonicals, hreflang, links, images, and JSON-LD schema
/workspace/claude-seo/scripts/claude-seo run fetch_page.py https://example.com --output /tmp/page.html
/workspace/claude-seo/scripts/claude-seo run parse_html.py /tmp/page.html --url https://example.com --json

# Headless Chromium SPA render & DOM comparison (detects SSR vs CSR hydration gaps)
/workspace/claude-seo/scripts/claude-seo run render_page.py https://example.com --json
```

### 3. GEO / AI Search & Agentic Readiness (`llms.txt`, WebMCP, AI Crawlers)
```bash
/workspace/claude-seo/scripts/claude-seo run agentic_check.py https://example.com --json
/workspace/claude-seo/scripts/claude-seo run agent_ux_check.py https://example.com --json
/workspace/claude-seo/scripts/claude-seo run lighthouse_agentic.py https://example.com --json
```

### 4. Content Quality (E-E-A-T) & Humanize Check
```bash
/workspace/claude-seo/scripts/claude-seo run content_quality.py /tmp/page.html --url https://example.com --json
/workspace/claude-seo/scripts/claude-seo run content_verify.py https://example.com --json
```

### 5. SEO Drift Monitoring (Pre/Post Deployment Regression Guard)
Run `drift_baseline.py` before deploying a site change, and `drift_compare.py` after deployment to verify zero unintended regressions in `<title>`, `<h1>`, canonicals, meta robots, or JSON-LD:
```bash
/workspace/claude-seo/scripts/claude-seo run drift_baseline.py https://example.com
/workspace/claude-seo/scripts/claude-seo run drift_compare.py https://example.com
```

### 6. Reading Sub-Skill Checklists & Rubrics
When performing a specialized audit, read the corresponding sub-skill instructions under `/workspace/claude-seo/skills/`:
- Full audit rubric & weights: `/workspace/claude-seo/skills/seo-audit/SKILL.md`
- Technical SEO (9 categories): `/workspace/claude-seo/skills/seo-technical/SKILL.md`
- GEO / AI Overviews / ChatGPT / Perplexity citation: `/workspace/claude-seo/skills/seo-geo/SKILL.md`
- Agentic readiness & WebMCP: `/workspace/claude-seo/skills/seo-agentic/SKILL.md`
- International SEO & machine-translation QA: `/workspace/claude-seo/skills/seo-hreflang/SKILL.md`
- Schema validation & 2024–2026 deprecated types: `/workspace/claude-seo/skills/seo-schema/SKILL.md`
- Programmatic SEO guardrails: `/workspace/claude-seo/skills/seo-programmatic/SKILL.md`
