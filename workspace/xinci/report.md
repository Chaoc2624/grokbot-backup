## 新词雷达

### 新词表:新名字和它背后的通用词

今天读了:pokebonk, qwen3.5-0.8b, rubix lang, php2shell poc, php2shell bypass aslr exp。提出 22 个通用写法,13 个通过相关性筛选,其中 0 个月搜不低于 50(? 数据)。
日搜是按每个通用词自己的月搜索量估算的。今天没法校准基准词 `gpts`,所以名字没有估算值。

| 关键词 | 类型 | 来自 | 新词? | 估算日搜 | 开始上涨 | 峰值 vs gpts | 峰值日 | 近 7 天比前 7 天 | 现在 | 首页竞争 | 决策 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pokebonk** | 名字 | — | 是 | — | 2026-10-15 | 100 vs 8.1 | 2026-10-19 | — | 还在涨 | 挤满 | 观察 |
| **qwen3.5-0.8b** | 名字 | — | 是 | — | 2026-09-20 | 12 vs 51.9 | 2026-09-22 | — | 维持 | 挤满 | 观察 |
| **rubix lang** | 名字 | — | — | — | — | 0 vs 46.4 | — | — | 还读不出 | 挤满 | 观察 |
| **php2shell poc** | 名字 | — | — | — | — | 0 vs 51.0 | — | — | 还读不出 | 挤满 | 观察 |
| **php2shell bypass aslr exp** | 名字 | — | — | — | — | 0 vs 54.9 | — | — | 还读不出 | 挤满 | 观察 |

决策规则:优先 = 近 30 天涨过、现在还在高位、估算日搜不低于 300。观察 = 涨了但规模小;还太早读不出;或者没动但本身就有这个规模的稳定需求。跳过 = 已回落,或没动且规模小。Trends 最后两天的数据还没结算,不计入。
首页竞争:能进 = 前十里有 3 个以上评分低于 30 的站,或关键词难度低于 20;挤满 = 一个弱站都没有、难度 40 以上(或未知);其余为一般。↓ = 还在涨,但首页被强站占满,从优先降为观察。有广告 = 有人花钱买这个点击。已有页面 = 近一个月标题里带这个词的页面数(多少人已经在为它做东西);在投广告 = 在这个词上投谷歌广告的域名(广告透明度:已经有人为这个需求付钱)。评分、页面数和广告来自 GoAnyAPI,难度和结果来自 DataForSEO。
没有 GOANYAPI_API_KEY:首页竞争只看关键词难度,没有各站评分。

相关查询未开启:设置 GOANYAPI_API_KEY 后,会加入大家和每个名字一起搜的词。

### 候选新词(判为专有名词的排前面;已覆盖的会标出)

