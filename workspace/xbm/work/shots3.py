import asyncio, json
from playwright.async_api import async_playwright
U='http://127.0.0.1:18091/'; OUT='/workspace/xbm/'
async def main():
    res={}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        for w, mob, name in ((1280, False, 'tg_order_preview.png'), (390, True, 'tg_order_preview_mobile.png')):
            ctx = await b.new_context(viewport={'width': w, 'height': 900}, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob)
            pg = await ctx.new_page(); await pg.goto(U); await pg.fill('input[name=p]','pv'); await pg.click('button')
            await pg.wait_for_selector('#tabs button'); await pg.goto(U+'#tg'); await pg.wait_for_selector('.br.tgd')
            await pg.add_style_tag(content='header{position:static!important}')
            d = pg.locator('.br.tgd').first
            res['daily_first_child_'+str(w)] = await d.evaluate("e=>{const c=e.querySelector('.cv');return c.firstElementChild.className+' | '+c.firstElementChild.textContent.slice(0,30)}")
            res['daily_order_ok_'+str(w)] = await d.evaluate("""e=>{let bad=0,n=0;let tp=null,last=null;for(const el of e.querySelectorAll('.cv>*')){if(el.classList.contains('tp')||el.classList.contains('sh')||el.classList.contains('hr')){last=null;continue}
              if(el.classList.contains('sp')){const t=(el.querySelector('.st').title||'').slice(0,19);if(!t)continue;n++;if(last&&t>last)bad++;last=t}}return {rows:n,violations:bad}}""")
            blk = pg.locator('.br.tgw', has_text='18:00–24:00').first
            res['win_vtop_'+str(w)] = await blk.evaluate("e=>{const v=e.querySelector('.cv.vtop');return v?[v.querySelectorAll('.vi').length, v.compareDocumentPosition(e.querySelector('details.tgg'))&4?'before groups':'after']:null}")
            res['win_vtop_times_'+str(w)] = await blk.evaluate("e=>[...e.querySelectorAll('.cv.vtop .vt')].map(x=>x.textContent)")
            row = d.locator('.cv .sp').nth(1); hb = await row.evaluate("e=>e.getBoundingClientRect().height")
            if not mob: await row.hover()
            await pg.wait_for_timeout(200); ha = await row.evaluate("e=>e.getBoundingClientRect().height")
            res['hover_h_'+str(w)] = [hb, ha]
            res['copy_starts_'+str(w)] = await pg.evaluate("untok(GX['g0']).slice(0,24)")
            bb = await d.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY}}")
            await pg.screenshot(path=OUT+name, full_page=True, clip={'x':0,'y':max(0,bb['y']-8),'width':w,'height':900 if not mob else 1000})
            if not mob:
                await blk.scroll_into_view_if_needed()
                bb = await blk.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY}}")
                await pg.screenshot(path=OUT+'tg_order_preview_window.png', full_page=True, clip={'x':0,'y':max(0,bb['y']-8),'width':w,'height':520})
            await ctx.close()
        await b.close()
    print(json.dumps(res, ensure_ascii=False, indent=1))
asyncio.run(main())
