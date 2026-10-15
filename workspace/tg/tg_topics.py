"""Shared topic keyword lists for tg_prep.py / tools/q.py (case-sensitive unless noted).
Add new brands/carriers/banks here (and in glossary.md)."""
import re
CATS = {
 'SIM': r'eSIM|esim|ESIM|SIM|[Ss]im卡|电话卡|手机卡|流量卡|号码|保号|接码|收码|验证码|漫游|流量|[Ww]i-?[Ff]i ?[Cc]all|wificall|wifi call|VoLTE|volte|副卡|携号|实名|套餐|月租|话费|充值卡'
        r'|giffgaff|Giffgaff|[Uu]ltra ?[Mm]obile|Tello|tello|Maxx|maxx|MAXX|CMHK|cmhk|香港移动|中国移动香港|CSL|csl|3HK|SmarTone|smartone|数码通|澳门电信|CTM|ctm|中国电信澳门'
        r'|[Cc]elcom|Singtel|singtel|StarHub|starhub|\bM1\b|[Gg]omo|GOMO|cmsg|CMSG|Vodafone|vodafone|\bO2\b|\bo2\b|\bEE\b|Lebara|lebara|VOXI|voxi|Lyca|lyca|T-Mobile|[Mm]int ?[Mm]obile|US Mobile|Google Fi|AT&T|Verizon'
        r'|Truphone|Airalo|airalo|xesim|[Dd]ito|DITO|Globe|AIS\b|True\b|dtac|Rakuten|povo|ahamo|1psim|红包卡|Kkday|kkday|Ting|Hello ?Mobile|Boost|Visible',
 '美卡外卡': r'美卡|外卡|信用卡|记账卡|借记卡|预付卡|\bC1\b|\bc1\b|Capital ?One|Capito|Discover|discover|Amex|amex|AMEX|运通|Chase|chase|BOA|BoA|Citi|花旗|ITIN|itin|SSN|ssn|信用分|养卡|下卡|批卡|开卡'
        r'|Apple Card|Apple Cash|Apple Pay|apple pay|\bAP\b|\bap\b|Google Pay|\bGP\b|万事达|Visa|visa|VISA|Master|master|卡bin|卡BIN|BIN\b|onepay|OnePay|Kikoff|kikoff|credit builder|loqbox|Loqbox|华美|Velo|refer',
 '银行开户': r'银行|开户|销户|关户|封户|港卡|汇丰|HSBC|hsbc|中银|BOC|渣打|星展|DBS|恒生|永隆|工银亚洲|大象|Airstar|众安|\bZA\b|ZA ?Bank|天星|Mox|\bmox\b|蚂蚁|富融|livi|WeLab|汇立|一卡通|金葵花'
        r'|[Mm]onzo|小马|Starling|starling|Lloyds|lloyds|lloy|劳埃德|Barclays|Zopa|zopa|\b212\b|Kroo|[Ll]em[Ff]i|N26|bunq|Revolut|revolut|[Ww]ise\b|WISE|ifast|iFAST|嘉信|Schwab|ibkr|IBKR|盈透|FSM|SoFi|[Ss]ofi|Mercury'
        r'|地址证明|账单|[Kk][Yy][Cc]|入金|出金|转账|汇款|换汇|万里汇|WorldFirst|worldfirst|PayPal|[Pp]aypal|\bpp\b|\bPP\b|Paysend|paysend|Plum|plum|[Ss]endwave|WorldRemit|worldRemit|Maya|maya|PDAX|[Pp]dax|GCash|gcash'
        r'|Altery|altery|[Yy]onder|[Zz]ilch|OCBC|[Ss]tarry[Bb]lu|\bstb\b|熊猫速汇|转数快|FPS|DD\b|直接存款|税号|税卡|BIR|TIN\b|NIN\b|\bnin\b|BVN|护照|签证|居留|准证|EP\b|S-?Pass|WP\b|singpass|Singpass',
 'U卡': r'[Uu] ?卡|USDT|usdt|USDC|usdc|PYUSD|pyusd|稳定币|币安|Binance|binance|OKX|okx|欧易|Bybit|bybit|Bitget|bitget|\bbgw\b|BGW|mexc|MEXC|抹茶|[Kk]raken|[Kk]rak\b|海妖|[Ii]nfini|KAST|[Kk]ast\b|[Pp]lasma'
        r'|[Ee]thena|\bena\b|[Ee]therfi|[Tt]uyo|[Rr]edot[Pp]ay|[Ss]afe[Pp]al|\be卡|\bp卡|\bP1\b|\bp1\b|[Nn]everless|Bridge|C2C|c2c|[Mm]ini[Pp]ay|minipay|Morse|[Pp]okepay|[Bb]lackcat|rain卡|企鹅卡|\bLava\b|\blava\b|BiyaPay|[Bb]iya|Xfers|Gate|gate|Coca|coca|Noah|dtcpay|Ether\.fi|[Cc]rypto\.com',
 'VPS': r'VPS|vps|家宽|机场|节点|线路|梯子|代理|IPLC|IEPL|CN2|cn2|GIA|9929|4837|CMI|BGP|CDN|服务器|独服|杜甫|DMIT|dmit|搬瓦工|[Bb]andwagon|\bbwg\b|BWG|Vultr|vultr|Linode|DigitalOcean|Hetzner|hetzner|OVH|RackNerd|racknerd|\bRN\b'
        r'|甲骨文|Oracle|AWS|Lightsail|GCP|Azure|Cloudflare|cloudflare|\bCF\b|补货|库存|缺货|限量|年付|月付|测速|延迟|丢包|带宽|原生IP|\bIP\b|\bip\b|解锁|Netflix|LowEndTalk|\bLET\b|hostloc|NodeSeek|nodeseek|\bNS\b|V2EX|v2ex'
        r'|Loon|loon|Surge|surge|Clash|clash|Shadowrocket|小火箭|Quantumult|\bQX\b|sing-?box|Xray|xray|Reality|reality|[Hh]ysteria|\bhy2\b|naive|tuic|WireGuard|wireguard|Tailscale|tailscale|DNS|dns|域名|SSL|面板|探针|Airrail|\baff\b|\bAFF\b',
 '羊毛链接': r'羊毛|薅|返现|返利|返佣|优惠|折扣|打折|活动|邀请码|邀请链接|白嫖|免费|奖励|bonus|Bonus|deal|Deal|promo|首单|开车|发车|车位|上车|拼车|领取|送\d|\d+ ?(刀|镑|欧|U|u|港币|HKD|USD|GBP|EUR)|£\d|\$\d|€\d',
}
RX = {k: re.compile(v, re.ASCII) for k, v in CATS.items()}   # ASCII: \b works next to CJK
BOT = re.compile(r'bot\b|Bot\b|BOT\b|_bot|Group ?Help|丫丫|AI_bot|东逆 Bot|TGBot', re.I)

def cats_of(text, urls=None):
    out = [k for k, r in RX.items() if r.search(text or '')]
    if urls and '羊毛链接' not in out: out.append('羊毛链接')
    return out

def is_bot(m):
    if 'sender_bot' in m:            # authoritative flag from Telegram (User.bot), recorded by tg_fetch.py
        return bool(m['sender_bot']) or bool(BOT.search(m.get('sender') or ''))
    # older data files without the flag: name/username heuristic
    return bool(BOT.search(m.get('sender') or '') or (m.get('sender_username') or '').lower().endswith('bot'))
