# 双轨补源：游戏轨 + AI工具轨

补上 new-term-radar / 书签X 默认圈（AI 模型首发）容易漏的两类建站词。
早晚例程在 XSCAN 之后、`merge_board.py` 之前（或紧挨其后）跑：

```bash
cd /workspace/xinci
python3 track_scan.py --mode am   # 或 pm；10:20 / 21:20
# 可选：把本档用 x MCP 搜到的帖塞进去
# python3 track_scan.py --mode pm --x-input /tmp/tracks_x_fill.json
python3 merge_board.py            # 会吃 tracks-YYYYMMDD-*.json
```

产出：`tracks-YYYYMMDD-{am|pm}.json` → 经 merge 进 `board_keywords.json` / `merged.json`，晚上 doable（KD≤31）照常打分。卡片 `render_card.py` 早晚都会画出游戏轨/AI工具轨分区；有词也会进看板合并列表。

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

## 合并与门槛

1. `track_scan.py` 写出 `tracks-*.json`：`tracks.game|ai_tools` 下各有 `items[]`（name/desc/url/source/first_seen/kind）和 `keywords[]`（keyword/reason）。
2. `merge_board.py` 读取当日 am+pm 的 tracks 文件：items 进 `merged.terms`（来源「游戏轨」「AI工具轨」），keywords 进 `board_keywords.json`（带 `is_vacuum_candidate`）。
3. 晚上 `doable.py` 照旧读 `board_keywords.json`，**门槛不变**（`min_volume` 500、`max_kd` 31 等）。过线才算可做词。
4. 付费 Semrush 仍只在 doable；本轨脚本不调 AIsa。

## X 部分说明

Shell 里调不到 `x` MCP。例程执行器应按 `XSCAN.md` 列出的查询用 `CallDynamicTool namespace="x"` 搜帖，整理成：

```json
{"game":[{"name":"…","desc":"…","url":"https://x.com/…","source":"@…","first_seen":"YYYY-MM-DD HH:MM"}],
 "ai_tools":[…]}
```

再 `--x-input` 喂给 `track_scan.py`；不喂也不影响 Steam/Roblox/sitemap 等自抓部分。
