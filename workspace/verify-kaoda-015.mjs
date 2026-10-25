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

function srgbToLuminance(r, g, b) {
  const [R, G, B] = [r, g, b].map(v => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

function contrastRatio(rgb1, rgb2) {
  const L1 = srgbToLuminance(...rgb1);
  const L2 = srgbToLuminance(...rgb2);
  const lighter = Math.max(L1, L2);
  const darker = Math.min(L1, L2);
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(2));
}

async function auditCommon(page, routeName, vpName) {
  return page.evaluate(({ routeName, vpName }) => {
    const docEl = document.documentElement;
    const horizOverflow = docEl.scrollWidth > docEl.clientWidth + 1;

    // 1. Topbar sticky & opacity check
    const topbar = document.querySelector('.topbar');
    const topbarCs = topbar ? getComputedStyle(topbar) : null;
    const topbarBg = topbarCs ? topbarCs.backgroundColor : null;
    const topbarRect = topbar ? topbar.getBoundingClientRect() : null;

    // 2. Visible logo & favicon links
    const brandSvg = document.querySelector('.brand-mark svg, .brand svg');
    const brandSvgRect = brandSvg ? brandSvg.getBoundingClientRect() : null;
    const faviconLinks = [...document.querySelectorAll('link[rel*="icon"]')].map(l => l.getAttribute('href'));

    // 3. Native select check
    const nativeSelects = document.querySelectorAll('select').length;

    // 4. Nested card check (card inside card with visible border + background/radius)
    const cardSelectors = '.panel, .item-card, .tg-summary-panel';
    const nestedCards = [];
    for (const card of document.querySelectorAll(cardSelectors)) {
      for (const child of card.querySelectorAll('*')) {
        if (child === card) continue;
        // Skip controls/buttons/badges/inputs/thumbs
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

    // 5. Short-label wrapping check (buttons, tabs, pills, th, badges with 2-5 CJK chars wrapping > 1 line)
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

    // 6. Nested vertical scrollbars check
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

    // 7. Page padding & main anchor
    const pageEl = document.querySelector('.page');
    const pageCs = pageEl ? getComputedStyle(pageEl) : null;
    const mainCol = document.querySelector('.content-grid > :first-child, .forum-layout > :first-child, .tg-reader');
    const mainRect = mainCol ? mainCol.getBoundingClientRect() : null;
    const toolbar = document.querySelector('.page-head .toolbar, .tg-timeline-controls');
    const toolbarRect = toolbar ? toolbar.getBoundingClientRect() : null;

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
      nestedCards,
      wrappedShortLabels,
      verticalScrollers,
      pagePaddingLeft: pageCs ? pageCs.paddingLeft : null,
      pagePaddingRight: pageCs ? pageCs.paddingRight : null,
      mainLeft: mainRect ? Math.round(mainRect.left) : null,
      mainWidth: mainRect ? Math.round(mainRect.width) : null,
      toolbarLeft: toolbarRect ? Math.round(toolbarRect.left) : null,
      toolbarTop: toolbarRect ? Math.round(toolbarRect.top) : null,
    };
  }, { routeName, vpName });
}

const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
const report = { favicons: {}, routes: {}, tgStickyAndGutter: {}, stateAnchorChecks: {} };

// Check favicon HTTP status
{
  const page = await browser.newPage();
  for (const path of ['/favicon.svg', '/favicon.ico', '/version.json']) {
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
  { name: 'bookmarks-open', url: '/bookmarks/open' },
  { name: 'bookmarks-done', url: '/bookmarks/done' },
  { name: 'radar-new', url: '/radar/new' },
  { name: 'radar-hot', url: '/radar/hot' },
  { name: 'forum', url: '/forum' },
  { name: 'tg-slots', url: '/tg?date=2026-10-23' },
  { name: 'tg-merged', url: '/tg?date=2026-10-23&view=merged' },
  { name: 'login', url: '/login' },
];

for (const vp of viewports) {
  report.routes[vp.name] = {};
  const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
  const page = await context.newPage();

  for (const r of routesToTest) {
    await page.goto(`${BASE}${r.url}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(300);

    // Also test scrolled state for topbar opacity on non-tg routes
    if (!r.name.startsWith('tg-') && r.name !== 'login') {
      await page.evaluate(() => window.scrollTo(0, 120));
      await page.waitForTimeout(100);
    }

    const res = await auditCommon(page, r.name, vp.name);
    res.topbarAlpha = parseAlpha(res.topbarBg);
    report.routes[vp.name][r.name] = res;

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(100);
    await page.screenshot({ path: `/workspace/hb-mobile/kaoda015-${vp.name}-${r.name}.png` });
  }

  // Detailed Section 21 (Sticky Continuity & Opacity) + Section 22 (Scrollbar Gutter & Symmetric Padding) on /tg
  await page.goto(`${BASE}/tg?date=2026-10-23`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.tg-timeline', { timeout: 10000 });
  await page.waitForTimeout(400);

  // Scroll reader down by 320px so sticky layers engage over scrolled content
  const tgAudit = await page.evaluate((vpName) => {
    const reader = document.querySelector('.tg-reader');
    if (reader) reader.scrollTop = 320;
    const topbar = document.querySelector('.topbar');
    const shell = document.querySelector('.tg-timeline-shell');
    const timeline = document.querySelector('.tg-timeline');
    const winNav = document.querySelector('.tg-window-nav');
    const controls = document.querySelector('.tg-timeline-controls');

    const topbarRect = topbar.getBoundingClientRect();
    const shellRect = shell.getBoundingClientRect();
    const timelineRect = timeline.getBoundingClientRect();
    const winNavRect = winNav ? winNav.getBoundingClientRect() : null;
    const readerRect = reader.getBoundingClientRect();
    const readerCs = getComputedStyle(reader);
    const timelineCs = getComputedStyle(timeline);
    const shellCs = getComputedStyle(shell);
    const winNavCs = winNav ? getComputedStyle(winNav) : null;

    // Measure first and last visible control in .tg-timeline-controls
    const visibleBtns = [...controls.children].filter(el => {
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return cs.display !== 'none' && r.width > 0 && r.height > 0;
    });
    const firstBtn = visibleBtns[0]?.getBoundingClientRect();
    const lastBtn = visibleBtns[visibleBtns.length - 1]?.getBoundingClientRect();

    // Seam & corner elementFromPoint checks while scrolled
    const midX = Math.round(timelineRect.left + timelineRect.width / 2);
    const seamTopbarTimeline = document.elementFromPoint(midX, Math.round(shellRect.top + 1));
    const bottomLeftCorner = document.elementFromPoint(Math.round(timelineRect.left + 2), Math.round(timelineRect.bottom - 2));
    const bottomRightCorner = document.elementFromPoint(Math.round(timelineRect.right - 2), Math.round(timelineRect.bottom - 2));

    const isInsideStickyOrChrome = (el) => {
      if (!el) return false;
      return Boolean(el.closest('.topbar, .tg-timeline-shell, .tg-window-nav'));
    };

    const gutterWidth = Math.round(reader.offsetWidth - reader.clientWidth);
    const padLeft = parseFloat(readerCs.paddingLeft) || 0;
    const padRight = parseFloat(readerCs.paddingRight) || 0;
    const leftInset = Math.round(timelineRect.left - readerRect.left);
    const rightInsetFromClient = Math.round((readerRect.left + reader.clientWidth) - timelineRect.right);
    const rightInsetFromBorder = Math.round(readerRect.right - timelineRect.right);

    const winNavPadLeft = winNavCs ? parseFloat(winNavCs.paddingLeft) || 0 : null;
    const winNavPadRight = winNavCs ? parseFloat(winNavCs.paddingRight) || 0 : null;

    return {
      vpName,
      readerScrollTop: reader.scrollTop,
      topbarBg: getComputedStyle(topbar).backgroundColor,
      shellBg: shellCs.backgroundColor,
      timelineBg: timelineCs.backgroundColor,
      winNavBg: winNavCs ? winNavCs.backgroundColor : null,
      gapAboveStickyPanel: Math.round(shellRect.top - topbarRect.bottom),
      gapBetweenStickyLayers: winNavRect ? Math.round(winNavRect.top - shellRect.bottom) : 0,
      seamHitOk: isInsideStickyOrChrome(seamTopbarTimeline),
      bottomLeftCornerHitOk: isInsideStickyOrChrome(bottomLeftCorner),
      bottomRightCornerHitOk: isInsideStickyOrChrome(bottomRightCorner),
      seamHitTag: seamTopbarTimeline ? `${seamTopbarTimeline.tagName}.${seamTopbarTimeline.className}` : null,
      bottomLeftCornerTag: bottomLeftCorner ? `${bottomLeftCorner.tagName}.${bottomLeftCorner.className}` : null,
      bottomRightCornerTag: bottomRightCorner ? `${bottomRightCorner.tagName}.${bottomRightCorner.className}` : null,
      readerPadLeft: padLeft,
      readerPadRight: padRight,
      gutterWidth,
      leftInset,
      rightInsetFromClient,
      rightInsetFromBorder,
      timelineInnerLeftInset: firstBtn ? Math.round(firstBtn.left - timelineRect.left) : null,
      timelineInnerRightInset: lastBtn ? Math.round(timelineRect.right - lastBtn.right) : null,
      winNavPadLeft,
      winNavPadRight,
      readingHeightBelowStack: Math.round(readerRect.bottom - (winNavRect && winNavRect.width > readerRect.width * 0.5 ? winNavRect.bottom : shellRect.bottom)),
    };
  }, vp.name);

  tgAudit.topbarAlpha = parseAlpha(tgAudit.topbarBg);
  tgAudit.shellAlpha = parseAlpha(tgAudit.shellBg);
  tgAudit.timelineAlpha = parseAlpha(tgAudit.timelineBg);
  tgAudit.winNavAlpha = tgAudit.winNavBg ? parseAlpha(tgAudit.winNavBg) : null;
  const overlaySim = await page.evaluate(() => {
    const style = document.createElement('style');
    style.id = 'kaoda-overlay-sim';
    style.textContent = 'html.tg-lock-scroll .tg-reader { scrollbar-gutter: auto !important; } .tg-reader::-webkit-scrollbar { width: 0px !important; display: none !important; }';
    document.head.appendChild(style);
    const reader = document.querySelector('.tg-reader');
    const shell = document.querySelector('.tg-timeline-shell');
    const rRect = reader.getBoundingClientRect();
    const sRect = shell.getBoundingClientRect();
    const cs = getComputedStyle(reader);
    const res = {
      padLeft: parseFloat(cs.paddingLeft),
      padRight: parseFloat(cs.paddingRight),
      gutterWidth: Math.round(reader.offsetWidth - reader.clientWidth),
      leftInset: Math.round(sRect.left - rRect.left),
      rightInsetFromBorder: Math.round(rRect.right - sRect.right),
      diff: Math.round((rRect.right - sRect.right) - (sRect.left - rRect.left)),
    };
    style.remove();
    return res;
  });
  tgAudit.overlayScrollbarSim = overlaySim;
  report.tgStickyAndGutter[vp.name] = tgAudit;
  await page.screenshot({ path: `/workspace/hb-mobile/kaoda015-${vp.name}-tg-scrolled.png` });

  // Also test merged view L1 -> L2 -> L3 in-place expansion & anchor stability
  await page.goto(`${BASE}/tg?date=2026-10-23&view=merged`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.tg-timeline', { timeout: 10000 });
  await page.waitForTimeout(300);
  const mergedAnchorBefore = await page.evaluate(() => {
    const timeline = document.querySelector('.tg-timeline');
    const stream = document.querySelector('.tg-day-stream, .tg-m');
    return {
      timelineLeft: Math.round(timeline.getBoundingClientRect().left),
      timelineWidth: Math.round(timeline.getBoundingClientRect().width),
      streamLeft: Math.round(stream.getBoundingClientRect().left),
      streamWidth: Math.round(stream.getBoundingClientRect().width),
    };
  });
  await page.evaluate(() => {
    const s = [...document.querySelectorAll('.tg-merged-section')].find(el => el.textContent.includes('Monzo相关'));
    if (s && !s.open) s.querySelector('summary').click();
  });
  await page.waitForTimeout(150);
  await page.evaluate(() => {
    const s = [...document.querySelectorAll('.tg-merged-section')].find(el => el.textContent.includes('Monzo相关'));
    const m = [...(s?.querySelectorAll('.tg-merged-member') || [])].find(el => el.textContent.includes('Revolut 与 Monzo 体量之争'));
    if (m && !m.open) m.querySelector('summary').click();
  });
  await page.waitForTimeout(200);
  const mergedAnchorAfter = await page.evaluate(() => {
    const timeline = document.querySelector('.tg-timeline');
    const stream = document.querySelector('.tg-day-stream, .tg-m');
    const s = [...document.querySelectorAll('.tg-merged-section')].find(el => el.textContent.includes('Monzo相关'));
    const m = [...(s?.querySelectorAll('.tg-merged-member') || [])].find(el => el.textContent.includes('Revolut 与 Monzo 体量之争'));
    const body = m?.querySelector('.tg-merged-member-body');
    return {
      timelineLeft: Math.round(timeline.getBoundingClientRect().left),
      timelineWidth: Math.round(timeline.getBoundingClientRect().width),
      streamLeft: Math.round(stream.getBoundingClientRect().left),
      streamWidth: Math.round(stream.getBoundingClientRect().width),
      l3Open: Boolean(m?.open),
      l3Height: Math.round(body?.getBoundingClientRect().height || 0),
      l3Messages: body?.querySelectorAll('.tg-message').length || 0,
    };
  });
  await page.screenshot({ path: `/workspace/hb-mobile/kaoda015-${vp.name}-tg-merged-expanded.png` });

  // Also test empty date anchor on /tg?date=2026-01-01&view=merged vs populated
  await page.goto(`${BASE}/tg?date=2026-01-01&view=merged`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(250);
  const mergedAnchorEmpty = await page.evaluate(() => {
    const timeline = document.querySelector('.tg-timeline');
    const stream = document.querySelector('.tg-day-stream, .tg-m');
    return {
      timelineLeft: Math.round(timeline.getBoundingClientRect().left),
      timelineWidth: Math.round(timeline.getBoundingClientRect().width),
      streamLeft: Math.round(stream.getBoundingClientRect().left),
      streamWidth: Math.round(stream.getBoundingClientRect().width),
    };
  });

  report.stateAnchorChecks[vp.name] = {
    tgMergedBefore: mergedAnchorBefore,
    tgMergedAfterExpand: mergedAnchorAfter,
    tgMergedEmptyDate: mergedAnchorEmpty,
    tgTimelineDriftOnExpand: Math.abs(mergedAnchorAfter.timelineLeft - mergedAnchorBefore.timelineLeft) + Math.abs(mergedAnchorAfter.timelineWidth - mergedAnchorBefore.timelineWidth),
    tgStreamDriftOnExpand: Math.abs(mergedAnchorAfter.streamLeft - mergedAnchorBefore.streamLeft) + Math.abs(mergedAnchorAfter.streamWidth - mergedAnchorBefore.streamWidth),
    tgStreamDriftOnEmpty: Math.abs(mergedAnchorEmpty.streamLeft - mergedAnchorBefore.streamLeft) + Math.abs(mergedAnchorEmpty.streamWidth - mergedAnchorBefore.streamWidth),
    bookmarksUrgentVsOpenMainDrift:
      Math.abs(report.routes[vp.name]['bookmarks-urgent'].mainLeft - report.routes[vp.name]['bookmarks-open'].mainLeft) +
      Math.abs(report.routes[vp.name]['bookmarks-urgent'].mainWidth - report.routes[vp.name]['bookmarks-open'].mainWidth),
    bookmarksUrgentVsDoneMainDrift:
      Math.abs(report.routes[vp.name]['bookmarks-urgent'].mainLeft - report.routes[vp.name]['bookmarks-done'].mainLeft) +
      Math.abs(report.routes[vp.name]['bookmarks-urgent'].mainWidth - report.routes[vp.name]['bookmarks-done'].mainWidth),
  };

  await context.close();
}

await browser.close();
console.log(JSON.stringify(report, null, 2));
