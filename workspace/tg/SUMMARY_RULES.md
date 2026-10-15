# TG 群总结 — 写作规则（每小时片段、6 小时时段、全天合并总结前必读）

## 一、铁律（用户要求，2026-10-08）
1. **只写群成员实际说了什么。** 不加自己的判断、警告、建议、评价或标签。
   - 禁止：⚠️、「别碰」「别学」「属于伪造证件」「违规」「欺诈」「有风险」「不推荐」「注意」「建议…」「待验证」等非成员说的话。
   - 成员自己的警告/建议就是该成员的发言行：`> Drift Silent：求人不如花钱，关系不好没有谁愿意给你地址，风险还是大`。
2. **不拿用户（Halo）比较或联系**（禁止「和你的情况类似」「你可以…」）。
3. **事实与原文完全一致**：发言行里的话必须是原文（只允许用「…」截掉前后或中间的无关部分、用 ` · ` 连接同一人的几条消息、加 `==关键词==` 标记）；不改写、不总结、不合并不同人的话。
4. **说话人写清楚**：每行开头写 TG 显示名（`> 东逆：…`）；机器人（东逆 Bot、AI_bot、丫丫、Group Help、TGBot）的推广尽量不收，确有信息时照原文截短一行。
5. **核对代替记忆**：prep 的 .txt 是筛选稿；写进总结的每条说法要在 .txt 或用 `tools/q.py` 在原始 JSON 里查到。
6. 闲聊、成人内容、政治段子不收。整小时没有实质内容的群在 spec 里不写（自动显示「无重要内容」）。
7. **拼写**查 `glossary.md`；遇到新的产品/运营商/银行/卡名/VPS 商/常见成员，追加到 glossary.md 对应小节。

## 二、写法：群 → 小时 → 话题 → 聊天记录（2026-10-08 起，看板按聊天记录样式渲染）
用户要求：不要「谁谁说「…」，谁谁说「…」」的长段落；每个话题下面是一行一个人的聊天记录。

关注重点：**eSIM、电话卡/SIM 卡、外卡/美卡、办电/保号/Wi-Fi Calling、银行卡与开户、U 卡、数字银行**；VPS 群里的 **VPS / 家宽 / 补货**。其他话题（AI 账号、Loon 用法等）少量收。

spec（`specs/<D>-<HH>.spec`）里每个群一个 `=== <group key>` 块，块内只用这几种行：

```
=== waika
### Maxx 预付 / 后付 (11 条 / 4 人)
> xy1：maxx的预付和后付有什么区别
> 一隻北極熊：預付套餐是自己買，可以改，可以疊加 · 後付只能一直每月付==12==，最多加成==15==
### 新加坡银行 / Wise (41 条 / 6 人)
> SSS：新加坡银行业都沦陷了
> 艺术家的爱也有保质期：monzo我被拒了 · wise国内可以申请卡
~ 话题活跃成员（近 7 天话题消息）：艺术家的爱也有保质期 34（银行开户/VPS/SIM）、苏 可乐 18（SIM/银行开户）
### 零星消息
> Acmo：微信绑定外卡被限制社交功能可以解封吗
--- 核验
- Maxx $12 / $15 套餐｜Maxx 官网（2026-10-08 查阅）：FAQ 写明 … https://maxxonline.sg/faqs-sim-only-plan
```

