#!/usr/bin/env python3
"""Turn a fetched window JSON into compact text for summarising (focus: SIM/eSIM, 美卡外卡, 银行开户/数字银行, U卡, VPS, 羊毛/链接).

  tg_prep.py data/2026-10-08/hourly/19.json [--group key] [--topic-budget 9000] [--other-budget 1200] [--max-chars 160]
  tg_prep.py --stats-only data/<date>/hourly/<HH>.json      # only (re)write the member stats file

Per group it prints: message/people totals, 热度 per topic category (messages / distinct people, bots excluded),
the most active members on these topics over the last 7 days of fetched data, then
  ### 话题消息  - every on-topic message (short ones too). Only if a busy group exceeds --topic-budget are
                 lines trimmed, and then only inside categories with more than 8 messages (rare topics are always kept).
  ### 其他消息  - highest-signal off-topic lines up to --other-budget (context only).
Line format:  HH:MM [话题] 发送者: 文本 [媒体] [↩︎被回复者: 摘要] 链接 <消息id> {类别}
Also writes data/<date>/hourly/<HH>.stats.json (per group, per sender: total and per-category counts).
"""
import argparse, glob, json, os, re, sys
from datetime import datetime, timedelta
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
from tg_topics import CATS, cats_of, is_bot

def stats_path(f):
    return f[:-5] + '.stats.json'

def member_stats(d):
    out = {}
    for g in d['groups']:
        s = out.setdefault(g['key'], {})
        for m in g['messages']:
            if is_bot(m) or not m.get('sender'): continue
            r = s.setdefault(m['sender'], {'n': 0, 'topic': 0, 'cats': {}})
            r['n'] += 1
            cs = cats_of(m.get('text') or '', m.get('urls'))
            cs = [c for c in cs if c != '羊毛链接'] or ([] if not cs else ['羊毛链接'])
            if cs: r['topic'] += 1
            for c in cs: r['cats'][c] = r['cats'].get(c, 0) + 1
    return out

