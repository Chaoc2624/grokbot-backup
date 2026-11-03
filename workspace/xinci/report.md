## 新词雷达

### 新词表:新名字和它背后的通用词

今天读了:pando, lifeval, qwen3.5-0.8b 0.016, gemma 3 270m, anymodelbot。提出 16 个通用写法,9 个通过相关性筛选,其中 1 个月搜不低于 50(2026-09 数据)。
日搜是按每个通用词自己的月搜索量估算的。今天没法校准基准词 `gpts`,所以名字没有估算值。

| 关键词 | 类型 | 来自 | 新词? | 估算日搜 | 开始上涨 | 峰值 vs gpts | 峰值日 | 近 7 天比前 7 天 | 现在 | 近 12 个月 | 首次有搜索 | 市场(月搜/KD) | 首页竞争 | 首页结构 | 决策 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **lifeval** | 名字 | — | 是 | — | 2026-10-30 | 0 vs 55.1 | 2026-10-30 | — | 还在涨 | — | — | **最佳 JP** · US 10 · DE 10 · FR 10 · JP 90 · 热度最高 Japan | 挤满 · AI 概览 · 视频 | — | 观察 → 新建页面 |
| **qwen3.5-0.8b 0.016** | 名字 | — | — | — | — | 0 vs 63.9 | — | — | 还读不出 | — | — | US 0 · DE 0 · FR 0 · JP 0 | 挤满 | — | 观察 → 新建页面 |
| **anymodelbot** | 名字 | — | — | — | — | 0 vs 44.4 | — | — | 还读不出 | — | — | US 0 · DE 0 · FR 0 · JP 0 | 挤满 · AI 概览 | — | 观察 → 新建页面 |
| **ai agent benchmark** | 通用词 | lifeval | 否 | 19 | 2026-10-25 | 2 vs 59.1 | 2026-10-25 | ×3.9 | 回落 | ██▇▇▅▅▅▅▅▅▇█ 上升,6 个月 +86% | — | — | — | — | 跳过 |
| **pando** | 名字 | — | 否 | — | — | 55 vs 63.4 | 2026-10-15 | ×0.8 | 没动 | — | — | — | — | — | 跳过 |
| **gemma 3 270m** | 名字 | — | 是 | — | 2026-10-28 | 3 vs 66.3 | 2026-10-28 | ×0.9 | 回落 | — | — | — | — | — | 跳过 |

决策规则:优先 = 近 30 天涨过、现在还在高位、估算日搜不低于 300。观察 = 涨了但规模小;还太早读不出;或者没动但本身就有这个规模的稳定需求。跳过 = 已回落,或没动且规模小。Trends 最后两天的数据还没结算,不计入。
首页竞争:能进 = 前十里有 3 个以上评分低于 30 的站,或关键词难度低于 20;挤满 = 一个弱站都没有、难度 40 以上(或未知);其余为一般。↓ = 还在涨,但首页被强站占满,从优先降为观察。有广告 = 有人花钱买这个点击。已有页面 = 近一个月标题里带这个词的页面数(多少人已经在为它做东西);在投广告 = 在这个词上投谷歌广告的域名(广告透明度:已经有人为这个需求付钱)。评分、页面数和广告来自 GoAnyAPI,难度和结果来自 DataForSEO。
没有 GOANYAPI_API_KEY:首页竞争只看关键词难度,没有各站评分。
首次有搜索 = 近 5 年里第一个有 Trends 热度的那一周(DataForSEO Trends;还没过完的一周和没结算的最后两天不计);“之前” = 从区间开头就有搜索。🆕 = 首次有搜索在 180 天内:它的首页竞争放宽一档读(挤满 → 一般,一般 → 能进),因为难度分数跟不上新词。市场 = 各国 Google Ads 月搜索量 / 关键词难度,不限语言;最佳 = 每点难度对应的搜索量最高(缺难度时按搜索量);热度最高 = Trends 里热度最高的国家。首页结构(仅优先行):前十里首页和内页各几个、平台上的结果(github.com, medium.com, sites.google.com, *.github.io, reddit.com, youtube.com, wikipedia.org)、标题含关键词的;平台占据 = 一半以上在平台上;可超越 = 大多是内页且没有精确匹配的首页;其余为有争夺。

近 12 个月 = Google Ads 每月搜索量,一格一个月(按这个词自己的最高月从零缩放),最新一个月大约晚一到两个月。X 起才有 = 一年前几乎没人搜,那个月起到了峰值的十分之一;冲高 = 已过顶的爆发(峰值是中位月份的 2 倍以上,现在只剩一半以下);下降 = 跌到早先峰值的 60% 以下,或最近三个月只有之前三个月的 0.7 倍;上升 = 最近三个月是之前三个月的 1.3 倍以上;显示的变化是最新一个月对比六个月前。搜索太少 = 最高的一个月也不到 50,读不出走势。

