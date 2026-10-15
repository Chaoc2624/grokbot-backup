#!/usr/bin/env python3
"""Ordering + 「涉及商家」 chips for chat-format digest content (shared by mkfrag / addtimes / tg_merge6h /
tg_digest_push / xbm tg_pull_summary). Rules (user, 2026-10-09):
  * newest first: hour sections ('**HH:MM–HH:MM**') newest first; inside an hour (or a daily '## 大类') topics
    newest first by their latest speech-line time; '### 零星消息' stays last; untimed topics after timed ones.
  * inside a topic: speech lines oldest first (by the {{time}} token; lines without a token keep their slot).
  * right under each topic heading: '~ 涉及商家：A · B · C' = merchants / platforms / banks / carriers / cards named
    in that topic's speech lines, in order of first mention (lexicon = glossary.md backticked names + a small
    supplement; display = glossary spelling). Recomputed every time; never hand-written.
  * '~ 话题活跃成员…' meta lines move to the end of their hour section; 网上核验 blocks go to the very end.

  tools/order.py FILE.json [...]        reorder items[].content in place (digest / pull-summary files)
  tools/order.py --check FILE.json      print what would change, don't write
"""
import json, os, re, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOSSARY = os.path.join(BASE, 'glossary.md')

TOKEN = re.compile(r'\{\{\s*([^{}\n]{4,40}?)\s*\}\}\s*$')
DIV = re.compile(r'^\*\*(\d{1,2}):(\d{2})\s*[–-]\s*\d{1,2}:\d{2}\*\*$')
TOPIC = re.compile(r'^###\s+')
SEC = re.compile(r'^#{1,2}\s+')
VH = re.compile(r'^#{1,4}\s+.*网上核验')
SPEECH = re.compile(r'^>\s*([^：:\n]{1,40}?)\s*[：:]\s*(.*)$')
CHIP = re.compile(r'^~\s*涉及商家[：:]')
ACTIVE = re.compile(r'^~\s*话题活跃成员')
ZERO = re.compile(r'^###\s+零星消息')

# ---------------- time keys ----------------
def tkey(line):
    m = TOKEN.search(line.strip())
    if not m: return ''
    r = re.match(r'^(?:(\d{4}-\d\d-\d\d)[ T])?(\d{1,2}:\d\d(?::\d\d)?)', m.group(1).strip())
    if not r: return ''
    t = r.group(2)
    if t.count(':') == 1: t += ':00'
    return (r.group(1) or '0000-00-00') + ' ' + t.zfill(8)

# ---------------- merchant lexicon ----------------
ALIASES = {   # canonical (glossary spelling) -> extra spellings members use
    'Kraken': ['krak', '海妖', 'kraken'], 'Starryblu': ['stb', 'starryblu'], 'Capital One': ['c1', 'capital one', 'capito one'],
    '万里汇': ['万里汇', 'worldfirst'], 'MEXC': ['mexc', '抹茶'], 'OKX': ['okx', '欧易'], 'Binance': ['binance', '币安'],
    'Bitget Wallet': ['bgw', 'bitget wallet'], 'Amex': ['amex', '运通'], 'Citi': ['citi', '花旗'], '汇丰': ['汇丰', 'hsbc', '滙豐'],
    'ZA Bank': ['za bank', 'zabank', '众安'], 'Airstar': ['airstar', '天星'], 'IBKR': ['ibkr', '盈透'], '嘉信': ['嘉信', 'schwab'],
    '工银亚洲': ['工亚', '工银亚洲'], 'TD': ['TD', '道明'], 'SmarTone': ['smartone', '数码通'], 'Shadowrocket': ['shadowrocket', '小火箭'],
    'Kikoff': ['kikoff', 'kickoff'], 'Vodafone': ['vodafone', '沃达丰'], 'GreenCloud': ['greencloud', '绿云'], '甲骨文': ['甲骨文', 'oracle'],
    '搬瓦工': ['搬瓦工', 'bandwagonhost', 'bandwagon'], 'dtcpay': ['dtcpay', 'dtc'], 'TNG': ['tng', "touch 'n go"], 'iFAST': ['ifast', '奕丰'],
    'PayPal': ['paypal'], 'Apple Pay': ['apple pay', 'applepay'], 'Google Pay': ['google pay'], 'N26': ['n26'], 'Coinbase': ['coinbase'],
    'Mastercard': ['mastercard', '万事达'], 'Visa': ['visa'], 'WeChat': ['wechat', '微信'], '支付宝': ['支付宝', 'alipay'],
    'Plasma One': ['plasma one', 'plasma'], 'ether.fi': ['ether.fi', 'etherfi'], 'T-Mobile': ['t-mobile', 'tmobile'], 'Wi-Fi': [],
    'Bitget': ['bitget'], 'Gate': ['Gate', 'gate.io'], 'Gate Money': ['gate money'], 'Starling': ['starling'], 'Monzo': ['monzo'],
    'Lebara': ['lebara'], 'VOXI': ['voxi'], 'CMSG': ['cmsg'], 'CMHK': ['cmhk'], 'cmuk': ['cmuk'], 'Wise': ['wise'],
    'ChatGPT': ['chatgpt'], 'Claude': ['claude'], 'Telegram Premium': ['telegram premium', 'tg会员'], '中国移动': ['中国移动'],
    'Lava': ['lava'], '星展 DBS': ['星展', 'dbs'], 'Simba': ['simba'], 'Saily': ['saily'], 'Maxx': ['maxx'],
}
SUPPLEMENT = ['dtcpay', 'Trust Bank', 'Eight', 'Simba', 'TNG', 'Gate Money', 'Coinbase', 'Egern', 'Visa', 'Mastercard', '银联',
              'Apple Pay', 'Google Pay', 'WeChat', '支付宝', 'ChatGPT', 'Claude', 'Telegram Premium', '中国移动', 'Revolut', 'Wise', 'Payy']
