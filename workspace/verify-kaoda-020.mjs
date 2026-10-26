import { chromium } from 'playwright';

const BASE = 'http://127.0.0.1:10099';

function parseAlpha(bg) {
  if (!bg || bg === 'transparent') return 0;
  const rgba = bg.match(/rgba\(([^)]+)\)/);
  if (rgba) {
    const parts = rgba[1].split(',').map(s => s.trim());
    return parseFloat(parts[3] ?? '1');
  }
  const rgb = bg.match(/rgb\(([^)]+)\)/);
  if (rgb) return 1;
  return 0;
}

async function auditCommon(page, routeName, vpName) {
  return page.evaluate(({ routeName, vpName }) => {
    const docEl = document.documentElement;
    const horizOverflow = docEl.scrollWidth > docEl.clientWidth + 1;

    const topbar = document.querySelector('.topbar');
    const topbarCs = topbar ? getComputedStyle(topbar) : null;
    const topbarBg = topbarCs ? topbarCs.backgroundColor : null;
    const topbarRect = topbar ? topbar.getBoundingClientRect() : null;

    const brandSvg = document.querySelector('.brand-mark svg, .brand svg');
    const brandSvgRect = brandSvg ? brandSvg.getBoundingClientRect() : null;
    const faviconLinks = [...document.querySelectorAll('link[rel*="icon"]')].map(l => l.getAttribute('href'));

    const nativeSelects = document.querySelectorAll('select').length;

    // Monochrome check on computed colors across all visible elements
    const coloredElements = [];
    const checkColorStr = (str, prop, el) => {
      if (!str) return;
      const m = str.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
      if (!m) return;
      const r = Number(m[1]), g = Number(m[2]), b = Number(m[3]);
      if (Math.max(r, g, b) - Math.min(r, g, b) > 8) {
        coloredElements.push({ tag: el.tagName, cls: String(el.className || '').slice(0, 50), prop, val: str });
      }
    };
    for (const el of document.querySelectorAll('*')) {
      const cs = getComputedStyle(el);
      checkColorStr(cs.color, 'color', el);
      checkColorStr(cs.backgroundColor, 'backgroundColor', el);
      checkColorStr(cs.borderTopColor, 'borderTopColor', el);
      checkColorStr(cs.borderLeftColor, 'borderLeftColor', el);
    }

    // Nested card check
    const cardSelectors = '.panel, .item-card, .tg-summary-panel';
    const nestedCards = [];
    for (const card of document.querySelectorAll(cardSelectors)) {
      for (const child of card.querySelectorAll('*')) {
        if (child === card) continue;
        if (child.matches('button, a, input, .pill, .keyword, .count, .segmented, .segment, .tg-picker-trigger, .tg-group-picker, .tg-image-thumb, .tg-image-link, .tg-ai-state, .tg-merchant-chip, .tg-topic-group, .tg-hour-state, .side-link, .error-box, .tg-topic')) continue;
        const cs = getComputedStyle(child);
        const bwTop = parseFloat(cs.borderTopWidth) || 0;
        const bwRight = parseFloat(cs.borderRightWidth) || 0;
        const bwBottom = parseFloat(cs.borderBottomWidth) || 0;
        const bwLeft = parseFloat(cs.borderLeftWidth) || 0;
        const radius = parseFloat(cs.borderTopLeftRadius) || 0;
        if (bwTop >= 1 && bwRight >= 1 && bwBottom >= 1 && bwLeft >= 1 && radius >= 6) {
          nestedCards.push({
            parent: card.className,
            child: `${child.tagName}.${child.className}`,
            border: `${bwTop}/${bwRight}/${bwBottom}/${bwLeft}`,
            radius,
          });
        }
      }
    }

    // Short-label wrapping check
    const wrappedShortLabels = [];
    for (const el of document.querySelectorAll('button, .button, .segment, .tg-view-tab, .pill, .keyword, .count, th, .nav-link')) {
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      const text = (el.textContent || '').trim().replace(/\s+/g, '');
      if (text.length >= 2 && text.length <= 5) {
        const cs = getComputedStyle(el);
        const lh = parseFloat(cs.lineHeight) || (parseFloat(cs.fontSize) * 1.4);
        const padY = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
        const innerH = rect.height - padY;
        if (innerH > lh * 1.65 && cs.whiteSpace !== 'nowrap') {
          wrappedShortLabels.push({ tag: el.tagName, cls: el.className, text, innerH: Math.round(innerH), lh: Math.round(lh) });
        }
      }
    }

    // Nested vertical scrollbars check
    const verticalScrollers = [];
    for (const el of document.querySelectorAll('*')) {
      const cs = getComputedStyle(el);
      if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 2) {
        verticalScrollers.push({
          tag: el.tagName,
          cls: String(el.className || '').slice(0, 60),
          clientH: el.clientHeight,
          scrollH: el.scrollHeight,
        });
      }
    }

    return {
      routeName,
      vpName,
      scrollW: docEl.scrollWidth,
      clientW: docEl.clientWidth,
      horizOverflow,
      topbarBg,
      topbarTop: topbarRect ? Math.round(topbarRect.top) : null,
      topbarBottom: topbarRect ? Math.round(topbarRect.bottom) : null,
      logoVisible: Boolean(brandSvgRect && brandSvgRect.width >= 16 && brandSvgRect.height >= 16),
      faviconLinks,
      nativeSelects,
      coloredElementsCount: coloredElements.length,
      coloredElementsSample: coloredElements.slice(0, 5),
      nestedCardsCount: nestedCards.length,
      nestedCards,
      wrappedShortLabelsCount: wrappedShortLabels.length,
      wrappedShortLabels,
      verticalScrollersCount: verticalScrollers.length,
      verticalScrollers,
    };
  }, { routeName, vpName });
}

