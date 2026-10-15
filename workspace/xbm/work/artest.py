import asyncio, json, urllib.request, copy
from playwright.async_api import async_playwright
U='http://127.0.0.1:18091/'; OUT='/workspace/xbm/'
def api(path, body=None, method=None):
    r=urllib.request.Request(U.rstrip('/')+path, data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None, method=method,
        headers={'Authorization':'Bearer pvtok','Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r))
async def main():
    res={}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        ctx = await b.new_context(viewport={'width':1280,'height':900})
        pg = await ctx.new_page(); await pg.goto(U); await pg.fill('input[name=p]','pv'); await pg.click('button')
        await pg.wait_for_selector('#tabs button')
        # ---- TG
        await pg.goto(U+'#tg'); await pg.wait_for_selector('.br.tgw'); await pg.wait_for_timeout(800)
        await pg.evaluate("poll()"); await pg.wait_for_timeout(300)
        blk = pg.locator('.br.tgw', has_text='18:00–24:00').first
        for g in ('外卡交流频道','【海无方】美卡交流群'):
            await blk.locator('details.tgg', has_text=g).first.locator('summary').click()
        # scroll so the 海无方 group rows are in view (外卡 rows above viewport)
        tgt = blk.locator('details.tgg', has_text='【海无方】美卡交流群').first.locator('.sp').nth(2)
        await tgt.evaluate("e=>window.scrollTo(0,e.getBoundingClientRect().top+scrollY-300)"); await pg.wait_for_timeout(300)
        before = await tgt.evaluate("e=>[e.textContent.slice(0,30),Math.round(e.getBoundingClientRect().top),scrollY]")
        opened_b = await pg.evaluate("[...document.querySelectorAll('#list details[open]')].length")
        # push changed 18-24 digest: two new rows at top of waika first topic (above viewport)
        d = api('/api/tg?date=2026-10-08&per=0')['days'][0]
        w = next(x for x in d['windows'] if x['window']=='18-24')
        items=[]
        for g in w['groups']:
            c=g['content']
            if g['grp']=='waika':
                i=c.index('\n> ')+1
                c=c[:i]+'> 测试员甲：自动刷新测试消息一 {{2026-10-08 18:59:58}}\n> 测试员乙：自动刷新测试消息二 {{2026-10-08 18:59:59}}\n'+c[i:]
            items.append({'group':g['grp'],'title':g['title'],'content':c,'msg_count':(g['msg_count'] or 0)+(2 if g['grp']=='waika' else 0)})
        api('/api/agent/tg',{'date':'2026-10-08','window':'18-24','partial':w['partial'],'win_start':w['win_start'],'win_end':w['win_end'],'replace':True,'items':items})
        await pg.evaluate("poll()"); await pg.wait_for_timeout(1200)
        after = await tgt.evaluate("e=>[e.textContent.slice(0,30),Math.round(e.getBoundingClientRect().top),scrollY]")
        res['tg'] = {'anchor_before':before,'anchor_after':after,'open_before':opened_b,
            'open_after':await pg.evaluate("[...document.querySelectorAll('#list details[open]')].length"),
            'pill':await pg.evaluate("[getComputedStyle(document.getElementById('npill')).display,document.getElementById('npill').textContent]"),
            'fresh':await pg.evaluate("[...document.querySelectorAll('.fresh')].map(e=>e.textContent.slice(0,20))")}
        await pg.screenshot(path=OUT+'autorefresh_preview.png', clip={'x':0,'y':0,'width':1280,'height':640})
        await pg.click('#npill'); await pg.wait_for_timeout(900)
        res['tg']['after_click'] = await pg.evaluate("(()=>{const e=[...document.querySelectorAll('.sp')].find(x=>x.textContent.includes('测试员乙'));const r=e.getBoundingClientRect();return [Math.round(r.top),getComputedStyle(document.getElementById('npill')).display]})()")
        # restore original 18-24
        api('/api/agent/tg',{'date':'2026-10-08','window':'18-24','partial':w['partial'],'win_start':w['win_start'],'win_end':w['win_end'],'replace':True,
             'items':[{'group':g['grp'],'title':g['title'],'content':g['content'],'msg_count':g['msg_count']} for g in w['groups']]})
        # busy skip: focus an input, change radar, poll -> no refresh
        # ---- bookmarks: ingest a test item; must not be marked read
        await pg.goto(U+'#urgent'); await pg.wait_for_selector('.card'); await pg.wait_for_timeout(500); await pg.evaluate("poll()"); await pg.wait_for_timeout(300)
        api('/api/agent/ingest',{'label':'自动刷新测试','items':[{'id':'ar-test-1','url':'https://x.com/a/status/1','title':'【测试】自动刷新新书签','tag':'测试','need':'n','action':'a','category':'urgent'}],'carried_ids':[]})
        await pg.evaluate("poll()"); await pg.wait_for_timeout(2500)
        res['bm'] = {'pill':await pg.evaluate("document.getElementById('npill').textContent+' / '+getComputedStyle(document.getElementById('npill')).display"),
            'card_present':await pg.evaluate("!!document.getElementById('car-test-1')")}
        await pg.screenshot(path=OUT+'autorefresh_preview_bm.png', clip={'x':0,'y':0,'width':1280,'height':500})
        # busy: focus search box then ingest another -> skipped
        await pg.focus('#q'); api('/api/agent/ingest',{'label':'自动刷新测试2','items':[{'id':'ar-test-2','title':'【测试】第二条','category':'urgent'}],'carried_ids':[]})
        await pg.evaluate("poll()"); await pg.wait_for_timeout(800)
        res['bm']['skipped_while_focused'] = await pg.evaluate("!document.getElementById('car-test-2')")
        await pg.evaluate("document.activeElement.blur()"); await pg.evaluate("poll()"); await pg.wait_for_timeout(1500)
        res['bm']['after_blur'] = await pg.evaluate("!!document.getElementById('car-test-2')")
        # ---- radar
        await pg.goto(U+'#new'); await pg.wait_for_selector('table.rt'); await pg.wait_for_timeout(500); await pg.evaluate("poll()"); await pg.wait_for_timeout(300)
        api('/api/agent/radar',{'label':'2026-10-08 自动刷新测试','run_at':'2026-10-08 22:00','items':[{'name':'TestProd','desc':'d','first_seen':'2026-10-08 21:50'}],'keywords':[]})
        await pg.evaluate("poll()"); await pg.wait_for_timeout(1500)
        res['radar_pill'] = await pg.evaluate("document.getElementById('npill').textContent+' / '+getComputedStyle(document.getElementById('npill')).display")
        # ---- visibility: hidden -> poll does nothing
        await ctx.close(); await b.close()
    import sqlite3
    c=sqlite3.connect('/workspace/xbm/work/preview.db')
    res['read_at_test_items']=c.execute("select id,read_at from items where id like 'ar-test-%'").fetchall()
    print(json.dumps(res,ensure_ascii=False,indent=1))
asyncio.run(main())
