#!/usr/bin/env python3
"""Helper for 「TG 拉取 → 助手总结」 (看板 https://x.omnitools.cc #tg).

  tg_pull_summary.py fetch  <job_id>            -> /workspace/xbm/tgpull/<job_id>-raw.json  (按群分组的全部原始消息：人名、HH:MM、正文、回复关系)
                                                  + <job_id>-raw.txt (紧凑文本，便于阅读) + <job_id>-summary.template.json (推送骨架)
  tg_pull_summary.py push   <job_id> file.json  -> 推总结（同一任务重复推会覆盖），状态置 done
         file.json = {"overview": "可选的总览 markdown",
                      "items": [{"grp": "群名", "chat_id": -100…, "from": "YYYY-MM-DD HH:MM", "to": "YYYY-MM-DD HH:MM",
                                 "msg_count": N, "content": "markdown（格式参考 tgpull/digest-sample.md）", "date": "可选，默认取 to 的日期"}]}
         push 前自动排序（/workspace/tg/tools/order.py）：话题新→旧、话题内发言旧→新、每个话题下加「~ 涉及商家：…」。
         看板每次拉取一张「📡 实时拉取」卡片（挂在任务结束那天），overview + 各群 item 全部显示在这张卡里；≤24 小时的拉取每群一条 item 即可，不必按小时/天拆。
  tg_pull_summary.py fail   <job_id> "原因"      -> 状态置 failed，页面显示原因和「重新总结」
  tg_pull_summary.py status <job_id>            -> 拉取状态 + 总结状态（none / pending / done / failed，超时）
  tg_pull_summary.py get    <job_id>            -> 已推送的总结
  tg_pull_summary.py reset  <job_id> [pending|none|failed]  -> 删除已推送的总结并设状态（默认 pending）
  tg_pull_summary.py retry  <job_id>            -> 让看板重新发 webhook
Token: ~/.xbm/board.env (XBM_API_TOKEN). Uses https://x.omnitools.cc, falls back to ssh root@192.255.151.85 -> 127.0.0.1:10091/board."""
import sys, json, os, subprocess, urllib.request, urllib.error
from urllib.parse import quote
env = dict(l.strip().split('=', 1) for l in open(os.path.expanduser('~/.xbm/board.env')) if '=' in l)
TOK = env['XBM_API_TOKEN']
OUT = '/workspace/xbm/tgpull'

def call(path, data=None, method=None):
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else None
    hdr = {'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json', 'User-Agent': 'xbm-client'}
    try:
        r = urllib.request.Request('https://x.omnitools.cc' + path, data=body, method=method, headers=hdr)
        return json.load(urllib.request.urlopen(r, timeout=30))
    except urllib.error.HTTPError as e:
        if e.code in (400, 401, 404, 409):                # real answer from the board: don't retry over ssh
            try: msg = json.load(e)
            except Exception: msg = {'error': 'HTTP %d' % e.code}
            sys.exit('board: HTTP %d %s' % (e.code, json.dumps(msg, ensure_ascii=False)))
    except Exception:
        pass
    cmd = ['ssh', '-o', 'ConnectTimeout=10', 'root@192.255.151.85',
           f"curl -sS {'-X ' + method + ' ' if method else ''}-H 'Authorization: Bearer {TOK}' -H 'Content-Type: application/json' "
           + ("--data-binary @- " if body else "") + f"'http://127.0.0.1:10091/board{path}'"]
    return json.loads(subprocess.run(cmd, input=body, capture_output=True, check=True).stdout)