决策后的 →:更新现有页 = 你的站已经在首页(首页检查里看到,或 Search Console 平均排名 10 以内),改那一页,别另起新页;改进现有页 = Search Console 里在第 2、3 页(平均 11 到 30 名);新建页面 = 没找到,或排得更靠后。你的站:frame-extractor.app, x.omnitools.cc。

AI 概览 = Google 在结果上方直接给答案,出现时用户点结果的比例大约减半(皮尤研究中心 2025:8% 对 15%)。答案框 = 答案就在搜索结果页上。

原话(每个通用词的依据):
- **ai agent benchmark** (lifeval): “LifeVal, a benchmark testing whether AI models can finish everyday errands for people”

相关查询未开启:设置 GOANYAPI_API_KEY 后,会加入大家和每个名字一起搜的词。

### 新名字的旁证：新建站、维基百科、Google、Discord

| 名字 | 带这个名字的新站（whois：30 天内注册；crt.sh：7 天内新证书） | 维基百科浏览（近 7 天 / 前 7 天） | Google 认成 | Discord 服务器 |
|---|---|---|---|---|
| pando | 2 (pandoracraft.co.uk, pandoramealbox.co.uk) · whois | 89 / 144 | — | — |
| lifeval | 0 · whois | — | — | — |
| qwen3.5-0.8b 0.016 | 0 | — | — | — |
| gemma 3 270m | 0 | — | — | — |
| anymodelbot | — | — | — | — |

### 候选新词(判为专有名词的排前面;已覆盖的会标出)

| 词 | 信号 | 名字得分 | 已覆盖 | 搜索变体 | 例子 |
|---|---|---|---|---|---|
| **pando** | X 2 个账号 ♥5457 | 0.90 | 无 | — | @OpenAIDevs: We built Pando, a new Git backend for / @dotey: AI 写的代码太多，Git 扛不住了：OpenAI 保留 Git 只换服务器，Ant |
| **lifeval** | X 1 个账号 ♥6071 | 0.80 | 无 | — | @OpenAI: For AGI to benefit all of humanity, it sh |
| **qwen3.5-0.8b 0.016** | X 1 个账号 ♥285 | 0.80 | 无 | — | @dotey: 不训练、不算梯度，GPT-6 Astra 直接改了另一个模型的权重：只动了 Qwen |
| **gemma 3 270m** | X 1 个账号 ♥285 | 0.80 | 无 | — | @dotey: 不训练、不算梯度，GPT-6 Astra 直接改了另一个模型的权重：只动了 Qwen |
| **anthropic residency** | X 2 个账号 ♥30524 | 0.70 | 无 | — | @AnthropicAI: Applications are now open for the An / @dotey: Anthropic 招驻留研究员：教授、技术创始人、资深工程师可转行做 AI 安全， |
| **mit csail** | X 2 个账号 ♥358 | 0.60 | 无 | — | @dotey: 不训练、不算梯度，GPT-6 Astra 直接改了另一个模型的权重：只动了 Qwen / @op7418: 昨晚推上 AI 圈最热门的研究： 我们可能可以像编程一样，让 AI 编写 AI 模 |
| **git** | X 2 个账号 ♥5457 | 0.50 | 无 | — | @OpenAIDevs: We built Pando, a new Git backend for / @dotey: AI 写的代码太多，Git 扛不住了：OpenAI 保留 Git 只换服务器，Ant |
| **anymodelbot** | GitHub 爆发 modelflare-ai/AnyModelBot ★2181(均 303/天,一天 +916) | 0.90 | 无 | modelflare-ai anymodelbot, modelflare anymodelbot | modelflare-ai/AnyModelBot: 🤖 Open-source, local-fi |
| **noir** | GitHub 爆发 Verlintas/NOIR ★1669(均 627/天,一天 +726) | 0.90 | 无 | verlintas noir | Verlintas/NOIR: 手机隐私审计：用 adb 扫出 Android 应用的权限、上报端点 |
| **run** | GitHub 爆发 BryceYuuu/RUN ★2674(均 526/天,一天 +1246) | 0.70 | 无 | bryceyuuu run, bryce run | BryceYuuu/RUN: RUN · 润：海外移居手册（欧洲 36 国 · 110 条路线 ·  |
| **com.clawhard** | ③ 竞品 12 处 (×11.9) | 0.70 | 无 | — |  |
| **connectors com.clawhard** | ③ 竞品 12 处 (×11.9) | 0.60 | 无 | — |  |
| **chat.conecto** | ③ 竞品 10 处 (×9.9) | 0.60 | 无 | — |  |
| **studio labs** | ③ 竞品 10 处 (×9.6) | 0.60 | 无 | — |  |
| **connectors chat.conecto** | ③ 竞品 10 处 (×9.9) | 0.50 | 无 | — |  |
| **sogni: ai image, video & music** 🎬 | App Store 新上架 | 0.90 | 无 | — | App Store: Sogni: AI Image, Video & Music |
| **glm 5.3 flashx legal** 🎬 | OpenRouter 新上架 | 0.70 | 无 | — | OpenRouter: GLM 5.3 FlashX Legal |
| **sun web & api** 🎙 | Product Hunt 新上架 | 0.90 | 无 | — | Product Hunt: SUN Web & API |
| **revreel: ai car edits** 🖼 | App Store 新上架 | 0.90 | 无 | — | App Store: RevReel: AI Car Edits |
| **photocut - ai photo editor** 🖼 | App Store 新上架 | 0.90 | 无 | — | App Store: PhotoCut - AI Photo Editor |

