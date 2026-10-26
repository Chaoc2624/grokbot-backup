---
name: adsense-site-auditor
description: >-
  Audit websites for Google AdSense application readiness and ad-serving
  compliance (73 ADS-* checklist items from 睡飞/阿飞🥒 yantoumu repo). Use when
  checking whether a site can apply for AdSense, pass review, fix low-value
  content rejection, verify ownership/ads.txt/privacy, or run a pre-launch
  AdSense readiness audit. Upstream:
  https://github.com/yantoumu/adsense-site-auditor-skill and Web.Cafe
  https://new.web.cafe/topic/bej425wdjc
---

# AdSense Site Auditor（睡飞开源版 · 本地工作流）

## ⚠ Critical Redline（有排名站点 TDH / 首页零擅自改动）

**注意！注意！注意！（睡飞原帖红线，已与团队 TDH 铁律对齐）**

- 站点**已经有排名、有流量**时，修改必须极其谨慎。
- **严禁擅自**：向已有排名的首页堆未折叠大段正文、修改存量 `<title>` / `<h1>` / `<meta description>`（TDH/TDK）、或用 React 条件卸载把审核向内容从 SSR 初始 HTML 里拿掉。
- **最好在网站正式上线之前**就用本 skill 完整跑一遍 ADS-* 检查，完善后再上线 / 再提交 AdSense。
- 对已有排名站点：本 skill **只允许输出审计报告与修复建议**；任何会改首页 TDH、或向首页倾倒未折叠大段文案的落地改动，**必须先获得用户明确批准**，否则一律停手只交报告。

## Core Rule

Use Google AdSense and Google Publisher official documentation as the source of truth. This skill converts those docs into an actionable website audit, but it cannot guarantee approval.

Before a serious audit, refresh the official docs when internet access is available because AdSense policies can change. If live docs conflict with this skill, the live Google docs win.

Every audit must explicitly evaluate every checklist item in `references/adsense-requirements.md`. Do not sample, summarize, or check only likely problem areas. For each requirement ID, assign exactly one status: `Pass`, `Fail`, `Unknown`, or `N/A`. Use `N/A` only when the requirement truly does not apply to the site type or monetization mode, and state why.

## Required Reference

Read `references/adsense-requirements.md` before auditing. It contains the full checklist (73 `ADS-*` IDs), severity mapping, and source URLs.

For user-facing invocation examples and reusable prompts, read `references/usage-prompts.md` when the user asks how to use this skill, asks for prompt templates, or needs an audit request template.

Upstream sources:
- GitHub: https://github.com/yantoumu/adsense-site-auditor-skill
- Web.Cafe 原帖（阿飞🥒 / 睡飞）: https://new.web.cafe/topic/bej425wdjc
- Local Claude / cc-skill copy: `/home/box/cc-skill/adsense-site-auditor`（`~/.claude/skills/adsense-site-auditor` 软链）

## Audit Workflow

1. Identify the target (live URL/repo, pre-application / post-rejection / post-fix).
2. Gather evidence (homepage + content pages, robots/sitemap/canonical, privacy/about/contact, ad density, crawl walls).
3. Classify findings: `Blocker` / `High` / `Medium` / `Pass` / `Unknown` / `N/A`.
4. Produce report: executive decision `Ready` / `Not ready` / `Ready after fixes`, then exhaustive Pass/Fail/Unknown/N/A table covering **every** ADS-* ID.

## Completeness Gate

Before finishing, count the requirement IDs in `references/adsense-requirements.md` and compare them with the IDs in the final checklist. If any ID is missing, the audit is incomplete.