EXCLUDE = {x.lower() for x in [
    'eSIM', 'Wi-Fi Calling', 'Wi-Fi', 'VoLTE', '保号', '办电', '接码', 'ITIN', 'SSN', 'KYC', 'USDT', 'USDC', 'PYUSD', 'C2C', 'refer', 'DD',
    'FPS', '转数快', 'EP', 'S Pass', 'WP', 'MOM', 'BIR', 'TIN', 'NIN', 'BVN', 'CMRA', 'CIFAS', '5/24', 'titm', '3X-UI', 'FTTR', 'natmap',
    'natter', 'CGNAT', 'CN2 GIA', 'IPLC', 'IEPL', '9929', '4837', 'CMI', 'BGP', '家宽', '原生 IP', '机场', 'anyTLS', 'Xray', 'Reality',
    'Hysteria2', 'sing-box', '回环地址', 'VF NL', '卡bin', 'P1', 'p卡', 'credit builder loan', 'Bridge', 'Singpass', 'SGWorkPass', 'Wi-Fi Calling',
    'D', 'Y', 'sec', 'True', 'Smart', 'Three', 'Infinite', 'Platinum', '正确写法']}
KEEP_EXACT_CASE = {'Rain', 'Velo', 'Morse', 'Eight', 'Gate', 'TD', 'EE', 'M1', 'O2', 'AIS', 'CSL', 'CTM', 'BOA', 'FSM'}
_LEX = None

def _glossary_terms():
    terms, sec = [], ''
    try: txt = open(GLOSSARY, encoding='utf-8').read()
    except OSError: return terms
    for line in txt.split('\n'):
        if line.startswith('## '): sec = line; continue
        if '群（key' in sec or '常见成员' in sec or re.match(r'^-\s*成员', line.strip()): continue
        for t in re.findall(r'`([^`\n]{1,30})`', line):
            for part in re.split(r'\s*/\s*', t):
                part = part.strip()
                if part and not re.fullmatch(r'[\d\s/.%-]+', part): terms.append(part)
    return terms

def lexicon():
    """[(compiled regex, canonical)] longest spelling first."""
    global _LEX
    if _LEX is not None: return _LEX
    spell = {}                                         # spelling -> canonical
    canon_of = {a.lower(): c for c, al in ALIASES.items() for a in al}
    for t in _glossary_terms() + SUPPLEMENT:
        if t.lower() in EXCLUDE and t not in KEEP_EXACT_CASE: continue
        c = canon_of.get(t.lower(), t)
        spell.setdefault(t, c)
    for c, al in ALIASES.items():
        for a in al: spell.setdefault(a, c)
    out = []
    for s, c in sorted(spell.items(), key=lambda kv: -len(kv[0])):
        if c.lower() in EXCLUDE and c not in KEEP_EXACT_CASE: continue
        if len(s) < 2 and not re.search(r'[^\x00-\x7f]', s): continue
        e = re.escape(s).replace(r'\ ', r'\s?')
        if re.search(r'[A-Za-z0-9]', s[0]): e = r'(?<![A-Za-z0-9])' + e
        if re.search(r'[A-Za-z0-9]', s[-1]) and len(s) < 5: e = e + r'(?![A-Za-z0-9])'   # long names may be glued: WeChathk
        ascii_ = not re.search(r'[^\x00-\x7f]', s)
        exact = s in KEEP_EXACT_CASE or (ascii_ and len(s) <= 3 and s.lower() not in canon_of)
        out.append((re.compile(e, 0 if exact else re.I), c))
    _LEX = out
    return out

def _speech_text(line):
    m = SPEECH.match(line.strip())
    if not m: return ''
    t = TOKEN.sub('', m.group(2))
    t = re.sub(r'https?://\S+|【[^】]{1,24}】', ' ', t)
    return t.replace('==', '')

def merchants(lines):
    """Merchants named in these speech lines (already in display order), first mention first."""
    found = []
    for line in lines:
        t = _speech_text(line)
        if not t: continue
        hits, taken = [], []
        for rx, c in lexicon():
            for m in rx.finditer(t):
                a, b = m.span()
                if any(a < y and x < b for x, y in taken): continue
                taken.append((a, b)); hits.append((a, c))
        for _, c in sorted(hits):
            if c not in found: found.append(c)
    return found