🎬 视频 · 🎙 语音 · 🖼 图片:它产出什么,一般用户愿意付费的顺序是 视频 > 语音 > 图片 > 文字。⚡ = 有 1,000 赞以上的帖子在手把手讲一套手动流程,或在跟一个热梗:还没人做成一键工具。按标签行动前先读原帖。

其他上升词(判为普通词):jascha sohl-dickstein, no ml, for agi, george22, genpark personal, cloudcorprecords, ocular, alphaparkinc genpark, r1, park genpark, alpha park, records, personal, corp, tutorials deepseek

### 主题:AI video

- 候选词 **sogni: ai image, video & music**:App Store 新上架

### ② 单仓库爆发(近 14 天新建,按每天涨星排;🆕 = 今天第一次达标)

| 仓库 | ★ | 均/天 | 比昨天 | 天数 | 简介 |
|---|---|---|---|---|---|
| [deepseek-ai/dsh-superagent-prototype](https://github.com/deepseek-ai/dsh-superagent-prototype) | 15720 | 4968 | +4158 | 3.2 | Towards a More Autonomous Agent System |
| [storytold/craft-anything](https://github.com/storytold/craft-anything) | 6405 | 2176 | +3861 | 2.9 | Craft Anything: understand how any software works, and craft |
| [heydamir/unslop](https://github.com/heydamir/unslop) | 6986 | 1423 | +1429 | 4.9 | A Claude skill that turns vibecoded, AI-looking UI into a de |
| [ccch1mneyyy/dsh-Go](https://github.com/ccch1mneyyy/dsh-Go) | 6841 | 742 | +1330 | 9.2 | dsh-go — DeepSeek Harness 装进口袋：手机本机运行，也能遥控你的电脑。 |
| 🆕 [BryceYuuu/RUN](https://github.com/BryceYuuu/RUN) | 2674 | 526 | +1246 | 5.1 | RUN · 润：海外移居手册（欧洲 36 国 · 110 条路线 · 主要移民地区） |
| [wangzan101/Mika](https://github.com/wangzan101/Mika) | 5894 | 1189 | +955 | 5.0 | An on-device AI agent for Android that operates apps and the |
| 🆕 [modelflare-ai/AnyModelBot](https://github.com/modelflare-ai/AnyModelBot) | 2181 | 303 | +916 | 7.2 | 🤖 Open-source, local-first alternative to Grok Bot, OpenAI d |
| [l0ng-ai/openidea](https://github.com/l0ng-ai/openidea) | 5463 | 419 | +910 | 13.0 | The IDE you know, rebuilt in Rust. IntelliJ IDEA–style keyma |
| [patch-gg/pixelfx](https://github.com/patch-gg/pixelfx) | 3885 | 907 | +653 | 4.3 | 244 pixel art effects, every one a small piece of code. Plus |
| [valentderah/totk-pc-recomp](https://github.com/valentderah/totk-pc-recomp) | 4323 | 858 | +685 | 5.0 | Static recompilation of The Legend of Zelda: Tears of the Ki |
| [anhao/ai-pose-gallery-zh](https://github.com/anhao/ai-pose-gallery-zh) | 5730 | 813 | +307 | 7.0 | 中文版 AI 姿势参考图库 · 1439 组 / 2878 张图片 / 完整汉化 · 零依赖静态画廊 |
| [unclebob/ub-mode](https://github.com/unclebob/ub-mode) | 6715 | 755 | +252 | 8.9 |  |
| 🆕 [Verlintas/NOIR](https://github.com/Verlintas/NOIR) | 1669 | 627 | +726 | 2.7 | 手机隐私审计：用 adb 扫出 Android 应用的权限、上报端点与数据流向，并给出可回滚的处置。Desktop An |
| [pengchujin/aerial-tv](https://github.com/pengchujin/aerial-tv) | 9255 | 653 | +302 | 14.2 | 给国产电视的一块干净桌面：参照 tvOS 设计的开源 Android TV 桌面，没有广告，开机自动接管。A tvOS- |
| [caru-ini/stack-diagram](https://github.com/caru-ini/stack-diagram) | 1395 | 599 | +494 | 2.3 | Agent skill: describe your stack in a sentence, get an archi |

### ⑨ 刚上架：新产品、新模型、新应用、新插件、热搜

- **Product Hunt**: [Teamily AI](https://www.producthunt.com/products/teamily-ai-human-ai-social-network); [AgentKit (by Scalekit)](https://www.producthunt.com/products/scalekit); [MachineMail](https://www.producthunt.com/products/machinemail); [SUN Web & API](https://www.producthunt.com/products/sun-ai); [Beamfy](https://www.producthunt.com/products/beamfy); [IQ](https://www.producthunt.com/products/iq-code); [Remote Gaze](https://www.producthunt.com/products/remote-gaze); [Peji](https://www.producthunt.com/products/peji); [Testera](https://www.producthunt.com/products/testera-3); [Calendarly](https://www.producthunt.com/products/calendarly-calendar-on-lock-screen)
- **Show HN**: [Subvocal](https://news.ycombinator.com/item?id=50340088); [Hacker Times, a New York Times-inspired version of Hacker News](https://hackertimes.ca/); [Warsaw in voxels](https://p.migdal.pl/warsaw-vibe-voxel/); [I built a little browser game to practice Vim commands](https://hjkl.duy.run)
- **OpenRouter**: [GLM 5.3 FlashX Legal](https://openrouter.ai/z-ai/glm-5.3-flashx-legal)
- **App Store**: [SocialLite-Block Reels&Shorts](https://apps.apple.com/us/app/sociallite-block-reels-shorts/id6757661674?uo=2); [AppClose](https://apps.apple.com/us/app/appclose/id1019290876?uo=2); [Sogni: AI Image, Video & Music](https://apps.apple.com/us/app/sogni-ai-image-video-music/id6450021857?uo=2); [RevReel: AI Car Edits](https://apps.apple.com/us/app/revreel-ai-car-edits/id6800568794?uo=2); [PhotoCut - AI Photo Editor](https://apps.apple.com/us/app/photocut-ai-photo-editor/id6444792863?uo=2); [Hushed: US Second Phone Number](https://apps.apple.com/us/app/hushed-us-second-phone-number/id600520752?uo=2)
部分来源失败：trending: HTTP 400: {"error":{"code":"invalid_arguments","details":{"reason":"unknown argument /country_code","session_guidance":"

### ⑤ 复盘(14 天前报出的词,在 DataForSEO Trends 里起没起来)

| 词 | 首次报出 | 结论 | 提前天数 |
|---|---|---|---|
| aiframework | 2026-10-16 | no_data | — |
| aki | 2026-10-16 | miss | — |
| aurelio finance | 2026-10-16 | miss | — |
| cloakbrowser | 2026-10-16 | hit | -25 |
| connectors io.github.ukraine | 2026-10-16 | no_data | — |

近 60 天的命中率(待复盘 432 个):

| 信号 | 复盘 | 命中 | 命中率 | 提前天数中位数 |
|---|---|---|---|---|
| ② 爆发 | 16 | 12 | 75% | -3.0 |
| ③ 竞品 | 4 | 1 | 25% | -25 |

### 数据状态

- ① X:35/35 个账号,659 条帖子
- ① HF:trending 100 个模型、100 个 Space
- ② 爆发:搜到 200 个新仓库
- ⑨ 新上架：trending: HTTP 400: {"error":{"code":"invalid_arguments","details":{"reason":"unknown argument /country_code","session_guidance":"
- ③ glama:154775 个网址,新增 1320
- ③ mcp.so:19813 个网址,新增 8
- ③ lobehub-mcp:200 个网址,新增 0
- ③ lobehub-skills:200 个网址,新增 0
- ③ toolify:927 个网址,新增 0
- ③ aixploria:613 个网址,新增 0
- ③ ai-bot.cn:5068 个网址,新增 693
- ③ opentools:7012 个网址,新增 0
- ③ dang:7806 个网址,新增 10
- ③ clipfly:281 个网址,新增 0
- ③ aitoptools:11881 个网址,新增 5
- ③ futurepedia:2499 个网址,新增 6
- 用时：共 7 min；超过 1 分钟的：sitemap 4 min、usecases 2 min
- 本次 AIsa 数据花费:$0.898(名字判断的模型调用另计)