- `### 话题名 (N 条 / M 人)`：话题标题；N/M 是本小时该群讨论这个话题的消息数和不同发言人数（不含机器人），用 `tools/q.py hourly/<HH> '正则' <group> --count --date <D>` 统计；没统计就不写括号。标题中性（产品/事情名），不带评价。
- `> 发言人：原话`：一行一个人，按时间顺序；同一人连续几条用 ` · ` 连起来；**不写「说」、不加「」**；原话照抄（可用 `…` 截短，长消息截到 ~130 字）；链接原样保留。
- `==关键词==`：产品/卡/运营商/银行/金额/关键事实可手动标记；**一行没有标记时 mkfrag 会自动标**（品牌词表和金额，见 `tools/chatfmt.py`），所以一般不用手标；不要用 ** 加粗。
- **经验分享**（美卡、办电、开银行卡、U 卡、数字银行的亲身经历）单独一个 `### 经验分享（…）` 话题，同样是原话行。
- `~ 话题活跃成员（近 7 天话题消息）：A 34（话题）、B 18（话题）`：数字取 prep 的「话题活跃成员」行，只写数字和话题。
- `### 零星消息`（不能漏）：只出现一两次的话题消息（卡、SIM、eSIM、银行、VPS、羊毛、链接）放这里，同样一行一人。prep「### 话题消息」里每一行要么进某个话题、要么进零星消息，除非是机器人重复推广或纯表情。
- 不要写 `- ` 开头的叙述句、「X 说…」「其余多为闲聊」「已略」之类的句子（checkquotes 会报 prose line）。小时分隔线 `**18:00–19:00**` 由合并脚本加，spec 里不写。

### 排序与「涉及商家」（用户要求，2026-10-09；脚本自动执行，看板也按同样规则显示）
- **条目新→旧**：一个时段里的小时段 `**HH:00–HH:00**` 最新的在最上面；一小时内（以及 daily 每个 `## 大类` 内）的话题按「话题里最晚一条发言的时间」从新到旧排；`### 零星消息` 固定在最后；没有时间的话题排在有时间的后面。
- **话题内发言旧→新**：同一个话题里的 `> 发言人：原话` 按 `{{时间}}` 从早到晚排（让人看到讨论是怎么开始的）；没有时间的行留在原位置。
- **涉及商家**：每个话题标题下自动加一行 `~ 涉及商家：A · B · C` = 这个话题发言里出现的商家/平台/银行/运营商/卡（按第一次出现的先后；名字取 glossary.md 的正确写法，如 krak/海妖 → Kraken、stb → Starryblu、c1 → Capital One）。词表 = glossary.md 里反引号写的名字 + tools/order.py 的少量补充；**不要手写这一行**，每次都会重算；新商家请加进 glossary.md（用反引号）才会出现。
- `~ 话题活跃成员…` 行自动移到该小时段末尾；网上核验整块在最后。
- 执行位置：`tools/order.py`（mkfrag / addtimes / tg_merge6h / tg_digest_push / xbm tg_pull_summary.py push 都会调用；手动：`./venv/bin/python tools/order.py FILE.json`）。spec 里照常按时间顺序写即可，不需要自己排。

## 三、网上核验（单独一节，看板上显示为黄色虚线框「🔎 网上核验 · 外部公开来源，不是群友发言」）
每小时挑 **3–5 条关键事实说法**（新优惠/活动、政策变化、价格、开户/注册要求、补货），上网核对：
- 顺序：官网/官方帮助页/官方 X 账号 → 中文论坛（NodeSeek、V2EX、HostLoc、小红书/知乎可作参考）→ 英文论坛（Reddit、FlyerTalk、LowEndTalk 等）→ X 搜索（x 命名空间的 search_posts_all 等，每小时约 20 次以内）。
- 写在该群 spec 块的 `--- 核验` 行之后，每条一行，格式固定：`- 说法简述｜来源名（日期）：来源怎么写的 链接`，例：
  `- 万里汇推荐奖励｜WorldFirst 英国官网（2026-10-08 查阅）：推荐人 ==￡150==、被推荐人 ==￡50==，条件为 … https://…`
  `- Maxx 免费通话｜未找到公开信息（已查官网、X）：—`
  `- 税卡开 MiniPay｜X @hellokivin（2026-09-16）：原文为 我前几天还用税卡开了minipay的卡呢。 https://x.com/…`
- 只写来源怎么说、日期和链接；**不写自己的结论**（不写「属实」「是假的」「建议」）。合并后每条前面自动加小时。

