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
        for w, mob, name in ():
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
            rows = blk.locator('.cv .sp')
            idx = await blk.evaluate("e=>[...e.querySelectorAll('.cv .sp')].findIndex(r=>{const n=r.querySelector('.nm');return n.scrollWidth>n.clientWidth+1})")
            row = rows.nth(max(idx, 1))
            await row.scroll_into_view_if_needed()
            geo = "e=>{const r=e.getBoundingClientRect();return [Math.round(r.width*100)/100,Math.round(r.height*100)/100]}"
            allh_b = await blk.evaluate("e=>[...e.querySelectorAll('.cv .sp')].map(r=>r.getBoundingClientRect().height)")
            before = await row.evaluate(geo)
            if not mob: await row.locator('.nm').hover()
            else: await row.locator('.tx').click(position={'x':5,'y':5})
            await pg.wait_for_timeout(250)
            after = await row.evaluate(geo)
            allh_a = await blk.evaluate("e=>[...e.querySelectorAll('.cv .sp')].map(r=>r.getBoundingClientRect().height)")
            res['tg_row_'+str(w)] = {'before': before, 'after': after, 'all_rows_same': allh_b == allh_a, 'n_rows': len(allh_b),
                'name': await row.evaluate("e=>[e.querySelector('.nm').textContent,getComputedStyle(e.querySelector('.nm')).width,getComputedStyle(e.querySelector('.nf')).visibility]"),
                'time': await row.evaluate("e=>[e.querySelector('.st').textContent,e.querySelector('.st').title,getComputedStyle(e.querySelector('.st')).visibility]"),
                'rows_with_time_visible': await blk.evaluate("e=>[...e.querySelectorAll('.cv .sp .st')].filter(s=>s.textContent&&s.offsetWidth&&getComputedStyle(s).visibility=='visible').length")}
            bb = await row.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY}}")
            await pg.screenshot(path=OUT+name, full_page=True, clip={'x':0,'y':max(0,bb['y']-300),'width':w,'height':640})
            await pg.context.close()
        # --- radar table
        for w, mob, name in ((1280, False, 'radar_table_preview.png'), (390, True, 'radar_table_preview_mobile.png')):
            pg = await page(b, w, mob)
            await pg.goto(U+'#new'); await pg.wait_for_selector('table.rt')
            await pg.add_style_tag(content='header{position:static!important}')
            box = pg.locator('.br', has_text='2026-10-08 中午').first
            await box.scroll_into_view_if_needed()
            res['radar_rows_'+str(w)] = await box.evaluate("e=>[...e.querySelectorAll('tr')].slice(1).map(t=>(t.classList.contains('kwr')?'KW ':'   ')+t.cells[0].textContent+' | '+t.cells[3].textContent+(t.querySelector('.sug')?' | '+t.querySelector('.sug').textContent.slice(0,20):''))")
            res['radar_kwl_gone'] = await pg.evaluate("document.querySelectorAll('.kwl').length==0")
            tr = box.locator('tr.kwr').first
            hb = await tr.evaluate("e=>e.getBoundingClientRect().height"); await tr.hover(); await pg.wait_for_timeout(150); ha = await tr.evaluate("e=>e.getBoundingClientRect().height")
            res['radar_hover_h_'+str(w)] = [hb, ha]
            bb = await box.evaluate("e=>{const r=e.getBoundingClientRect();return {y:r.top+window.scrollY,h:r.height}}")
            await pg.screenshot(path=OUT+name, full_page=True, clip={'x':0,'y':max(0,bb['y']-8),'width':w,'height':min(bb['h']+16, 1400)})
            res['radar_test_run'] = await pg.evaluate("fetch('api/radar?date=2026-10-01').then(r=>r.json()).then(d=>rRows({...d.runs[0],day:'2026-10-01'}).map(i=>(i.kw?'KW#'+i.rank+' ':'')+i.name+(i.only?' (no item)':'')+' '+(i.reason||'')))")
            res['hot_ok'] = await pg.evaluate("(async()=>{location.hash='hot';await new Promise(r=>setTimeout(r,800));return document.querySelectorAll('.rt tr').length})()")
            await pg.context.close()
        # --- bookmark cards
        for w, mob, name in ():
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
