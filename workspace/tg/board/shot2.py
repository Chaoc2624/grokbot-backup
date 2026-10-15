import sys, asyncio
from playwright.async_api import async_playwright
url, out, width, maxh = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
groups = sys.argv[5].split(',')
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': width, 'height': 900}, device_scale_factor=2 if width < 600 else 1)
        await pg.goto(url + '#tg'); await pg.wait_for_selector('.br.tgw', timeout=20000)
        await pg.add_style_tag(content='header{position:static!important}')
        blk = pg.locator('.br.tgw', has_text='18:00–24:00').first
        for g in groups:
            await blk.locator('details.tgg', has_text=g).first.locator('summary').click()
        await pg.wait_for_timeout(300)
        bb = await blk.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY,height:r.height}}")
        await pg.screenshot(path=out, full_page=True, clip={'x': 0, 'y': max(0, bb['y'] - 16), 'width': width, 'height': min(bb['height'] + 32, maxh)})
        await b.close()
asyncio.run(main())
