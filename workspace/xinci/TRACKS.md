# 双轨补源：游戏轨 + AI工具轨

补上 new-term-radar / 书签X 默认圈（AI 模型首发）容易漏的建站词。
例程现为每天 18:00（Asia/Shanghai）跑一次。在 XSCAN 之后、`merge_board.py` 之前跑双轨、新闻轨和热梗轨：

```bash
cd /workspace/xinci
python3 track_scan.py --mode pm
# 可选：把本档用 x MCP 搜到的帖塞进去
# python3 track_scan.py --mode pm --x-input /tmp/tracks_x_fill.json
PYTHONUNBUFFERED=1 python3 news_scan.py   # 新闻轨；须在 track_scan 之后，按当天 tracks/xnew 去重
PYTHONUNBUFFERED=1 python3 meme_scan.py   # 热梗轨；独立状态文件，不覆盖新闻轨产出
python3 merge_board.py                    # 会吃 tracks / news / meme 当日文件
```

产出：`tracks-YYYYMMDD-{am|pm}.json`、`news-YYYYMMDD.json`、`meme-YYYYMMDD.json` → 经 merge 进 `board_keywords.json` / `merged.json`，doable（KD≤31）照常打分。卡片 `render_card.py` 会画出游戏轨/AI工具轨分区；新闻轨 / 热梗轨条目经 merge / push 进入看板列表（来源 chip「新闻轨」「热梗轨」）。

---

## 游戏轨（source 标「游戏轨」）

**目标：** Roblox / Steam / Poki / 可玩 HTML5 爆款名 → 适合做游戏站、unblocked、在线玩页的词。

| 信号 | 怎么拿 | 免费？ |
|---|---|---|
| Steam 畅销 / 新热 / 全球畅销 | `store.steampowered.com/search/results/?filter=…&json=1` | 是 |
| Roblox Top Trending / Up-and-Coming / Playing Now | `apis.roblox.com/explore-api/v1/get-sorts` | 是 |
| Poki 首页热门 | 解析 `/en/g/{slug}` | 是 |
| X 社媒（人工/例程补） | 见 `XSCAN.md` 游戏轨查询；`--x-input` 填入 | 用免费 `x` MCP |

**清洗与出词：** 去 emoji / `[标签]` / ™®；主词 = 清洗后的游戏名；派生（控量）`{名} unblocked`、`{名} online`、`{名} play`。状态去重在 `track_state/game_seen.json`。

**过滤：** 明显色情/赌博丢弃；超长营销串截断；同一 run 每源最多约 25 条。

---

## AI工具轨（source 标「AI工具轨」）

**目标：** 导航站新上架工具名、PH/HN 新工具 → 适合做工具站 / alternative / generator 页。

| 信号 | 怎么拿 | 免费？ |
|---|---|---|
| Toolify 工具 sitemap 增量 | index + `sitemap_tools_N.xml`，对比 `track_state/` | 是 |
| Futurepedia `sitemap_tools.xml` 增量 | 同上；可用 lastmod 辅助 | 是 |
| Aixploria 当月 post sitemap 增量 | `sitemap-posttype-post.YYYYMM.xml` | 是 |
| Product Hunt 总 feed | Atom，抽产品名 | 是 |
| HN「AI tool」RSS | hnrss.org | 是 |
| X 社媒（人工/例程补） | 见 `XSCAN.md` AI工具轨查询 | 用免费 `x` MCP |

**清洗与出词：** URL 末段 slug → 空格化为人名；派生 `{名}`、`{名} ai`、`{名} alternative`（控量）。首次跑只建快照、`new=0`（与雷达 sitemap 同理）；第二次起出增量。

**过滤：** 路径碎片、纯数字 id、locale 重复丢掉；每源 new 上限约 40。

---


---

## 新闻轨（source 标「新闻轨」）

