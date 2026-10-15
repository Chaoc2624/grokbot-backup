import json
raw=json.load(open('bookmarks-raw.json'))
B=raw['bookmarks']
arts=json.load(open('articles.json'))
def t(i):
    s=B[i]['created_at_bjt']; return f"发于 {s[5:10]} {s[11:16]}"
def link(i): return B[i]['url']
cats=[
("A","🇺🇸 美卡 / ITIN / 美国银行与信用","ITIN 下号后的全链路：美国地址（ATMB、保单、Revolut 账单当地址证明）、首张美卡 C1、Nu/Majority/Revolut/SoFi 开户、Kikoff 建信用、开户奖励和 DD 羊毛。收藏里占比最大，属于正在推进的主线。",
 {14:"★ 美卡系列 02：筛了 300+ ATMB 地址，总结出四步验证法挑住宅地址（长文）",
  70:"★ ITIN 经验第 4 期：怎么检查美国地址质量（长文，可以和第 3 期连着看）",
  76:"ITIN 经验第 3 期：美国地址三种方案对比（朋友地址 / 代收 / ATMB）",
  63:"★ 不用 P 图：买一个月 State Farm 租客险（10~15 刀），保单当第一份地址证明（长文）",
  68:"用 Revolut 生成 Statement 当地址证明，解决先有鸡还是先有蛋的问题",
  9:"高赞：办美签→新泽西租房考驾照→线下跑 BOA/Amex/Chase/Citi/WF 开户的完整路线",
  20:"有 ITIN 的话，新泽西是最容易拿美国驾照的州之一（必须真实居住）",
  36:"C1 电话开卡：开着钉钉 AI 听记实时翻译，提前备好卡号、ITIN、地址",
  51:"Nu Bank US：ITIN 只刷脸就能开户，可选 2500 额度信用卡（开户后不能再补开）",
  60:"Majority：护照直接开户，押金卡建信用；入金 20 刀、30 天内 3 笔 >5 刀消费奖 20 刀",
  81:"Revolut 美区：押金信用卡（1.5% 返现）、4% 存款、美元/英镑账户",
  78:"有 ITIN 必注册：Credit Karma 和 SoFi，免费查信用分",
  66:"Equifax 1 美元看三大局信用报告，7 天试用",
  67:"新 ITIN（905 号段）用 Kikoff 循环信用 + 分期信用打破零信用",
  21:"Kikoff 会不会影响 C1 申请的讨论",
  77:"富国开户奖励 3 个工作日就到账（500/325 刀），从 IB 出金的普通 ACH 就满足 DD",
  8:"飞香港办恒生，用恒生入金 SoFi 也算 DD",
  19:"美卡进度：C1 推荐奖励 300 刀已拿到，SoFi 约 600 刀、Acorns 约 233 刀待做",
  11:"美区 PayPal Debit Card：提示无效 SSN 时，走买加密货币认证，上传护照 + ITIN",
  12:"★ Firstrade 资产满 2.5 万美元可申请 Visa 借记卡，不出国就能拿的正规美卡",
  6:"Rakuten 返利：注册美卡有额外奖励，邀请注册后消费 50 返 50",
  79:"Pangea 汇款到菲律宾 Maya，白送 20 刀（需要美卡、美号、Maya）",
  7:"求推荐千元左右的二手三星美版机，用来玩 Samsung Wallet"}),
("B","🌏 海外身份 / KYC：税号、签证、驾照、券商","第二身份材料：土耳其/意大利/泰国税号、泰国 DTV 和越南签证、内地驾照换香港驾照、菲律宾驾照，加上 IBKR、FSM HK 等券商开户和 CRS 规避。",
 {26:"★ 土耳其税号：只要护照，官网 3 分钟免费出号（附三个坑）",
  35:"意大利 Codice Fiscale：使领馆预约，免费办理",
  27:"泰国 TIN：必须本人到泰国税务局办，适合长居泰国的人",
  17:"泰国 DTV 签证（自己办 2 千多块，5 年多次）可以当 KYC 材料，Wise 已经认",
  23:"★ 内地驾照免试换香港驾照全流程（900 港币，材料齐全当天拿证）",
  18:"★ 换香港驾照最新预约攻略：必须网上预约，名额只放未来 4 周，每个工作日 17:00 更新",
  99:"越南电子签自己办：单次 25 美元、多次 50 美元",
  49:"菲律宾驾照代办（达沃当天往返，2300 元）",
  48:"wdknews 回本合集：ITIN、菲律宾税卡、NIN、各种驾照工签代办汇总",
  4:"★ IBKR 盈透开户：多个账户版的身份证明和地址证明组合，强调合规",
  82:"★ IBKR 规避 CRS：查有没有 U*****F 结尾的英国分公司账户，有的话发工单关掉",
  72:"FSM Global HK：只用内地身份证开户，港股 0 佣金，和 iFAST 银行资金互转（长文）",
  65:"想要嘉信借记卡，可以往马来西亚身份的路子上靠"}),
("C","📱 海外手机号 / eSIM / 保号接码","低成本保号卡（英国 Lyca、波兰 Play24、菲律宾 Smart、Tello、捷克 Kaktus、smarty），新加坡和香港流量卡，以及用 EC20 模组自建接码机。",
 {33:"★ 英国 Lyca：免实名、0 月租，国内免费接码，每年保号不到 1 英镑（长文）",
  2:"★ 不用 Singpass、大陆就能激活的新加坡漫游 eSIM：29 元/月 15G（长文）",
  39:"波兰 Play24：开卡 30 PLN，每年充 5 PLN 保号，需要 KYC 和欧洲卡支付",
  30:"波兰 Play eSIM 开卡步骤（文字版）",
  15:"Tello 保号别交 5 刀月费了，改充 PAYG credit（一次管 90 天）",
  62:"Tello 配小火箭分流，开着 VPN 也能收短信",
  54:"菲律宾 Smart eSIM：余额 ≥1 比索就能保号",
  50:"注册 Maya 需要菲律宾号：用 Smart eSIM 解决",
  52:"Smart App 里的 GigaPay 可以绑 Maya 给号码充值",
  32:"Google Voice 2026 年还能申请吗？保号要每 2~3 个月主动打一次电话",
  38:"捷克 Kaktus 免费卡已经没戏，官网可以开 eSIM",
  75:"smarty 邀请奖励：下个月续订 15£ 的套餐双方各得 20£",
  13:"香港卡在大陆上台：中国移动香港，24 个月合约，押金 1000 港币",
  57:"★ HiDeck：自托管的高通模组控制台（EC20 不到 100 元），收发短信、VoWiFi、eSIM 管理",
  58:"大疆 4G 模块平替：N1 刷 Armbian + EC20 在线管理多张 eSIM（长文）",
  31:"刷到的靓号晒图"}),
("D","💳 U 卡 / 非美国支付卡 / 返利羊毛","加密 U 卡（Bybit EU、Redotpay、Gate）、Gopay 虚拟卡、众安和 Monzo，以及 WorldRemit、SheerID 这类返现和认证羊毛。不少帖子带邀请码，属于推广，看的时候留意。",
 {28:"★ 德区 Bybit EU Card：有护照就能开，订阅 GPT 返现上限 50 欧（长文）",
  29:"春秋航空 Gopay 虚拟卡：美国卡 BIN，可以绑 Google Pay / Apple Pay（带邀请码）",
  73:"Gate U 卡国区和菲区对比，菲区卡可以直接用现货余额消费",
  47:"Redotpay U 卡推广（带邀请码）",
  74:"WorldRemit 通过 TopCashBack 返现 $63.63",
  16:"SheerID 认证有一波车，作者说可能会翻车",
  37:"免费领的黑色众安银行卡到手",
  46:"Monzo 和小马银行卡的邮件转寄接收"}),
("E","🛜 网络 / 科学上网 / 服务器与自托管","软路由、旁路由、Claude 防封分流规则、Pixel 内置 Google VPN、iOS 27 改定位新方案、甲骨文免费服务器，以及家庭网络监控、异地组网、远程唤醒电脑。",
 {1:"★ 软路由保姆级教程：NAS 或旧电脑装 OpenClash，全家连上 Wi-Fi 就能访问外网（长文）",
  3:"★ Claude 防封分流的完整域名规则（小火箭/Surge 配置）",
  61:"★ iOS 27 正式版下 WLOC+MITM 已失效，新的改定位方案（iLoader + SideStore，不用越狱）",
  43:"WLOC 基于 Roam Control 复活，可以用小火箭改定位",
  24:"白嫖 4C24G：甲骨文注册、升级 PAYG、创建实例的完整教程（长文）",
  25:"Pixel 在国内用 Google VPN（前置代理法）",
  42:"配了旁路由以后，家里国内 App 也不转圈了",
  59:"小火箭加一条规则，解决 Telegram 和 X 不弹通知的问题",
  93:"Neko Master：家庭网关流量实时可视化（开源）",
  85:"MeshLAN：开源的 Windows 虚拟局域网，P2P 优先，支持服务映射",
  80:"ESP32-S3 + MQTT 远程唤醒睡眠中的电脑"}),
("F","🚀 出海建站 / SEO / 选品","独立开发出海的方法论（选题、20 分钟建站、铺外链），外链资源和自动提交 Skill，竞品和流量工具，设计灵感库。",
 {41:"★ 14 年老 IT 裸辞出海：抓缝隙选题、20 分钟建站、狂铺外链（长文，3237 收藏）",
  84:"★ 选品方法汇总：抄对标、Product Hunt API、看 Stripe/Creem 付费率、GitHub Trending、看投流",
  95:"★ Backlink Skills（开源）：700+ 免费外链地址，用 Codex 自动提交",
  90:"外链渠道分享：DataForSEO、grok-cli 采集征集帖、外链榜",
  91:"中推导航站互相提交外链的征集帖",
  45:"AIsa GTM 引擎：一个 API Key 打通 Similarweb、Ahrefs、Semrush 等，39 美元按量付费（推广）",
  98:"design-dna：把参考网站的设计风格拆成 JSON，喂给 Codex 生成页面",
  89:"12 个设计灵感库（recent.design、lapa.ninja、land-book、awwwards 等）",
  87:"paywall-gallery：1000+ App 的付费墙截图库（开源）",
  86:"blobatar：4kb 的几何头像生成库",
  5:"出海和 SEO 值得关注的人：哥飞、Loki、子木等"}),
("G","🤖 AI 工具 / Agent / 开发效率","AI Agent 工作流（Codex 调 Grok、Grokbot 读书签做日报）、微信 CLI、剪映 Skill、知识库同步，以及 X Premium+ 价格、Cursor 漏洞这类讨论。",
 {10:"★ turingou：让 Grokbot 读完书签、按项目分类，再交给 Codex/Claude Code 自动评估（和你现在要做的事很像）",
  97:"★ Codex 调 Grok Build CLI 去 X 上搜技巧，附 skill",
  88:"微信 CLI + 微信个人情报库：总结 24 小时聊天、生成行动日报（作者说要开源）",
  55:"wx-cli 重新公开（作者说是限时开放；本地解密数据库有风险）",
  53:"Hypit + 剪映 Skill：AI 拆解视频、生成素材，再渲染进剪映",
  83:"Obsidian 从 iCloud 换成自建 Fast Note Sync，AI Agent 可以通过 MCP 访问",
  44:"一套角色一致性很好的 AI 出图方法（10w+ 浏览）",
  56:"Jev 网站合集（YouWare），包含申请路径和 API 调用",
  40:"用 Muse Agent 自动注册甲骨文云",
  64:"X Premium+ 约 100 元/月，含 Grok 额度，比 Claude/ChatGPT 基础订阅便宜",
  71:"FluentRead 改版后可以替代沉浸式翻译",
  94:"X Filter CN：过滤引流和色情回复的 Chrome 扩展（开源）",
  92:"vibe coding 做的日本汉字和简中汉字差异对比工具",
  96:"Cursor team 账单延迟的漏洞科普（属于钻计费规则的空子，有封号风险，不建议跟）"}),
("H","☕ 其他 / 闲聊","和主线无关的零散收藏。",
 {69:"怎么练英文听力，目标是听懂科技播客（讨论帖，2384 收藏）",
  22:"真果鉴：短剧聚合 App（来源不明，留意安全和版权）",
  34:"Starlink 家庭宽带广告",
  0:"蒙古包趣问"}),
]
picks={"A":[14,63,12,9,60,51],"B":[26,23,18,4,82,72],"C":[33,2,39,57,15],"D":[28,29,73],"E":[1,3,61,24],"F":[41,84,95,98],"G":[10,97,88,53],"H":[69]}
seen=set()
for c in cats:
    for i in c[3]: assert i not in seen,i; seen.add(i)