## 四、全天合并总结（daily.json）
同样是聊天记录格式：`## 大类`（🔥 今日要点 / 💳 U 卡 / 数字银行 / 🇭🇰 港卡 / 🇬🇧 英区 / 🇺🇸 美卡 / 📱 SIM / eSIM / 🖥 网络 / AI / 其他）→ `### 话题 【群标签】 (N 条 / M 人)` → `> 发言人：原话`。
一个话题的原话都来自同一个群时，群标签写在标题里；来自多个群时，每行末尾写 `【群标签】`（groups.json 的 tag）。只能取当天各小时片段里已核对过的原话；每个大类里话题按最晚发言时间新→旧排、话题内发言旧→新（推送时 order.py 自动排，并加 `~ 涉及商家`）。网上核验放最后一节 `#### 🔎 网上核验（外部公开来源，不是群友发言）`，格式同第三节。
检查：`./venv/bin/python tools/checkquotes.py <D> day digests/<D>/daily.json`。

## 五、流程（每小时一次；看板固定 4 个 6 小时时段 00-06 / 06-12 / 12-18 / 18-24）
`./venv/bin/python tg_hourly.py` 打印要做的小时、所属时段、完整命令和积压。每小时依次：
1. `./venv/bin/python tg_fetch.py --window lasthour` → `data/<D>/hourly/<HH>.json`（22 个群约 30 秒；00:xx 那次抓前一天 23-24）
2. `./venv/bin/python tg_prep.py data/<D>/hourly/<HH>.json > data/<D>/hourly/<HH>.txt`（同时写 `<HH>.stats.json` 成员统计）
3. 读 .txt，按第二节写 spec（聊天记录格式），存为 `specs/<D>-<HH>.spec`（安静的群不写）；用 q.py 查原文和统计热度；写完跑 `./venv/bin/python tools/checkquotes.py <D> <HH> specs/<D>-<HH>.spec`，必须输出 all speech lines verbatim（NOT FOUND 要改；prose line / speaker? 警告也要处理）
4. 网上核验 3–5 条，写进对应群的 `--- 核验` 段
5. `./venv/bin/python tools/mkfrag.py <D> <HH> < specs/<D>-<HH>.spec` → `digests/<D>/hourly/<HH>.json`（标题、条数自动填，群按 groups.json 的 order 排）
6. `./venv/bin/python tg_merge6h.py --date <D> --block <HH-HH> --push`（时间线：最新的小时在最上面，自动加「**HH:00–HH:00**」小时分隔 + 各话题聊天记录（话题新→旧、发言旧→新、涉及商家）；核验集中在每群末尾；时段最后一小时合并前 partial=true）。不要手改 block 文件，改片段后重新 merge。
7. 按第四节更新 `digests/<D>/daily.json`（聊天记录格式；partial 直到 23-24 合并完；checkquotes `day` 通过）→ `./venv/bin/python tools/addtimes.py <D> digests/<D>/daily.json` → `./venv/bin/python tg_digest_push.py digests/<D>/daily.json`（push 会按排序规则重排并写回文件）
8. 推送后检查：`grep -n '⚠\|别碰\|别学\|伪造\|和你' digests/<D>/*.json` 只能命中成员原话；`grep -c '说「' digests/<D>/hourly/<HH>.json` 应为 0。
旧 3 小时总结在 `digests/<D>/3h/`；旧日期迁移：`./venv/bin/python tg_migrate3to6.py --date <D> [--dry-run]`。

格式：片段 / 时段文件 → {date, window, partial, win_start, win_end, items:[{group,title,content(聊天记录格式, 见 tools/chatfmt.py),msg_count[,verify]}]}。
本地预览看板：`LOCAL=1 ./venv/bin/python board/preview_server.py`（http://127.0.0.1:8765/#tg，用本地 digests 替换当天内容）；截图 `python3 board/shot2.py http://127.0.0.1:8765/ out.png 1280 2600 '外卡交流频道'`。