def week_stats(date):
    """Sum hourly stats files of the last 7 days (date inclusive)."""
    d0 = datetime.strptime(date, '%Y-%m-%d'); agg, hours = {}, 0
    for i in range(7):
        day = (d0 - timedelta(days=i)).strftime('%Y-%m-%d')
        for p in glob.glob(os.path.join(BASE, 'data', day, 'hourly', '*.stats.json')):
            hours += 1
            for gk, ss in json.load(open(p)).items():
                ga = agg.setdefault(gk, {})
                for name, r in ss.items():
                    a = ga.setdefault(name, {'n': 0, 'topic': 0, 'cats': {}})
                    a['n'] += r['n']; a['topic'] += r['topic']
                    for c, n in r['cats'].items(): a['cats'][c] = a['cats'].get(c, 0) + n
    return agg, hours

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--group')
    ap.add_argument('--topic-budget', type=int, default=9000); ap.add_argument('--other-budget', type=int, default=1200)
    ap.add_argument('--max-chars', type=int, default=160); ap.add_argument('--stats-only', action='store_true')
    a = ap.parse_args()
    d = json.load(open(a.file)); w = d['window']
    if '/hourly/' in a.file:
        json.dump(member_stats(d), open(stats_path(a.file), 'w'), ensure_ascii=False)
    if a.stats_only: return
    week, hours = week_stats(w['date'])
    print(f"# 窗口 {w['date']} {w['label']}（{w['start']} ~ {w['end']}{'，进行中' if w.get('partial') else ''}）")
    print("> 先读 /workspace/tg/SUMMARY_RULES.md（只写群成员实际说的话、写出说话人、数字照原文、不加判断/警告/建议/标签）；"
          "专有名词拼写查 /workspace/tg/glossary.md，遇到新词追加进去。本文件是筛选稿：引用前用 tools/q.py 查原文，"
          "热度可用 `tools/q.py <win> 'regex' <group> --count` 精确统计。")
    print("> 类别：" + ' / '.join(CATS) + "（{类别} 为关键词自动标注，仅供参考）")
    for g in sorted(d['groups'], key=lambda g: g.get('order') or 999):
        if a.group and g['key'] != a.group: continue
        msgs = g['messages']
        replies = {}
        for m in msgs:
            if m.get('reply_to'): replies[m['reply_to']] = replies.get(m['reply_to'], 0) + 1
        people = {m['sender'] for m in msgs if m.get('sender') and not is_bot(m)}
        heat = {}
        topical, other, seen = [], [], {}
        for m in msgs:
            raw = (m['text'] or '').replace('\n', ' ⏎ ').strip()
            cs = cats_of(raw + ' ' + (m.get('media') or ''), m.get('urls'))
            bot = is_bot(m)
            if not bot:
                for c in cs:
                    h = heat.setdefault(c, [0, set()]); h[0] += 1; h[1].add(m.get('sender'))
            core = re.sub(r'\W', '', raw)
            if not cs and len(core) < 6: continue
            if cs and not core and not m.get('urls'): continue
            sig = core[:40]
            if sig and sig in seen:                       # repeated promos / copy-paste: keep first only
                seen[sig] += 1; continue
            seen[sig] = 1
            t = raw if len(raw) <= a.max_chars else raw[:a.max_chars] + '…'
            extra = []
            if m.get('fwd_from'): extra.append(f"[转发自 {m['fwd_from']}]")
            if m.get('reply_to_text'): extra.append(f"[↩︎{m['reply_to_text'][:40]}]")
            urls = [u for u in m.get('urls') or [] if u not in t]
            if urls: extra.append(' '.join(u[:90] for u in urls[:2]))
            topic = f"[{m['topic']}] " if m.get('topic') else ''
            who = (m['sender'] or '?')[:18] + ('(bot)' if bot else '')
            line = f"{m['time'][11:16]} {topic}{who}: {t} {' '.join(extra)} <{m['id']}>" + (f" {{{','.join(cs)}}}" if cs else '')
            score = min(len(core), 80) / 10 + 2 * bool(m.get('urls')) + 3 * replies.get(m['id'], 0) - (12 if bot else 0)
            (topical if cs else other).append({'id': m['id'], 'line': line, 'score': score, 'cats': cs, 'bot': bot})
        # trim topical only if over budget, never inside rare categories (<= 8 msgs)
        note = ''
        if sum(len(x['line']) for x in topical) > a.topic_budget:
            rare = {c for c, h in heat.items() if h[0] <= 8}
            keep = {x['id'] for x in topical if set(x['cats']) & rare and not x['bot']}
            used = sum(len(x['line']) for x in topical if x['id'] in keep)
            for x in sorted(topical, key=lambda x: -x['score']):
                if x['id'] in keep: continue
                if used + len(x['line']) > a.topic_budget: continue
                keep.add(x['id']); used += len(x['line'])
            note = f"（话题消息筛选：{len(keep)}/{len(topical)} 条；少于 8 条的类别全部保留）"
            topical = [x for x in topical if x['id'] in keep]
        keep_o, used = set(), 0
        for x in sorted(other, key=lambda x: -x['score']):
            if used + len(x['line']) > a.other_budget: continue
            keep_o.add(x['id']); used += len(x['line'])
        other = [x for x in other if x['id'] in keep_o]
        print(f"\n## [{g['key']}] {g['title']}（标签【{g.get('tag') or g['title']}】{'，频道' if g.get('type') == 'channel' else ''}{'，论坛话题群' if g.get('type') == 'forum' else ''}）"
              f" — 共 {g['count']} 条 / {len(people)} 人发言" + (f" — 错误: {g['error']}" if g.get('error') else ''))
        if heat:
            print('热度（本时段，条/人，不含机器人）：' + ' · '.join(f"{c} {h[0]}/{len(h[1])}" for c, h in sorted(heat.items(), key=lambda x: -x[1][0])))
        act = sorted(((n, r) for n, r in week.get(g['key'], {}).items() if r['topic']), key=lambda x: -x[1]['topic'])[:6]
        if act:
            print(f"话题活跃成员（近 7 天已抓取 {hours} 个小时文件，话题消息数）：" + '；'.join(
                f"{n} {r['topic']}（" + '、'.join(f'{c}{k}' for c, k in sorted(r['cats'].items(), key=lambda x: -x[1])[:3]) + '）' for n, r in act))
        if msgs: print(f"(链接 {msgs[0]['link'].rsplit('/', 1)[0]}/<id>)")
        if topical: print(f"### 话题消息{note}"); [print(x['line']) for x in topical]
        if other: print('### 其他消息（节选）'); [print(x['line']) for x in other]

if __name__ == '__main__':
    main()
