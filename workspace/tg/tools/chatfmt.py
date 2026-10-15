"""Chat-style digest format helpers (shared by mkfrag.py, checkquotes.py, convert_chat.py).

Content / spec line types (one per line):
  **18:00–19:00**                 hour divider (added by tg_merge6h.py; don't write it in specs)
  ### 话题名 (11 条 / 4 人)        topic heading; counts optional; '### 零星消息' = the cold single-message list
  > 发言人：原话                    speech line, verbatim; several messages of the same person joined by ' · ';
                                   '…' marks trimmed text; ==关键词== marks a keyword (rendered as highlight)
  ~ 话题活跃成员（近 7 天话题消息）：A 34 · B 18      small muted meta line
  #### 🔎 网上核验 …  /  - 话题｜来源（日期）：来源怎么说 链接     web-verification block (external sources)
  ## 标题                          section heading (daily.json only)
"""
import re

SPEECH = re.compile(r'^>\s*([^：:\n]{1,40}?)\s*[：:]\s*(.*)$')
TOPIC = re.compile(r'^###\s+(.*?)\s*(?:[（(]\s*(\d+)\s*条\s*/\s*(\d+)\s*人\s*[)）])?\s*$')
MARK = re.compile(r'==([^=\n]{1,40}?)==')
TAG = re.compile(r'【[^】]{1,24}】')

_BRANDS = (
    r'eSIM|esim|ESIM|[Ww]i-?[Ff]i ?[Cc]alling|wificalling|VoLTE|红包卡|保号|接码'
    r'|giffgaff|Giffgaff|[Uu]ltra ?[Mm]obile|Tello|tello|Maxx|maxx|MAXX|CMHK|cmhk|CSL|csl|3HK|SmarTone|数码通|CTM'
    r'|[Cc]elcom|Singtel|singtel|StarHub|\bM1\b|[Gg]omo|GOMO|cmsg|CMSG|Vodafone|vodafone|\bO2\b|\bEE\b|Lebara|lebara|VOXI|voxi|Lyca|T-Mobile|[Mm]int ?[Mm]obile|US Mobile|Google Fi|AT&T|Verizon'
    r'|Airalo|xesim|[Dd]ito|DITO|DOTI|Globe|\bAIS\b|dtac|Rakuten|povo|ahamo|Saily|Truphone'
    r'|[Uu]卡|\bC1\b|\bc1\b|Capital ?One|Discover|Amex|AMEX|运通|Chase|chase|Citi|花旗|ITIN|itin|SSN|ssn|Apple Pay|apple pay|Google Pay|万事达|Visa|visa|VISA|Mastercard|MasterCard|master|银联|卡bin|卡BIN|Kikoff|loq|Loqbox'
    r'|汇丰|HSBC|hsbc|中银香港|中银|渣打|星展|DBS|恒生|工银亚洲|工亚|大象|Airstar|众安|ZA ?Bank|天星|Mox|蚂蚁银行|富融|livi|WeLab|汇立|Trust Bank|OCBC|Maybank|CIMB|信银国际'
    r'|[Mm]onzo|小马|Starling|Lloyds|lloyds|Barclays|Zopa|zopa|ZOPA|Kroo|N26|n26|bunq|Revolut|revolut|[Ww]ise\b|WISE|ifast|iFAST|嘉信|Schwab|IBKR|盈透|FSM|fsm|SoFi|Mercury'
    r'|万里汇|WorldFirst|PayPal|[Pp]aypal|Paysend|paysend|Plum|plum|[Ss]endwave|Maya|maya|GCash|PDAX|Altery|[Yy]onder|[Zz]ilch|[Ss]tarry[Bb]lu|\bstb\b|BIR|税卡|水卡|\bTIN\b|\bNIN\b|\bnin\b|singpass|Singpass|SGWorkPass'
    r'|USDT|USDC|PYUSD|币安|Binance|OKX|欧易|Bybit|Bitget|\bbgw\b|BGW|mexc|MEXC|Mexc|[Kk]raken|[Kk]rak\b|海妖|[Ii]nfini|KAST|[Kk]ast\b|[Pp]lasma ?[Oo]ne|[Ee]ther\.?fi|\be卡|[Tt]uyo|[Rr]edot[Pp]ay|[Mm]ini[Pp]ay|minipay'
    r'|BiyaPay|dtcpay|DTC|dtc|Coca|[Bb]itget|[Cc]rypto\.com|Lava\b|COINS|[Cc]oins\.ph'
    r'|VPS|vps|家宽|IPLC|IEPL|CN2|GIA|9929|CMIN2|DMIT|dmit|搬瓦工|[Bb]andwagon|Vultr|Hetzner|OVH|RackNerd|甲骨文|Oracle|DediOne|Cloudflare'
    r'|Loon|loon|Surge|Clash|Shadowrocket|小火箭|Egern|egern|anyTLS|Claude|claude|ChatGPT|GPT\b|Telegram ?Premium|TG ?会员|tg会员|@PremiumBot|WeChat|wechat'
)
_AMOUNT = (r'[£$€¥]\s?\d[\d,.]*(?:\s?[kKwW万])?'
           r'|\d[\d,.]*\s?(?:万|千|百)?\s?(?:刀|美金|美元|英镑|镑|磅|欧元|欧|港币|港元|HKD|hkd|USD|GBP|EUR|SGD|新币|RM|rm|PHP|php|人民币|CNY|cny|元|块|U\b|u\b|USDT|GB|G\b|T\b|分钟|mins?\b|%|％)')
HL = re.compile(r'(?:' + _AMOUNT + r')|(?:' + _BRANDS + r')', re.ASCII)


def autohl(text, cap=4):
    """Wrap keywords/amounts in ==…== (only if the text has no markers yet). Leaves URLs alone."""
    if MARK.search(re.sub(r'https?://\S+', '', text)):
        return text
    out, last, n = [], 0, 0
    urls = [m.span() for m in re.finditer(r'https?://\S+|【[^】]{1,24}】', text)]   # never inside links or 【群标签】
    seen = set()
    for m in HL.finditer(text):
        a, b = m.span()
        if any(x <= a < y for x, y in urls) or n >= cap:
            continue
        w = m.group(0).strip()
        if len(w) < 2 or w.lower() in seen:
            continue
        seen.add(w.lower())
        out.append(text[last:a]); out.append('==' + m.group(0) + '=='); last = b; n += 1
    out.append(text[last:])
    return ''.join(out)


def strip_marks(s):
    return MARK.sub(r'\1', s)


def canon(line, hl=True):
    """Canonicalise a spec line: speech lines -> '> 名：话' (auto-highlighted). Other lines unchanged."""
    m = SPEECH.match(line.strip())
    if m and line.lstrip().startswith('>'):
        name, text = m.group(1).strip(), m.group(2).strip()
        return f'> {name}：{autohl(text) if hl else text}'
    return line.rstrip()


def lint(line):
    """Return a warning string for lines that break the chat format, else None."""
    t = line.strip()
    if not t or t.startswith(('###', '~ ', '**', '#### ', '## ', '--- ')):
        return None
    if t.startswith('>'):
        if not SPEECH.match(t): return 'speech line without 名：'
        if '「' in t or '」' in t: return 'speech line contains 「」'
        return None
    return 'prose line (use "> 名：原话" speech lines)'
