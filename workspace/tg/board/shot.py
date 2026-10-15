import sys, asyncio
from playwright.async_api import async_playwright
url, out, width = sys.argv[1], sys.argv[2], int(sys.argv[3])
groups = sys.argv[4].split(',') if len(sys.argv) > 4 else ['外卡交流频道', '「 东逆 」海外基建交流群']
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': width, 'height': 900}, device_scale_factor=2 if width < 600 else 1.5)
        await pg.goto(url + '#tg'); await pg.wait_for_selector('.br.tgw', timeout=20000)
        await pg.add_style_tag(content='header{position:static!important}')
        blk = pg.locator('.br.tgw', has_text='18:00–24:00').first
        for g in groups:
            await blk.locator('details.tgg', has_text=g).first.locator('summary').click()
        await pg.wait_for_timeout(300)
        await blk.scroll_into_view_if_needed()
        await blk.screenshot(path=out)
        await b.close()
asyncio.run(main())
