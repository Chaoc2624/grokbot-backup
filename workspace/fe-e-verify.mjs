import { chromium } from 'playwright';
import fs from 'fs';

const BASE = process.env.PD_BASE || 'https://frame-extractor.app';
const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 800, shot: '/workspace/fe-pd-next-desktop-1280x800.png' },
  { name: 'mobile', width: 390, height: 844, shot: '/workspace/fe-pd-next-mobile-390x844.png' },
];
const REQUIRED_TESTIDS = [
  'ssr-workbench-controls',
  'micro-filmstrip-loupe',
  'engineering-verification-table',
  'codec-compat-matrix',
  'try-sample-video-btn',
  'batch-contact-sheet-panel',
  'post-download-next-steps',
];

function isCardish(el) {
  // evaluated in page
}

async function kexMetrics(page, state) {
  return page.evaluate((state) => {
    const docEl = document.documentElement;
    const horizontalOverflow = Math.max(0, docEl.scrollWidth - docEl.clientWidth);

    const header =
      document.querySelector('header') ||
      document.querySelector('[data-testid="site-header"]');
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
      stickyHeaderOpaque =
        a >= 0.85 ||
        (cs.backdropFilter || '').includes('blur') ||
        (cs.webkitBackdropFilter || '').includes('blur');
    }

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
    for (const el of document.querySelectorAll('details, section, div, article')) {
      if (!isCardish(el)) continue;
      let p = el.parentElement;
      while (p && p !== document.body) {
        if (isCardish(p)) {
          nestedCards.push({
            child: `${el.tagName}.${String(el.className || '').slice(0, 60)}`,
            parent: `${p.tagName}.${String(p.className || '').slice(0, 60)}`,
            testid: el.getAttribute('data-testid') || p.getAttribute('data-testid'),
          });
          break;
        }
        p = p.parentElement;
      }
    }

    // Empty-state above-fold clickables (viewport)
    const vh = window.innerHeight;
    const interactive = [...document.querySelectorAll('button, a[href], [role="button"], input[type="file"]')];
    const aboveFoldClickables = interactive
      .filter((el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > vh) return false;
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none' || cs.pointerEvents === 'none') return false;
        if (el.getAttribute('aria-disabled') === 'true' || el.disabled) return false;
        // skip hidden file input
        if (el.tagName === 'INPUT' && cs.display === 'none') return false;
        return true;
      })
      .map((el) => ({
        tag: el.tagName,
        testid: el.getAttribute('data-testid'),
        text: (el.textContent || '').trim().slice(0, 48),
        href: el.getAttribute('href'),
      }));

    const workbench = document.querySelector('[data-testid="ssr-workbench-controls"]');
    let workbenchPreview = null;
    if (workbench) {
      const chips = [...workbench.querySelectorAll('[aria-disabled="true"]')];
      const realButtons = [...workbench.querySelectorAll('button')].filter((b) => !b.disabled);
      workbenchPreview = {
        open: workbench.hasAttribute('open'),
        staticChips: chips.length,
        enabledButtons: realButtons.length,
        grabChipIsSpan:
          workbench.querySelector('[data-testid="grab-and-download-frame"]')?.tagName === 'SPAN',
      };
    }

    const batch = document.querySelector('[data-testid="batch-contact-sheet-panel"]');
    const next = document.querySelector('[data-testid="post-download-next-steps"]');
    let nextInfo = null;
    if (next) {
      const btns = [...next.querySelectorAll('button')].map((b) => ({
        text: (b.textContent || '').trim(),
        variantGuess: b.className.includes('bg-primary') || b.className.includes('bg-foreground') ? 'solidish' : 'outlineish',
        h: Math.round(b.getBoundingClientRect().height * 10) / 10,
      }));
      const links = [...next.querySelectorAll('a')].map((a) => a.getAttribute('href'));
      nextInfo = {
        title: (next.querySelector('p')?.textContent || '').trim().slice(0, 40),
        buttons: btns,
        links,
        nestedCardish: isCardish(next) && [...next.querySelectorAll('div,section')].some(isCardish),
      };
    }

    let batchInfo = null;
    if (batch) {
      const summary = batch.querySelector(':scope > summary');
      const sr = summary?.getBoundingClientRect();
      batchInfo = {
        open: batch.hasAttribute('open'),
        summaryText: (summary?.textContent || '').trim().slice(0, 80),
        summaryH: sr ? Math.round(sr.height * 10) / 10 : null,
      };
    }

    // Primary CTA uniqueness when active workbench visible
    const solidGrab = [...document.querySelectorAll('[data-testid="grab-and-download-frame"]')].filter(
      (el) => el.tagName === 'BUTTON' && !el.disabled
    );
    const solidGrabStyles = solidGrab.map((el) => {
      const cs = getComputedStyle(el);
      return {
        bg: cs.backgroundColor,
        h: Math.round(el.getBoundingClientRect().height * 10) / 10,
        text: (el.textContent || '').trim(),
      };
    });

    const testids = [...new Set([...document.querySelectorAll('[data-testid]')].map((e) => e.getAttribute('data-testid')))];

    // subtitle fake-link check
    const techLine = [...document.querySelectorAll('p')].find((p) =>
      (p.textContent || '').includes('Exact PTS Frame-Lock')
    );
    let techLineOk = null;
    if (techLine) {
      const cs = getComputedStyle(techLine);
      techLineOk = {
        hasUnderline: cs.textDecorationLine.includes('underline') || techLine.className.includes('underline'),
        cursor: cs.cursor,
        colorAccentish: techLine.className.includes('text-accent-brand'),
        muted: techLine.className.includes('text-muted-foreground'),
      };
    }

    return {
      state,
      horizontalOverflow,
      stickyHeaderOpaque,
      nestedCards: nestedCards.length,
      nestedCardSamples: nestedCards.slice(0, 6),
      aboveFoldClickables,
      aboveFoldClickableCount: aboveFoldClickables.length,
      workbenchPreview,
      batchInfo,
      nextInfo,
      solidGrabStyles,
      testidsPresent: {
        batch: !!batch,
        next: !!next,
        workbench: !!workbench,
        sample: !!document.querySelector('[data-testid="try-sample-video-btn"]'),
        filmstrip: !!document.querySelector('[data-testid="micro-filmstrip-loupe"]'),
        engTable: !!document.querySelector('[data-testid="engineering-verification-table"]'),
        codec: !!document.querySelector('[data-testid="codec-compat-matrix"]'),
      },
      techLineOk,
      uniqueTestidCount: testids.length,
    };
  }, state);
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    channel: 'chrome',
    args: ['--disable-web-security', '--no-sandbox'],
  });
  const report = { base: BASE, kex: '0.2.3', viewports: {}, tdh: {} };

  // TDH via page
  {
    const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (compatible; KEX-QA/1.0)' });
    const page = await ctx.newPage();
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    const tdh = await page.evaluate(() => {
      const title = document.title;
      const h1 = document.querySelector('h1')?.textContent?.trim();
      const meta = document.querySelector('meta[name="description"]')?.getAttribute('content');
      return { title, h1, meta };
    });
    report.tdh = tdh;
    await ctx.close();
  }

  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      userAgent: 'Mozilla/5.0 (compatible; KEX-QA/1.0)',
    });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);
    await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForTimeout(1000);

    // Expand workbench to inspect static chips
    await page.evaluate(() => {
      const el = document.querySelector('[data-testid="ssr-workbench-controls"]');
      if (el) el.open = true;
    });
    await page.waitForTimeout(300);
    const empty = await kexMetrics(page, 'empty-expanded-workbench');

    // Collapse again for empty first-screen shot
    await page.evaluate(() => {
      const el = document.querySelector('[data-testid="ssr-workbench-controls"]');
      if (el) el.open = false;
    });
    await page.waitForTimeout(200);
    const emptyCollapsed = await kexMetrics(page, 'empty-collapsed');

    // Load sample video → active
    const sampleBtn = page.locator('[data-testid="try-sample-video-btn"]');
    await sampleBtn.scrollIntoViewIfNeeded();
    await sampleBtn.click();
    // wait for meta / video ready: grab button becomes real button
    try {
      await page.waitForSelector('button[data-testid="grab-and-download-frame"]', { timeout: 45000 });
      await page.waitForTimeout(1500);
    } catch (e) {
      // continue with whatever state
    }

    const activeBeforeGrab = await kexMetrics(page, 'active-before-grab');

    // Grab & Download to populate frames / next-steps
    const grab = page.locator('button[data-testid="grab-and-download-frame"]');
    if (await grab.count()) {
      await grab.first().click();
      await page.waitForTimeout(2000);
    }

    // wait for next-steps
    try {
      await page.waitForSelector('[data-testid="post-download-next-steps"]', { timeout: 15000 });
    } catch {}
    try {
      await page.waitForSelector('[data-testid="batch-contact-sheet-panel"]', { timeout: 5000 });
    } catch {}

    await page.waitForTimeout(500);
    const active = await kexMetrics(page, 'active-after-grab');

    // Screenshot active first screen (scroll to next-steps if needed for mobile evidence)
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(200);
    // Prefer shot that includes next-steps when present
    const next = page.locator('[data-testid="post-download-next-steps"]');
    if (await next.count()) {
      await next.scrollIntoViewIfNeeded();
      await page.waitForTimeout(200);
    }
    await page.screenshot({ path: vp.shot, fullPage: false });

    // Also empty first-screen shot variants
    const emptyShot = `/workspace/fe-pd-next-${vp.name}-empty-${vp.width}x${vp.height}.png`;
    // reload empty for clean empty shot
    await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForTimeout(600);
    await page.screenshot({ path: emptyShot, fullPage: false });

    report.viewports[vp.name] = {
      size: vp,
      emptyCollapsed,
      emptyExpandedWorkbench: empty,
      activeBeforeGrab,
      activeAfterGrab: active,
      screenshots: { nextFocus: vp.shot, empty: emptyShot },
    };
    await context.close();
  }

  await browser.close();
  fs.writeFileSync('/workspace/fe-e-verify-report.json', JSON.stringify(report, null, 2));

  // Pass/fail summary
  const summary = { pass: true, fails: [], notes: [] };
  const lockTitle = 'Video Frame Extractor - Free Online Video Frame Grabber';
  const lockH1 = 'Free Video Frame Extractor & Video Frame Grabber';
  if (report.tdh.title !== lockTitle) {
    summary.pass = false;
    summary.fails.push(`TITLE drift: ${report.tdh.title}`);
  }
  if (report.tdh.h1 !== lockH1) {
    summary.pass = false;
    summary.fails.push(`H1 drift: ${report.tdh.h1}`);
  }
  for (const vp of VIEWPORTS) {
    const v = report.viewports[vp.name];
    for (const key of ['emptyCollapsed', 'activeAfterGrab']) {
      const m = v[key];
      if (m.horizontalOverflow > 0) {
        summary.pass = false;
        summary.fails.push(`${vp.name}.${key}.horizontalOverflow=${m.horizontalOverflow}`);
      }
      if (m.nestedCards > 0) {
        summary.pass = false;
        summary.fails.push(`${vp.name}.${key}.nestedCards=${m.nestedCards}`);
      }
    }
    if (!v.activeAfterGrab.testidsPresent.next) {
      summary.pass = false;
      summary.fails.push(`${vp.name}: post-download-next-steps missing after grab`);
    }
    if (!v.activeAfterGrab.testidsPresent.batch) {
      summary.pass = false;
      summary.fails.push(`${vp.name}: batch-contact-sheet-panel missing after grab`);
    }
    if (!v.emptyExpandedWorkbench.workbenchPreview?.grabChipIsSpan) {
      summary.pass = false;
      summary.fails.push(`${vp.name}: empty grab chip not SPAN`);
    }
    if ((v.emptyExpandedWorkbench.workbenchPreview?.enabledButtons || 0) > 0) {
      summary.notes.push(
        `${vp.name}: workbench enabledButtons=${v.emptyExpandedWorkbench.workbenchPreview.enabledButtons}`
      );
    }
    if (v.emptyCollapsed.techLineOk && (v.emptyCollapsed.techLineOk.hasUnderline || v.emptyCollapsed.techLineOk.colorAccentish)) {
      summary.pass = false;
      summary.fails.push(`${vp.name}: Exact PTS line still looks like a link`);
    }
  }
  report.summary = summary;
  fs.writeFileSync('/workspace/fe-e-verify-report.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ tdh: report.tdh, summary, desktop: summarizeVp(report.viewports.desktop), mobile: summarizeVp(report.viewports.mobile) }, null, 2));
}

function summarizeVp(v) {
  if (!v) return null;
  return {
    empty: {
      overflow: v.emptyCollapsed.horizontalOverflow,
      nested: v.emptyCollapsed.nestedCards,
      sticky: v.emptyCollapsed.stickyHeaderOpaque,
      aboveFold: v.emptyCollapsed.aboveFoldClickableCount,
      chips: v.emptyExpandedWorkbench.workbenchPreview,
      tech: v.emptyCollapsed.techLineOk,
      testids: v.emptyCollapsed.testidsPresent,
    },
    active: {
      overflow: v.activeAfterGrab.horizontalOverflow,
      nested: v.activeAfterGrab.nestedCards,
      sticky: v.activeAfterGrab.stickyHeaderOpaque,
      batch: v.activeAfterGrab.batchInfo,
      next: v.activeAfterGrab.nextInfo,
      grab: v.activeAfterGrab.solidGrabStyles,
      testids: v.activeAfterGrab.testidsPresent,
    },
    shots: v.screenshots,
  };
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