def fetch(jid):
    msgs, off, meta = [], 0, None
    while True:
        d = call(f'/api/tg/pull/{quote(jid)}/raw?offset={off}&limit=2000')
        meta = meta or d; msgs += d['messages']; off += len(d['messages'])
        if not d['messages'] or off >= d['total']: break
    job = call(f'/api/tg/pull/{quote(jid)}').get('job') or {}
    multi = len({m['date'] for m in msgs}) > 1
    groups = []
    for g in meta['groups']:
        ms = [m for m in msgs if m['chat_id'] == g['chat_id']]
        idx = {m['msg_id']: m for m in ms}
        rows = []
        for m in ms:
            r = {'id': m['msg_id'], 't': m['hm'][:5], 'who': m['sender'] or '?', 'text': m['text'] or ''}
            if multi: r['d'] = m['date'][5:]
            if m.get('media'): r['media'] = m['media']
            if m.get('fwd'): r['fwd'] = m['fwd']
            if m.get('reply_to'):
                p = idx.get(m['reply_to'])
                r['re'] = {'id': m['reply_to'], 'who': p['sender'], 't': p['hm'][:5], 'text': (p['text'] or p.get('media') or '')[:80]} if p else {'id': m['reply_to']}
            if not m.get('new'): r['old'] = True             # stored by an earlier pull (still inside this job's range)
            r['link'] = m.get('link')
            rows.append(r)
        groups.append({'grp': g['title'], 'key': g['key'], 'chat_id': g['chat_id'], 'msg_count': len(rows),
                       'first': (ms[0]['date'] + ' ' + ms[0]['hm'][:5]) if ms else None, 'last': (ms[-1]['date'] + ' ' + ms[-1]['hm'][:5]) if ms else None,
                       'messages': rows})
    os.makedirs(OUT, exist_ok=True)
    out = {'job_id': jid, 'from': meta['from'], 'to': meta['to'], 'total': len(msgs), 'new_count': job.get('added'),
           'summary_status': (job.get('summary') or {}).get('status'), 'groups': groups}
    p = f'{OUT}/{jid}-raw.json'; json.dump(out, open(p, 'w'), ensure_ascii=False, indent=1)
    with open(f'{OUT}/{jid}-raw.txt', 'w') as f:
        f.write(f"# 拉取 {jid}：{meta['from']} – {meta['to']}（北京时间），共 {len(msgs)} 条\n")
        for g in groups:
            f.write(f"\n## {g['grp']}（{g['msg_count']} 条，{g['first'] or '-'} – {g['last'] or '-'}，chat_id {g['chat_id']}）\n")
            for r in g['messages']:
                ex = ''.join([f" [转发自 {r['fwd']}]" if r.get('fwd') else '', f" [{r['media']}]" if r.get('media') else '',
                              (f" [↩ {r['re']['who']} {r['re']['t']}：{r['re']['text']}]" if r.get('re', {}).get('who') else (f" [↩ #{r['re']['id']}]" if r.get('re') else ''))])
                body = ' '.join(x for x in (ex.strip(), r['text']) if x)
                f.write(f"{r.get('d', '') + ' ' if r.get('d') else ''}{r['t']} #{r['id']} {r['who']}：{body}".rstrip().replace('\n', ' ⏎ ') + '\n')
    tpl = {'overview': '', 'items': [{'grp': g['grp'], 'chat_id': g['chat_id'], 'from': g['first'], 'to': g['last'], 'msg_count': g['msg_count'], 'content': ''}
                                     for g in groups if g['msg_count']]}
    json.dump(tpl, open(f'{OUT}/{jid}-summary.template.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({'raw': p, 'text': f'{OUT}/{jid}-raw.txt', 'template': f'{OUT}/{jid}-summary.template.json', 'total': len(msgs),
                      'groups': {g['grp']: g['msg_count'] for g in groups}}, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    c, jid = sys.argv[1], sys.argv[2]; J = quote(jid)
    if c == 'fetch': fetch(jid)
    elif c == 'push':
        # enforce the ordering rules (SUMMARY_RULES.md 二·排序): topics newest first, speech lines oldest first,
        # '~ 涉及商家' chips under each topic; the file is rewritten so it matches what the board shows
        sys.path.insert(0, '/workspace/tg/tools'); from order import order_doc
        doc = json.load(open(sys.argv[3]))
        if order_doc(doc): json.dump(doc, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
        print(json.dumps(call(f'/api/tg/pull/{J}/summary', doc), ensure_ascii=False))
    elif c == 'fail': print(json.dumps(call(f'/api/tg/pull/{J}/summary/fail', {'error': ' '.join(sys.argv[3:]) or '总结失败'}), ensure_ascii=False))
    elif c == 'retry': print(json.dumps(call(f'/api/tg/pull/{J}/summary/retry', {}), ensure_ascii=False))
    elif c == 'get': print(json.dumps(call(f'/api/tg/pull/{J}/summary'), ensure_ascii=False, indent=1))
    elif c == 'reset': print(json.dumps(call(f'/api/tg/pull/{J}/summary?status=' + (sys.argv[3] if len(sys.argv) > 3 else 'pending'), method='DELETE'), ensure_ascii=False))
    elif c == 'status':
        j = call(f'/api/tg/pull/{J}').get('job') or {}
        s = j.get('summary') or {}
        print(json.dumps({'job_id': j.get('id'), 'pull_status': j.get('status'), 'from': j.get('since_bj'), 'to': j.get('until_bj'), 'fetched': j.get('fetched'),
                          'added': j.get('added'), 'summary': s}, ensure_ascii=False, indent=1))
    else: sys.exit(__doc__)
