import asyncio, json
from playwright.async_api import async_playwright
U='http://127.0.0.1:18091/'; OUT='/workspace/xbm/'
async def main():
    res={}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        for w, mob, name in ((1280, False, 'tg_header_preview.png'), (390, True, 'tg_header_preview_mobile.png')):
            ctx = await b.new_context(viewport={'width': w, 'height': 900}, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob)
            pg = await ctx.new_page(); await pg.goto(U); await pg.fill('input[name=p]','pv'); await pg.click('button')
            await pg.wait_for_selector('#tabs button'); await pg.goto(U+'#tg'); await pg.wait_for_selector('.br.tgd')
            await pg.add_style_tag(content='header{position:static!important}')
            res[str(w)] = await pg.evaluate("""[...document.querySelectorAll('.br.tgd,.br.tgw')].map(c=>{const h=c.querySelector('.bh');const p=h.querySelector('.pill');
               return {hdr:h.textContent.replace(/\\s+/g,' ').trim(),h:Math.round(h.getBoundingClientRect().height),pillW:p?Math.round(p.getBoundingClientRect().width):null,
                 rows:c.querySelectorAll('details.tgg').length,zero:[...c.querySelectorAll('details.tgg .gc')].filter(x=>/^0\\s*条/.test(x.textContent)).length}})""")
            c = pg.locator('.br.tgw', has_text='18:00–24:00').first
            hb = await c.evaluate("e=>e.getBoundingClientRect().height")
            if not mob: await c.locator('.bh').hover()
            await pg.wait_for_timeout(200)
            res['hover_card_'+str(w)] = [hb, await c.evaluate("e=>e.getBoundingClientRect().height")]
            res['hov_overlap_'+str(w)] = await c.evaluate("e=>{const a=e.querySelector('.hov').getBoundingClientRect(),m=e.querySelector('.tgm').getBoundingClientRect();return Math.round(a.left-m.right)}")
            top = await pg.locator('.br.tgd').first.evaluate("e=>e.getBoundingClientRect().top+window.scrollY")
            # screenshot: daily header area + the 18-24 window card header + group list
            await c.evaluate("e=>e.querySelector('.cv.vtop')&&(e.querySelector('.cv.vtop').style.display='none')")  # only for screenshot compactness
            await pg.evaluate("document.querySelector('.br.tgd .cv').style.maxHeight='90px'")
            bb = await c.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY,h:r.height}}")
            await pg.screenshot(path=OUT+name, full_page=True, clip={'x':0,'y':max(0,top-10),'width':w,'height':min(bb['y']+bb['h']-top+20, 1800)})
            await ctx.close()
        await b.close()
    print(json.dumps(res, ensure_ascii=False, indent=1))
asyncio.run(main())
