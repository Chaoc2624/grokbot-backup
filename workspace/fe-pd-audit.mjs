import { chromium } from 'playwright';
import fs from 'fs';

const BASE = process.env.PD_BASE || 'https://frame-extractor.app';
const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'mobile', width: 390, height: 844 },
];
const DRAWER_TESTIDS = [
  'ssr-workbench-controls',
  'micro-filmstrip-loupe',
  'engineering-verification-table',
  'codec-compat-matrix',
];
const GEO_TERMS = [
  'requestVideoFrameCallback',
  'metadata.mediaTime',
  'metadata.presentedFrames',
  'Laplacian',
  'SHA-256',
  'framemd5',
  'showinfo',
  'ffprobe',
  'WebCodecs',
  'SMPTE',
];

function parseAlpha(bg) {
  if (!bg || bg === 'transparent') return 0;
  const rgba = bg.match(/rgba?\(([^)]+)\)/);
  if (!rgba) return 0;
  const parts = rgba[1].split(',').map((s) => s.trim());
  if (parts.length === 4) return parseFloat(parts[3]);
  return 1;
}

async function measure(page, state) {
  return page.evaluate(({ drawerTestIds, state }) => {
    const docEl = document.documentElement;
    const horizontalOverflow = Math.max(0, docEl.scrollWidth - docEl.clientWidth);

    const header =
      document.querySelector('header') ||
      document.querySelector('[data-testid="site-header"]') ||
      document.querySelector('nav')?.closest('header,div');
    let stickyHeaderOpaque = false;
    if (header) {
      const cs = getComputedStyle(header);
      const bg = cs.backgroundColor;
      let a = 0;
      const m = bg.match(/rgba?\(([^)]+)\)/);
      if (m) {
        const p = m[1].split(',').map((s) => s.trim());
        a = p.length === 4 ? parseFloat(p[3]) : 1;
      }
      stickyHeaderOpaque = a >= 0.85 || cs.backdropFilter.includes('blur') || cs.webkitBackdropFilter?.includes('blur');
    }

    // Nested cards: bordered rounded surface inside another bordered rounded surface
    const isCardish = (el) => {
      if (!el || el === document.body || el === document.documentElement) return false;
      const cs = getComputedStyle(el);
      const bw =
        (parseFloat(cs.borderTopWidth) || 0) +
        (parseFloat(cs.borderRightWidth) || 0) +
        (parseFloat(cs.borderBottomWidth) || 0) +
        (parseFloat(cs.borderLeftWidth) || 0);
      const radius = Math.max(
        parseFloat(cs.borderTopLeftRadius) || 0,
        parseFloat(cs.borderTopRightRadius) || 0,
        parseFloat(cs.borderBottomLeftRadius) || 0,
        parseFloat(cs.borderBottomRightRadius) || 0
      );
      const bg = cs.backgroundColor;
      let alpha = 0;
      const mm = bg.match(/rgba?\(([^)]+)\)/);
      if (mm) {
        const p = mm[1].split(',').map((s) => s.trim());
        alpha = p.length === 4 ? parseFloat(p[3]) : 1;
      }
      return bw >= 3.5 && radius >= 8 && alpha > 0.05;
    };

    const nestedCards = [];
    const all = [...document.querySelectorAll('details, section, div, article')];
    for (const el of all) {
      if (!isCardish(el)) continue;
      let p = el.parentElement;
      while (p && p !== document.body) {
        if (isCardish(p)) {
          nestedCards.push({
            child: `${el.tagName}.${String(el.className || '').slice(0, 80)}`,
            parent: `${p.tagName}.${String(p.className || '').slice(0, 80)}`,
            testid: el.getAttribute('data-testid') || p.getAttribute('data-testid') || null,
          });
          break;
        }
        p = p.parentElement;
      }
    }

    const drawers = drawerTestIds.map((id) => {
      const el = document.querySelector(`[data-testid="${id}"]`);
      if (!el) return { id, present: false };
      const summary = el.querySelector(':scope > summary');
      const rect = summary ? summary.getBoundingClientRect() : null;
      const open = el.hasAttribute('open');
      // marker visibility
      let markerHidden = true;
      if (summary) {
        const before = getComputedStyle(summary, '::-webkit-details-marker');
        // list-style none
        markerHidden = getComputedStyle(summary).listStyleType === 'none' || getComputedStyle(summary).listStyle === 'none';
      }
      // buttons in drawer
      const buttons = [...el.querySelectorAll('button')].map((b) => {
        const r = b.getBoundingClientRect();
        return {
          testid: b.getAttribute('data-testid'),
          h: Math.round(r.height * 10) / 10,
          top: Math.round(r.top * 10) / 10,
          text: (b.textContent || '').trim().slice(0, 40),
        };
      });
      // same-row h-8 groups: cluster by top within 1px
      const visibleBtns = buttons.filter((b) => b.h > 0);
      const rows = {};
      for (const b of visibleBtns) {
        const key = Math.round(b.top);
        rows[key] = rows[key] || [];
        rows[key].push(b);
      }
      let stepTopDelta = 0;
      let buttonHeightOk = true;
      for (const row of Object.values(rows)) {
        if (row.length < 2) continue;
        const tops = row.map((x) => x.top);
        stepTopDelta = Math.max(stepTopDelta, Math.max(...tops) - Math.min(...tops));
        for (const b of row) {
          if (Math.abs(b.h - 32) > 1.5 && b.testid) buttonHeightOk = false;
        }
      }
      return {
        id,
        present: true,
        open,
        summary: rect
          ? { x: Math.round(rect.x * 10) / 10, w: Math.round(rect.width * 10) / 10, h: Math.round(rect.height * 10) / 10, y: Math.round(rect.y * 10) / 10 }
          : null,
        markerHidden,
        buttonHeightOk,
        stepTopDelta,
        buttonCount: buttons.length,
      };
    });

    // FFmpeg details (no testid) — find by summary text
    const allDetails = [...document.querySelectorAll('details')];
    const ffmpegDetails = allDetails.find((d) =>
      (d.querySelector('summary')?.textContent || '').includes('FFmpeg CLI')
    );
    let ffmpeg = null;
    if (ffmpegDetails) {
      const s = ffmpegDetails.querySelector(':scope > summary');
      const r = s?.getBoundingClientRect();
      ffmpeg = {
        present: true,
        open: ffmpegDetails.hasAttribute('open'),
        summary: r
          ? { x: Math.round(r.x * 10) / 10, w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }
          : null,
      };
    }

    const testids = [...document.querySelectorAll('[data-testid]')].map((el) => el.getAttribute('data-testid'));
    const uniqueTestids = [...new Set(testids)];

    return {
      state,
      horizontalOverflow,
      stickyHeaderOpaque,
      nestedCards: nestedCards.length,
      nestedCardSamples: nestedCards.slice(0, 8),
      drawers,
      ffmpeg,
      uniqueTestidCount: uniqueTestids.length,
      testidOccurrenceCount: testids.length,
    };
  }, { drawerTestIds: DRAWER_TESTIDS, state });
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  const html = await fetch(BASE + '/').then((r) => r.text());
  const testidMatches = [...html.matchAll(/data-testid="([^"]+)"/g)].map((m) => m[1]);
  const uniqueSSR = [...new Set(testidMatches)];
  const geoHits = Object.fromEntries(GEO_TERMS.map((t) => [t, html.includes(t)]));
  const detailsOpenDefault = (html.match(/<details[^>]*\sopen[\s>]/gi) || []).length;
  const detailsCount = (html.match(/<details\b/gi) || []).length;
  // PD drawers should not have open in SSR (except maybe FAQ)
  const pdOpenInSSR = DRAWER_TESTIDS.filter((id) => {
    const re = new RegExp(`data-testid="${id}"[^>]*\\sopen[\\s>]|<details[^>]*\\sopen[^>]*data-testid="${id}"`, 'i');
    return re.test(html);
  });

  const report = {
    base: BASE,
    ssr: {
      uniqueTestids: uniqueSSR.length,
      testidOccurrences: testidMatches.length,
      uniqueList: uniqueSSR.sort(),
      geoHits,
      detailsCount,
      detailsOpenDefault,
      pdOpenInSSR,
    },
    viewports: {},
  };

  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(800);

    // A: collapsed
    const collapsed = await measure(page, 'collapsed');
    // capture summary anchors before expand
    const beforeAnchors = Object.fromEntries(
      collapsed.drawers.filter((d) => d.present).map((d) => [d.id, d.summary])
    );
    if (collapsed.ffmpeg?.summary) beforeAnchors['ffmpeg'] = collapsed.ffmpeg.summary;

    const shotA = `/workspace/fe-pd-${vp.name}-${vp.width}x${vp.height}.png`;
    await page.screenshot({ path: shotA, fullPage: false });

    // B: expand all PD drawers
    await page.evaluate((ids) => {
      for (const id of ids) {
        const el = document.querySelector(`[data-testid="${id}"]`);
        if (el) el.open = true;
      }
      for (const d of document.querySelectorAll('details')) {
        const t = d.querySelector('summary')?.textContent || '';
        if (t.includes('FFmpeg CLI') || t.includes('Workbench Controls')) d.open = true;
      }
    }, DRAWER_TESTIDS);
    await page.waitForTimeout(400);
    const expanded = await measure(page, 'expanded');
    const afterAnchors = Object.fromEntries(
      expanded.drawers.filter((d) => d.present).map((d) => [d.id, d.summary])
    );
    if (expanded.ffmpeg?.summary) afterAnchors['ffmpeg'] = expanded.ffmpeg.summary;

    const drift = {};
    for (const key of Object.keys(beforeAnchors)) {
      const b = beforeAnchors[key];
      const a = afterAnchors[key];
      if (!b || !a) {
        drift[key] = { missing: true };
        continue;
      }
      drift[key] = {
        dx: Math.round((a.x - b.x) * 10) / 10,
        dw: Math.round((a.w - b.w) * 10) / 10,
      };
    }

    report.viewports[vp.name] = {
      size: vp,
      collapsed,
      expanded,
      summaryDrift: drift,
      screenshotCollapsed: shotA,
    };
    await context.close();
  }

  await browser.close();
  fs.writeFileSync('/workspace/fe-pd-audit-report.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