**目标：** 用 [Horizon](https://github.com/Thysrael/Horizon)（MIT）的免密钥、非 X 源，补上圈外的新产品 / 新工具 / 新游戏 / 新模型信号。不替换现有 radar daily、书签X、游戏轨、AI工具轨。

配置：`/workspace/xinci/news_sources.json`（可编辑查询词、频道、RSS 名单）。脚本：`/workspace/xinci/news_scan.py`（独立适配层，不整包安装 Horizon）。

| 信号 | 怎么拿 | 免费？ |
|---|---|---|
| Google News RSS 检索 | `news.google.com/rss/search`，`when:24h`，查询偏窄（新品/新工具/新游戏/模型发布） | 是，无密钥 |
| GDELT 2.0 DOC API | `api.gdeltproject.org/api/v2/doc/doc`，`timespan=24h` | 是，无密钥；共享出口 IP 可能 429 |
| 公开 Telegram 频道 | `t.me/s/<channel>` 网页预览（不登录） | 是 |
| 通用 RSS/Atom | Simon Willison、HF / OpenAI / DeepMind / Google AI / Ollama 博客、GitHub Trending Daily、Steam News、TechCrunch AI、The Verge AI | 是 |

**刻意不用的源与功能：** Horizon 的 twitter、openbb、email / wechat / webhook / pages、Apify、Playwright、Firecrawl；其 LLM 打分、enrichment、简报与推送。也不重复已有的 Toolify / Futurepedia / Aixploria sitemap、Product Hunt、HN。

**命令：**

```bash
cd /workspace/xinci
python3 news_scan.py                  # 默认北京当天、最近约 24 小时
# python3 news_scan.py --date YYYY-MM-DD --skip gdelt --no-llm --dry-run
```

**清洗与出词：** 规则过滤（需有发布/上线等信号，或来自官方博客 / 日更榜）+ 按名称 / URL 去重（当天 `tracks-*.json` / `xnew-*.json` + `track_state/news_seen.json`）。从标题抽产品 / 游戏 / 模型名；若需「是什么、做什么」或抽名，调用 `/home/box/.local/bin/free-llm`，失败则回退规则。主词 = 抽出的名称。

**产出：** `news-YYYYMMDD.json`，结构与 tracks 同形：`tracks.news.items[]`（name/desc/url/source/first_seen/kind）与 `keywords[]`（keyword/reason/from）。item 的 `source` 形如「新闻轨·Google News」「新闻轨·Telegram@zaihuapd」。

**合并与配额：** `merge_board.py` 读取当日 `news-YYYYMMDD.json`，items 进 `merged.terms`（来源「新闻轨」），keywords 进 `board_keywords.json`（`is_vacuum_candidate`）。`push_board.py` 带上新闻轨 items / source chip；关键词上限仍为 40，新闻轨最多 8 个，排在书签X / 游戏轨 / AI工具轨之后，**只填主轨用剩的名额，不挤占主轨**。主轨已满时新闻轨 keywords 可能为 0，但 items 仍在列表。


---

## 热梗轨（source 标「热梗轨」）

**目标：** 每天监听 TikTok、YouTube、Instagram 上用户可能用本人照片/视频复刻的热梗与 AI 视频热词。独立脚本与状态，不覆盖新闻轨文件。

配置：`/workspace/xinci/meme_sources.json`。脚本：`/workspace/xinci/meme_scan.py`。

| 平台 | 官方公开方法 | 本次可达？ |
|---|---|---|
| TikTok | Creative Center 公开 Trends 页 HTTP GET；完整榜需 [Discovery API](https://business-api.tiktok.com/portal/docs/discovery-api-overview/v1.3)（广告账户授权） | 公开页 HTTP 200，但热榜为前端渲染，HTML 抽不到标签；无 advertiser token，直采记为 unavailable |
| YouTube | 官方 [Data API v3 `videos.list?chart=mostPopular`](https://developers.google.com/youtube/v3/docs/videos/list) | 无 API key，探测 403；官方 RSS 不支持 chart=mostPopular。且 2025-07 起该榜来自 Music/Movies/Gaming，不等于已下线的 Trending Now |
| Instagram | 无免申请官方趋势 RSS/API；[Meta Content Library](https://transparency.meta.com/en-us/researchtools/meta-content-library/) 需 CASD 科研审核 | unavailable，需正规权限 |
| secondary（须标注，不是直采） | 官方 [Google Trends RSS](https://trends.google.com/trending/rss?geo=US) | 可抓，仅作 discovery；须过滤到 AI 视频/复刻梗，不能写成三平台热榜 |

**刻意不用：** 未公开的 Creative Center 内部接口、复制 cookies、绕过登录/反爬、Google News 或 X 转述冒充平台直采、历史种子（hotel lobby、ai raindance、ai zombie、burning bridges、Bulin47）当作当天趋势。不安装 TikTok for Business（广告投放）或 TubeAlfred（字幕/评论）插件充当热榜源。

**命令：**

```bash
cd /workspace/xinci
PYTHONUNBUFFERED=1 python3 meme_scan.py
# python3 meme_scan.py --date YYYY-MM-DD --no-llm --dry-run
```

**清洗与出词：** 排除历史种子；抽名/解释/去重用 `free-llm`（失败则规则）。无多点快照或多创作者复刻证据时，`trend_stage` 标「待观察」，**新发现 ≠ 新爆**，不编造增速。视频仅元数据，`video_semantics` 标「未核实」，不声称已观看。Semrush 缺数据不能判 0 量。原帖营收是作者自述，不用于评分承诺。

**产出：** `meme-YYYYMMDD.json`：`tracks.meme.items[]`（name/desc/url/source/first_seen/kind，以及 platform、source_url、collected_at、published_at、metrics、replication_evidence、trend_stage、generation_feasibility、risks、coverage_type、video_semantics）与 `keywords[]`。另有 `coverage`（各平台 status / 原 URL / 采集时间 / 可得指标）和 `permissions_needed`。状态去重：`track_state/meme_seen.json`，并与当天 tracks/xnew/news 去重。

**合并与配额：** `merge_board.py` 读取当日 `meme-YYYYMMDD.json`，来源「热梗轨」。`push_board.py` 带 source chip；热梗轨 keywords 最多 6 个，只填主轨用剩名额，不挤占书签X / 游戏轨 / AI工具轨。

**失败口径：** 某平台直采失败时，coverage.status 写 `unavailable`/`blocked`，摘要须写清「未全接入」及所需正规权限，不得称已监听三平台热榜。Google Trends 命中只能标 secondary。

## 合并与门槛

1. `track_scan.py` 写出 `tracks-*.json`：`tracks.game|ai_tools` 下各有 `items[]`（name/desc/url/source/first_seen/kind）和 `keywords[]`（keyword/reason）。
2. `merge_board.py` 读取当日 am+pm 的 tracks 文件以及 `news-YYYYMMDD.json`、`meme-YYYYMMDD.json`：items 进 `merged.terms`（来源「游戏轨」「AI工具轨」「新闻轨」「热梗轨」），keywords 进 `board_keywords.json`（带 `is_vacuum_candidate`）。
3. 晚上 `doable.py` 照旧读 `board_keywords.json`，**门槛不变**（`min_volume` 500、`max_kd` 31 等）。过线才算可做词。
4. 付费 Semrush 仍只在 doable；本轨脚本不调 AIsa。

## X 部分说明

Shell 里调不到 `x` MCP。例程执行器应按 `XSCAN.md` 列出的查询用 `CallDynamicTool namespace="x"` 搜帖，整理成：

```json
{"game":[{"name":"…","desc":"…","url":"https://x.com/…","source":"@…","first_seen":"YYYY-MM-DD HH:MM"}],
 "ai_tools":[…]}
```

再 `--x-input` 喂给 `track_scan.py`；不喂也不影响 Steam/Roblox/sitemap 等自抓部分。