const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
const report = { buildInfo: null, favicons: {}, routes: {}, tgStickyAndGutter: {}, accordionChecks: {} };

{
  const page = await browser.newPage();
  const bRes = await page.goto(`${BASE}/build.json`);
  report.buildInfo = await bRes?.json().catch(() => null);
  for (const path of ['/favicon.svg', '/favicon.ico', '/build-info.json']) {
    const res = await page.goto(`${BASE}${path}`);
    report.favicons[path] = { status: res?.status(), contentType: res?.headers()['content-type'] };
  }
  await page.close();
}

const viewports = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'mobile', width: 390, height: 844 },
];

const routesToTest = [
  { name: 'briefs', url: '/briefs' },
  { name: 'bookmarks-urgent', url: '/bookmarks/urgent' },
  { name: 'tg', url: '/tg?date=2026-10-23' },
  { name: 'tg-merged', url: '/tg?date=2026-10-23&view=merged' },
  { name: 'radar', url: '/radar/new' },
  { name: 'forum', url: '/forum' },
  { name: 'login', url: '/login' },
];

for (const vp of viewports) {
  report.routes[vp.name] = {};
  const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
  const page = await context.newPage();

  for (const r of routesToTest) {
    await page.goto(`${BASE}${r.url}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(350);
    const res = await auditCommon(page, r.name, vp.name);
    res.topbarAlpha = parseAlpha(res.topbarBg);
    report.routes[vp.name][r.name] = res;

    // Save requested screenshots
    if (vp.name === 'desktop' && r.name === 'tg') {
      await page.screenshot({ path: `/workspace/hb-mobile/kaoda020-desktop-tg.png` });
    }
    if (vp.name === 'mobile' && ['tg', 'tg-merged', 'briefs', 'radar', 'forum'].includes(r.name)) {
      await page.screenshot({ path: `/workspace/hb-mobile/kaoda020-mobile-${r.name}.png` });
    }
  }

  // Detailed Sticky & Gutter Audit on /tg?date=2026-10-23
  await page.goto(`${BASE}/tg?date=2026-10-23`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.tg-timeline', { timeout: 10000 });
  await page.waitForTimeout(350);

  const tgAudit = await page.evaluate((vpName) => {
    const reader = document.querySelector('.tg-reader');
    if (reader) reader.scrollTop = 320;
    const topbar = document.querySelector('.topbar');
    const shell = document.querySelector('.tg-timeline-shell');
    const timeline = document.querySelector('.tg-timeline');
    const winNav = document.querySelector('.tg-window-nav');

    const topbarRect = topbar.getBoundingClientRect();
    const shellRect = shell.getBoundingClientRect();
    const timelineRect = timeline.getBoundingClientRect();
    const winNavRect = winNav && getComputedStyle(winNav).display !== 'none' ? winNav.getBoundingClientRect() : null;
    const readerRect = reader.getBoundingClientRect();
    const readerCs = getComputedStyle(reader);
    const timelineCs = getComputedStyle(timeline);
    const shellCs = getComputedStyle(shell);
    const winNavCs = winNav ? getComputedStyle(winNav) : null;

    const midX = Math.round(timelineRect.left + timelineRect.width / 2);
    const seamTopbarTimeline = document.elementFromPoint(midX, Math.round(shellRect.top + 1));
    const bottomLeftCorner = document.elementFromPoint(Math.round(timelineRect.left + 2), Math.round(timelineRect.bottom - 2));
    const bottomRightCorner = document.elementFromPoint(Math.round(timelineRect.right - 2), Math.round(timelineRect.bottom - 2));

    const isInsideStickyOrChrome = (el) => Boolean(el && el.closest('.topbar, .tg-timeline-shell, .tg-window-nav'));

    return {
      vpName,
      topbarBg: getComputedStyle(topbar).backgroundColor,
      shellBg: shellCs.backgroundColor,
      timelineBg: timelineCs.backgroundColor,
      winNavBg: winNavCs ? winNavCs.backgroundColor : null,
      gapAboveStickyPanel: Math.round(shellRect.top - topbarRect.bottom),
      gapBetweenStickyLayers: winNavRect ? Math.round(winNavRect.top - shellRect.bottom) : 0,
      seamHitOk: isInsideStickyOrChrome(seamTopbarTimeline),
      bottomLeftCornerHitOk: isInsideStickyOrChrome(bottomLeftCorner),
      bottomRightCornerHitOk: isInsideStickyOrChrome(bottomRightCorner),
      readerPadLeft: parseFloat(readerCs.paddingLeft) || 0,
      readerPadRight: parseFloat(readerCs.paddingRight) || 0,
      leftInset: Math.round(timelineRect.left - readerRect.left),
      rightInsetFromClient: Math.round((readerRect.left + reader.clientWidth) - timelineRect.right),
    };
  }, vp.name);

  tgAudit.topbarAlpha = parseAlpha(tgAudit.topbarBg);
  tgAudit.shellAlpha = parseAlpha(tgAudit.shellBg);
  tgAudit.timelineAlpha = parseAlpha(tgAudit.timelineBg);
  tgAudit.winNavAlpha = tgAudit.winNavBg ? parseAlpha(tgAudit.winNavBg) : 1;
  report.tgStickyAndGutter[vp.name] = tgAudit;

  // 3-level accordion verification in 按时段 (mobile) and 合并相似 (desktop + mobile)
  let slotAccOk = true;
  if (vp.name === 'mobile') {
    await page.goto(`${BASE}/tg?date=2026-10-23`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(300);
    slotAccOk = await page.evaluate(() => {
      const slot = document.querySelector('.tg-m-acc-slot');
      if (!slot) return false;
      if (!slot.open) slot.querySelector('summary')?.click();
      const topic = slot.querySelector('.tg-m-acc-topic');
      if (!topic) return false;
      if (!topic.open) topic.querySelector('summary')?.click();
      const body = topic.querySelector('.tg-m-acc-topic-body');
      return Boolean(slot.open && topic.open && body && body.getBoundingClientRect().height > 20);
    });
  }

  await page.goto(`${BASE}/tg?date=2026-10-23&view=merged`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  const mergedAcc = await page.evaluate(() => {
    const s = [...document.querySelectorAll('.tg-merged-section')].find(el => el.textContent.includes('Monzo相关')) || document.querySelector('.tg-merged-section');
    if (s && !s.open) s.querySelector('summary')?.click();
    const m = [...(s?.querySelectorAll('.tg-merged-member') || [])].find(el => el.textContent.includes('Revolut')) || s?.querySelector('.tg-merged-member');
    if (m && !m.open) m.querySelector('summary')?.click();
    const body = m?.querySelector('.tg-merged-member-body');
    return {
      l1Open: Boolean(s?.open),
      l2Open: Boolean(m?.open),
      l3Height: Math.round(body?.getBoundingClientRect().height || 0),
      l3Messages: body?.querySelectorAll('.tg-message').length || 0,
    };
  });
  if (vp.name === 'mobile') {
    await page.screenshot({ path: `/workspace/hb-mobile/kaoda020-mobile-tg-merged.png` });
  }
  report.accordionChecks[vp.name] = { slotAccOk, mergedAcc };

  await context.close();
}

await browser.close();
console.log(JSON.stringify(report, null, 2));
