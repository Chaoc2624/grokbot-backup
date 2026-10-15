import asyncio, json
from playwright.async_api import async_playwright
U='http://127.0.0.1:18091/'
OUT='/workspace/xbm/'
async def page(b, w, mobile=False):
    ctx = await b.new_context(viewport={'width': w, 'height': 900}, device_scale_factor=2 if mobile else 1, has_touch=mobile, is_mobile=mobile)
    pg = await ctx.new_page()
    await pg.goto(U); await pg.fill('input[name=p]', 'pv'); await pg.click('button')
    await pg.wait_for_selector('#tabs button')
    return pg
async def main():
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        # --- brief tab (default landing)
        for w, mob, name in ((1280, False, 'brief_tab_preview.png'), (390, True, 'brief_tab_preview_mobile.png')):
            pg = await page(b, w, mob); await pg.wait_for_selector('.br.latest')
            res['landing_hash_'+str(w)] = await pg.evaluate("location.hash||'(none)'")
            res['tabs_'+str(w)] = await pg.evaluate("[...document.querySelectorAll('#tabs button')].map(x=>x.textContent+(x.classList.contains('on')?'*':''))")
            res['nav_has_brief'] = await pg.evaluate("document.querySelector('#nav').textContent.includes('每日简报')")
            await pg.screenshot(path=OUT+name, clip={'x':0,'y':0,'width':w,'height':1100 if not mob else 1300})
            await pg.goto(U+'#briefs'); await pg.reload(); await pg.wait_for_selector('.br.latest')
            res['old_hash_ok_'+str(w)] = await pg.evaluate("document.querySelector('#tabs .on').textContent")
            await pg.context.close()
        # --- TG tab
        for w, mob, name in ((1280, False, 'tg_names_preview.png'), (390, True, 'tg_names_preview_mobile.png')):
            pg = await page(b, w, mob)
            await pg.goto(U+'#tg'); await pg.wait_for_selector('.br.tgw')
            await pg.add_style_tag(content='header{position:static!important}')
            blk = pg.locator('.br.tgw', has_text='18:00–24:00').first
            for g in ('外卡交流频道', '东逆薅毛大队', '【海无方】美卡交流群'):
                s = blk.locator('details.tgg', has_text=g).first.locator('summary')
                if await s.count(): await s.click()
            await pg.wait_for_timeout(300)
            row = blk.locator('.cv .sp', has=pg.locator('.st[title]')).nth(2)
            await row.scroll_into_view_if_needed()
            before = await row.evaluate("e=>{const r=e.getBoundingClientRect();return [r.width,r.height]}")
            vis_b = await row.evaluate("e=>getComputedStyle(e.querySelector('.st')).visibility")
            if mob: await row.locator('.tx').click(position={'x':5,'y':5})
            else: await row.hover()
            await pg.wait_for_timeout(250)
            after = await row.evaluate("e=>{const r=e.getBoundingClientRect();return [r.width,r.height]}")
            vis_a = await row.evaluate("e=>getComputedStyle(e.querySelector('.st')).visibility")
            st = await row.evaluate("e=>[e.querySelector('.st').textContent,e.querySelector('.st').title,e.querySelector('.nm').textContent]")
            res['tg_row_'+str(w)] = {'before': before, 'after': after, 'vis': [vis_b, vis_a], 'time': st}
            # all rows heights unchanged when hovering each? sample 30 rows
            res['tg_names_'+str(w)] = await blk.evaluate("e=>[...e.querySelectorAll('.cv .sp .nm')].slice(0,12).map(n=>[n.textContent,getComputedStyle(n).textAlign,n.scrollWidth>n.clientWidth])")
            bb = await row.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY}}")
            await pg.screenshot(path=OUT+name, full_page=True, clip={'x':0,'y':max(0,bb['y']-380),'width':w,'height':760})
            await pg.context.close()
        # --- bookmark cards
        for w, mob, name in ((1280, False, 'urgency_preview.png'), (390, True, 'urgency_preview_mobile.png')):
            pg = await page(b, w, mob)
            await pg.goto(U+'#open'); await pg.wait_for_selector('.card')
            await pg.add_style_tag(content='header{position:static!important}')
            cards = pg.locator('.card')
            c = cards.nth(1)
            before = await c.evaluate("e=>{const r=e.getBoundingClientRect();return [r.width,r.height]}")
            if mob: await c.locator('.t').click()
            else: await c.hover()
            await pg.wait_for_timeout(300)
            after = await c.evaluate("e=>{const r=e.getBoundingClientRect();return [r.width,r.height]}")
            res['card_'+str(w)] = {'before': before, 'after': after,
               'acts': await c.evaluate("e=>[...e.querySelectorAll('.acts button')].map(b=>b.textContent+' ['+b.title+']')"),
               'border_left': await c.evaluate("e=>getComputedStyle(e).borderLeftWidth+' '+getComputedStyle(e).borderLeftColor"),
               'acts_scroll': await c.evaluate("e=>{const a=e.querySelector('.acts');return [a.scrollWidth,a.clientWidth]}")}
            if mob:
                bb = await c.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY,h:r.height}}")
                await pg.screenshot(path=OUT+name, full_page=True, clip={'x':0,'y':max(0,bb['y']-12),'width':w,'height':bb['h']+24})
            else:
                await pg.screenshot(path=OUT+name, clip={'x':0,'y':0,'width':w,'height':1000})
            await pg.context.close()
        await b.close()
    print(json.dumps(res, ensure_ascii=False, indent=1))
asyncio.run(main())
