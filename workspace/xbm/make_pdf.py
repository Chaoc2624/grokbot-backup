#!/usr/bin/env python3
"""Render an X bookmark daily brief: make_pdf.py brief.json out.pdf
brief.json = {"title":..., "subtitle":..., "sections":[{"name":..., "items":[{"tag":..., "title":..., "need":..., "action":..., "deadline":..., "url":..., "posted_at"?: "10-05 21:30", "remind"?: "第3次提醒"}], "cls"?: "carry"}], "notes":[...], "board"?: url}"""
import json, sys, html, subprocess, os
b = json.load(open(sys.argv[1])); out = os.path.abspath(sys.argv[2])
e = html.escape
css = """body{font-family:'Noto Sans CJK SC','Noto Serif CJK SC',sans-serif;font-size:11pt;color:#222;margin:28px 34px}
h1{font-size:20pt;margin:0 0 4px}.sub{color:#666;font-size:9.5pt;margin-bottom:14px}
h2{font-size:13.5pt;margin:18px 0 8px;padding:4px 8px;border-radius:4px}
h2.s0{background:#fde2e1;color:#a11}h2.s1{background:#fff1d6;color:#8a5a00}h2.s2{background:#e3f0ff;color:#0b4f9c}h2.s3{background:#eee;color:#555}h2.carry{background:#ffe4e6;color:#9f1239;border:1px solid #fda4af}
.rm{display:inline-block;font-size:8.5pt;background:#fee2e2;color:#b91c1c;border-radius:3px;padding:0 5px;margin-left:6px}.board{font-size:9.5pt;margin:-8px 0 12px}
.it{border-left:3px solid #ccc;padding:4px 0 4px 10px;margin:0 0 10px;page-break-inside:avoid}
.t{font-weight:bold}.tag{display:inline-block;font-size:8.5pt;background:#333;color:#fff;border-radius:3px;padding:0 5px;margin-right:6px}
.dl{color:#c00;font-weight:bold}.k{color:#666}.posted{color:#666;font-size:9pt;margin-top:2px}a{color:#0b5cad;font-size:9pt;word-break:break-all}
ul{margin:4px 0 0 18px;padding:0}li{margin:2px 0}"""
h = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>",
     f"<h1>{e(b['title'])}</h1><div class='sub'>{e(b['subtitle'])}</div>"]
if b.get('board'): h.append(f"<div class='board'>在看板上标记完成、不紧急或忽略：<a href='{e(b['board'])}' style='font-size:9.5pt'>{e(b['board'])}</a></div>")
for i, s in enumerate(b['sections']):
    if not s['items']: continue
    cls = s.get('cls') or f"s{min(i,3)}"
    h.append(f"<h2 class='{cls}'>{e(s['name'])}（{len(s['items'])}）</h2>")
    for it in s['items']:
        h.append("<div class='it'>")
        h.append(f"<div class='t'>{('<span class=tag>'+e(it['tag'])+'</span>') if it.get('tag') else ''}{e(it['title'])}{('<span class=rm>'+e(it['remind'])+'</span>') if it.get('remind') else ''}</div>")
        if it.get('posted_at'): h.append(f"<div class='posted'>发于 {e(it['posted_at'])}</div>")
        if it.get('deadline'): h.append(f"<div class='dl'>⏰ {e(it['deadline'])}</div>")
        if it.get('need'): h.append(f"<div><span class='k'>需求：</span>{e(it['need'])}</div>")
        if it.get('action'): h.append(f"<div><span class='k'>建议：</span>{e(it['action'])}</div>")
        if it.get('url'): h.append(f"<a href='{e(it['url'])}'>{e(it['url'])}</a>")
        h.append("</div>")
if b.get('notes'):
    h.append("<h2 class='s3'>说明</h2><ul>" + "".join(f"<li>{e(n)}</li>" for n in b['notes']) + "</ul>")
h.append("</body></html>")
open('/tmp/xbm_brief.html', 'w').write("\n".join(h))
subprocess.run(['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                f'--print-to-pdf={out}', 'file:///tmp/xbm_brief.html'], check=True, capture_output=True)
print(out)