# ---------------- reordering ----------------
def _sort_speech(body):
    idx = [i for i, l in enumerate(body) if l.lstrip().startswith('>') and SPEECH.match(l.strip())]
    timed = [i for i in idx if tkey(body[i])]
    vals = sorted((body[i] for i in timed), key=tkey)   # stable: equal keys keep written order
    out = list(body)
    for i, v in zip(timed, vals): out[i] = v
    return out

def _order_topics(lines, chips):
    """lines of one hour section / daily ## section (no dividers inside). Returns (lines, active_meta)."""
    pre, topics, active = [], [], []
    for l in lines:
        t = l.strip()
        if ACTIVE.match(t): active.append(l.rstrip()); continue
        if CHIP.match(t): continue
        if TOPIC.match(t): topics.append([l.rstrip()]); continue
        if not t: continue
        (topics[-1] if topics else pre).append(l.rstrip())
    done = []
    for k, tp in enumerate(topics):
        body = _sort_speech(tp[1:])
        if chips:
            ms = merchants(body)
            if ms: body = ['~ 涉及商家：' + ' · '.join(ms)] + body
        keys = [tkey(l) for l in body if tkey(l)]
        done.append((tp[0], body, max(keys) if keys else '', k))
    zero = [x for x in done if ZERO.match(x[0])]
    rest = [x for x in done if not ZERO.match(x[0])]
    timed = sorted([x for x in rest if x[2]], key=lambda x: (x[2], -x[3]), reverse=True)
    untimed = [x for x in rest if not x[2]]
    out = list(pre)
    for h, b, _, _ in timed + untimed + zero: out += [h] + b
    return out, active

def order_content(content, chips=True):
    if not content or re.fullmatch(r'\s*无重要内容\s*', content): return content
    lines = content.split('\n')
    # 1. pull out 网上核验 blocks (heading + its lines until the next boundary)
    body, verify, vhead, inv = [], [], None, False
    for l in lines:
        t = l.strip()
        if VH.match(t): inv = True; vhead = vhead or t; continue
        if inv:
            if DIV.match(t) or SEC.match(t) or TOPIC.match(t): inv = False
            else:
                if t: verify.append(t)
                continue
        body.append(l)
    # 2. split into hour sections
    secs, cur = [], {'div': None, 'lines': []}
    for l in body:
        if DIV.match(l.strip()):
            secs.append(cur); cur = {'div': l.strip(), 'lines': []}
        else: cur['lines'].append(l)
    secs.append(cur)
    head = secs[0]; hours = [s for s in secs[1:]]
    def do_section(ls):
        # daily: '## 大类' subsections keep their order; topics sorted inside each
        parts, cur2 = [], []
        for l in ls:
            if SEC.match(l.strip()) and not TOPIC.match(l.strip()) and not VH.match(l.strip()):
                parts.append(cur2); cur2 = [l.rstrip()]
            else: cur2.append(l)
        parts.append(cur2)
        out, act = [], []
        for p in parts:
            if not p: continue
            h = [p[0]] if p and SEC.match(p[0].strip()) else []
            o, a = _order_topics(p[len(h):], chips); act += a
            if h or o: out.append('\n'.join(h + o))
        txt = '\n\n'.join(x for x in out if x.strip()) if any(SEC.match(x.strip()) for x in ls) else '\n'.join(out)
        if act: txt = (txt + '\n' if txt else '') + '\n'.join(dict.fromkeys(act))
        return txt
    blocks = []
    h0 = do_section(head['lines'])
    if h0.strip(): blocks.append(h0)
    def hkey(s):
        m = DIV.match(s['div']); return int(m.group(1)) * 60 + int(m.group(2))
    for s in sorted(hours, key=hkey, reverse=True):
        blocks.append(s['div'] + ('\n' + do_section(s['lines']) if any(x.strip() for x in s['lines']) else ''))
    out = '\n\n'.join(blocks).strip()
    if verify:
        out += '\n\n' + (vhead or '#### 🔎 网上核验（外部公开来源，不是群友发言）') + '\n' + '\n'.join(verify)
    return out

def order_doc(d, chips=True):
    changed = 0
    for it in d.get('items', []):
        c = it.get('content')
        if isinstance(c, str):
            n = order_content(c, chips)
            if n != c: it['content'] = n; changed += 1
    if isinstance(d.get('overview'), str) and d['overview'].strip():
        n = order_content(d['overview'], chips)
        if n != d['overview']: d['overview'] = n; changed += 1
    return changed

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args: sys.exit(__doc__)
    for p in args:
        d = json.load(open(p)); n = order_doc(d)
        if '--check' not in sys.argv and n: json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
        print(p, f'{n} content(s) reordered' + (' (check only)' if '--check' in sys.argv else ''))