| 词 | 信号 | 名字得分 | 已覆盖 | 搜索变体 | 例子 |
|---|---|---|---|---|---|
| **pokebonk** | X 1 个账号 ♥157 | 0.90 | 无 | — | @op7418: 这哥们儿做的宝可梦版本《吸血鬼幸存者》游戏是真的火 叫 PokeBonk，我去，玩 |
| **qwen3.5-0.8b** | X 1 个账号 ♥114 | 0.80 | 无 | — | @TeksEdge: This small Local AI model could replace |
| **ocrbench kie** | X 1 个账号 ♥114 | 0.70 | 无 | — | @TeksEdge: This small Local AI model could replace |
| **carbon x release** | HF Spaces 新进榜第 46 名 | 0.70 | 无 | — | HuggingFaceBio/Carbon-X-Release (static, ♥19) |
| **ssi** | HF Spaces 新进榜第 40 名 | 0.60 | 无 | — | Hunter26666666/SSI_Space (docker, ♥48) |
| **rubix lang** | GitHub 爆发 tek-sys-hub/Rubix-lang ★1898(均 570/天) | 0.90 | 无 | tek-sys-hub rubix lang, tek rubix lang | tek-sys-hub/Rubix-lang: The 100% Pure x86-64 Assem |
| **php2shell poc** | GitHub 爆发 ikow/php2shell-poc ★1378(均 1118/天,一天 +955) | 0.80 | 无 | ikow php2shell poc, qi php2shell poc | ikow/php2shell-poc: CVE-2026-109618/109619 — 5 RCE |
| **php2shell bypass aslr exp** | GitHub 爆发 9bie/php2shell-bypass-aslr-exp ★850(均 775/天) | 0.80 | 无 | 9bie php2shell bypass aslr exp | 9bie/php2shell-bypass-aslr-exp: A php2shell exploi |
| **php2shell cve 2026 109618 cve 2026 109619 poc** | GitHub 爆发 eness/php2shell-CVE-2026-109618-CVE-2026-109619-PoC ★803(均 665/天) | 0.80 | 无 | eness php2shell cve 2026 109618 cve 2026 109619 poc, enes php2shell cve 2026 109618 cve 2026 109619 poc | eness/php2shell-CVE-2026-109618-CVE-2026-109619-Po |
| **dsh purge** | GitHub 爆发 mmparko/dsh-purge ★1549(均 166/天,一天 +704) | 0.70 | 无 | mmparko dsh purge | mmparko/dsh-purge: DeepSeek Harness 破甲 (mirror of  |
| **php2shell checker** | GitHub 爆发 openai/php2shell-checker ★696(均 451/天) | 0.70 | 无 | openai php2shell checker | openai/php2shell-checker:  |
| **connectors io.github.datadmon** | ③ 竞品 10 处 (×10.0) | 0.70 | 无 | — |  |
| **com.1102tools** | ③ 竞品 9 处 (×9.0) | 0.70 | 无 | — |  |
| **connectors com.1102tools** | ③ 竞品 9 处 (×9.0) | 0.70 | 无 | — |  |
| **connectors ai.saifs** | ③ 竞品 8 处 (×7.4) | 0.70 | 无 | — |  |
| **click.mymarketing** | ③ 竞品 7 处 (×7.0) | 0.70 | 无 | — |  |
| **connectors click.mymarketing** | ③ 竞品 7 处 (×7.0) | 0.70 | 无 | — |  |
| **co.youraitools** | ③ 竞品 7 处 (×7.0) | 0.70 | 无 | — |  |
| **connectors co.youraitools** | ③ 竞品 7 处 (×7.0) | 0.70 | 无 | — |  |
| **connectors app.openkrill** | ③ 竞品 9 处 (×6.0) | 0.70 | 无 | — |  |

其他上升词(判为普通词):emudhra 18, relation f1 ovisocr3, crypto.randomuuid, randomint, leis, io.github.theluckystrike, connectors io.github.theluckystrike, connectors com.textforagents, dev.workers.rainmaker, connectors dev.workers.rainmaker, dev.workers.rainmaker wells.well, connectors click.myagents, io.github.datadmon, sites, jobs scraper

### 主题:AI video

今天没有相关的新词

### ② 单仓库爆发(近 14 天新建,按每天涨星排;🆕 = 今天第一次达标)

| 仓库 | ★ | 均/天 | 比昨天 | 天数 | 简介 |
|---|---|---|---|---|---|
| [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) | 22262 | 4264 | +5556 | 5.2 | Debloat any Android or Google TV over Wi-Fi and get an Apple |
| [deepseek-ai/DeepInfer](https://github.com/deepseek-ai/DeepInfer) | 19376 | 3106 | +2294 | 6.2 | DeepInfer: High-performance, large-scale inference framework |
| [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) | 18909 | 1338 | +699 | 14.1 | An agent skill for creating detailed, interactive isometric  |
| [pengchujin/aerial-tv](https://github.com/pengchujin/aerial-tv) | 2871 | 1318 | +1035 | 2.2 | 给国产电视的一块干净桌面：参照 tvOS 设计的开源 Android TV 桌面，没有广告，开机自动接管。A tvOS- |
| 🆕 [ikow/php2shell-poc](https://github.com/ikow/php2shell-poc) | 1378 | 1118 | +955 | 1.2 | CVE-2026-109618/109619 — 5 RCE chains + detection rules (Sur |
| [simbasjungles/free-my-tv](https://github.com/simbasjungles/free-my-tv) | 3070 | 1116 | +724 | 2.8 | A fast, ad-free home screen for Google TV. Open source, buil |
| [ly05010419/MacNativeGames](https://github.com/ly05010419/MacNativeGames) | 4285 | 905 | +780 | 4.7 |  |
| 🆕 [9bie/php2shell-bypass-aslr-exp](https://github.com/9bie/php2shell-bypass-aslr-exp) | 850 | 775 | — | 1.1 | A php2shell exploit that requires no modifications to the of |
| 🆕 [mmparko/dsh-purge](https://github.com/mmparko/dsh-purge) | 1549 | 166 | +704 | 9.3 | DeepSeek Harness 破甲 (mirror of YuJunZhiXue/dsh-purge) — 上游即将 |
| 🆕 [eness/php2shell-CVE-2026-109618-CVE-2026-109619-PoC](https://github.com/eness/php2shell-CVE-2026-109618-CVE-2026-109619-PoC) | 803 | 665 | — | 1.2 | Proof-of-Concept (PoC) exploit for php2shell (CVE-2026-10961 |
| 🆕 [tek-sys-hub/Rubix-lang](https://github.com/tek-sys-hub/Rubix-lang) | 1898 | 570 | — | 3.3 | The 100% Pure x86-64 Assembly Systems Language |
| [JoasASantos/REA-Prompts](https://github.com/JoasASantos/REA-Prompts) | 1431 | 544 | +169 | 2.6 | REAP - Prompts for you to use REA (Reverse Engineer Anything |
| [xiaoyang111222/cn-math-taxonomy](https://github.com/xiaoyang111222/cn-math-taxonomy) | 2145 | 513 | +253 | 4.2 | 数学（小学到高中）、英语（三年级到高中）、初中物理的知识图谱：1644 个知识点、2403 条先修边、6723 道题，对 |
| 🆕 [ctresb/leis](https://github.com/ctresb/leis) | 1155 | 154 | +485 | 7.5 | Todas as leis do Brasil |
| 🆕 [openai/php2shell-checker](https://github.com/openai/php2shell-checker) | 696 | 451 | — | 1.5 |  |

### ⑤ 复盘(14 天前报出的词,在 Google Trends 里起没起来)

今天没有到期的词(最早报出的词还不满 14 天)

### 数据状态

- ① X:33/35 个账号,620 条帖子
- ① HF:trending 100 个模型、100 个 Space
- ② 爆发:搜到 200 个新仓库
- ③ glama:141772 个网址,新增 741
- ③ mcp.so:19665 个网址,新增 241
- ③ lobehub-mcp:200 个网址,新增 0
- ③ lobehub-skills:200 个网址,新增 0
- ③ toolify:no URLs read
- ③ aixploria:595 个网址,新增 0
- ③ ai-bot.cn:5068 个网址,新增 689
- ③ opentools:7007 个网址,新增 0
- ③ dang:7787 个网址,新增 5
- ③ clipfly:281 个网址,新增 0
- ③ aitoptools:11846 个网址,新增 4
- ③ futurepedia:1329 个网址,新增 0
- 本次 AIsa 数据花费:$0.221(名字判断的模型调用另计)