assert seen==set(range(100)),set(range(100))-seen
todos=[
("⏰ 有时效 / 会过期",[
 (18,"香港驾照换证预约：名额每个工作日 17:00 更新，只放未来 4 周；递交前 3 个月内要在运输署平台核实手机号或邮箱"),
 (60,"Majority 开户奖励：入金 20 刀，30 天内完成 3 笔 >5 刀的消费"),
 (66,"Equifax 1 美元 7 天试用：注册的话，记得在到期前取消，避免续费"),
 (75,"smarty 邀请奖励：要在下个月续订 15£ 套餐才能拿 20£"),
 (28,"Bybit EU Card 新户奖励：入金 100 欧得 25 欧，首月 10% 返现，GPT 订阅返现上限 50 欧（先确认活动还在不在）"),
 (19,"美卡羊毛：SoFi 约 600 刀、Acorns 约 233 刀（作者的待办，你可以参考）"),
 (77,"富国开户奖励 500/325 刀，普通 ACH 就满足 DD（活动可能有期限）"),
 (57,"HiDeck 用的 EC20 模组现在不到 100 元，作者说想玩趁早"),
 (55,"wx-cli 作者说是限时公开，发于 09-18，可能已经关了"),
]),
("🔁 周期性保号 / 维护",[
 (32,"Google Voice：每 2~3 个月主动打一次电话（比如 Apple 800 免费客服），否则 3 个月回收"),
 (15,"Tello：改充 PAYG credit，一次管 90 天，到期前续充"),
 (39,"波兰 Play24：每年充 5 PLN 保号"),
 (54,"菲律宾 Smart / DITO：余额保持在 1 比索以上"),
]),
("✅ 一次性检查 / 行动项",[
 (82,"如果有 IBKR：检查有没有 U*****F 结尾的英国分公司账户，有的话发工单关闭，避免产生 CRS 信息交换"),
 (61,"如果升级了 iOS 27：旧的 WLOC+MITM 改定位已经失效，要换新方案"),
 (3,"如果在用 Claude：可以对照这份完整的分流域名规则检查一下"),
 (51,"Nu Bank US 开户时就要决定要不要信用卡，开户后不能再补开"),
]),
]
L=[]
dates=[b['created_at_bjt'] for b in B]
L.append(f"# @Chaoc2624 X 书签总结（按主题分类）\n")
L.append(f"- 生成时间：2026-10-08 北京时间\n- 共 {len(B)} 条（X API 返回的最近 100 条书签；还有更早的书签没有拉取）\n- 发帖时间范围：{min(dates)} ~ {max(dates)}（北京时间；绝大多数在 08-10 之后）\n- 书签文件夹：API 返回空，没有建过文件夹\n- 原始数据：/workspace/xbm/overview/bookmarks-raw.json\n")
L.append("## 分类概览\n\n| 类别 | 条数 | 概括 |\n|---|---|---|")
for k,name,desc,items in cats: L.append(f"| {name} | {len(items)} | {desc} |")
L.append("\n## 待办 / 有截止时间的条目\n")
for h,items in todos:
    L.append(f"### {h}")
    for i,txt in items: L.append(f"- {txt}（@{B[i]['author_username']}，{t(i)}）{link(i)}")
    L.append("")
for k,name,desc,items in cats:
    L.append(f"## {name}（{len(items)} 条）\n\n{desc}\n\n**精选**")
    for i in picks[k]: L.append(f"- {items[i].lstrip('★ ')}（@{B[i]['author_username']}，{t(i)}）{link(i)}")
    L.append("\n**全部**")
    for i in sorted(items,key=lambda i:B[i]['created_at_bjt'],reverse=True):
        L.append(f"- {items[i]}（@{B[i]['author_username']}，{t(i)}）{link(i)}")
    L.append("")
L.append("---\n说明：★ 表示推荐优先看。标「长文」的是 X Article，标题通过 X API 补全。部分帖子带邀请码或推广，涉及 KYC 和地址证明的内容请按合规方式操作。")
open('bookmarks-by-topic.md','w').write("\n".join(L))
json.dump({k:sorted(items) for k,_,_,items in cats},open('categories.json','w'))
print({name:len(items) for k,name,_,items in cats})
