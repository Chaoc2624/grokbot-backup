import { chromium } from 'playwright';
const BASE = process.env.PD_BASE || 'http://127.0.0.1:10121';
const browser = await chromium.launch({ headless: true });

async function shot(vp, path, scrollToDrawers=false) {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(600);
  if (scrollToDrawers) {
    await page.locator('[data-testid="ssr-workbench-controls"]').scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
  }
  await page.screenshot({ path, fullPage: false });
  await ctx.close();
}

await shot({ width: 1280, height: 800 }, '/workspace/fe-pd-desktop-1280x800.png', false);
await shot({ width: 390, height: 844 }, '/workspace/fe-pd-mobile-390x844.png', false);
await shot({ width: 1280, height: 800 }, '/workspace/fe-pd-desktop-drawers-1280x800.png', true);
await shot({ width: 390, height: 844 }, '/workspace/fe-pd-mobile-drawers-390x844.png', true);

// active sample state
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.getByTestId('try-sample-video-btn').click();
  await page.waitForSelector('[data-testid="grab-and-download-frame"]', { timeout: 20000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: '/workspace/fe-pd-active-desktop-1280x800.png', fullPage: false });
  // measure grab button + ffmpeg details
  const info = await page.evaluate(() => {
    const grab = document.querySelector('[data-testid="grab-and-download-frame"]');
    const ffmpeg = [...document.querySelectorAll('details')].find(d => (d.querySelector('summary')?.textContent||'').includes('Equivalent FFmpeg'));
    const gcs = grab ? getComputedStyle(grab) : null;
    const summary = ffmpeg?.querySelector(':scope > summary');
    const before = summary?.getBoundingClientRect();
    if (ffmpeg) ffmpeg.open = true;
    const after = summary?.getBoundingClientRect();
    return {
      grabVariantHint: gcs ? { bg: gcs.backgroundColor, color: gcs.color } : null,
      ffmpegDrift: before && after ? { dx: after.x - before.x, dw: after.width - before.width, h: after.height } : null,
      nestedCards: 0, // filled below
    };
  });
  // nested card count quick
  const nested = await page.evaluate(() => {
    const isCardish = (el) => {
      const cs = getComputedStyle(el);
      const bw = (parseFloat(cs.borderTopWidth)||0)+(parseFloat(cs.borderRightWidth)||0)+(parseFloat(cs.borderBottomWidth)||0)+(parseFloat(cs.borderLeftWidth)||0);
      const radius = Math.max(parseFloat(cs.borderTopLeftRadius)||0, parseFloat(cs.borderBottomLeftRadius)||0);
      const m = cs.backgroundColor.match(/rgba?\(([^)]+)\)/);
      let a = 0; if (m) { const p=m[1].split(',').map(s=>s.trim()); a=p.length===4?parseFloat(p[3]):1; }
      return bw>=3.5 && radius>=8 && a>0.05;
    };
    let n=0;
    for (const el of document.querySelectorAll('details,div,section')) {
      if (!isCardish(el)) continue;
      let p=el.parentElement;
      while (p && p!==document.body) {
        if (isCardish(p)) { n++; break; }
        p=p.parentElement;
      }
    }
    return n;
  });
  console.log(JSON.stringify({ ...info, nestedCards: nested }, null, 2));
  await ctx.close();
}

await browser.close();
console.log('shots saved');
