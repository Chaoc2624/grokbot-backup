# XSCAN：书签X 扫描流程（AI 新品 + 建站热词）

每次 10:20（am 档）和 21:20（pm 档）运行；晚上档在 merge_board.py 之前执行。
只用免费的 `x` 命名空间（CallDynamicTool namespace="x"），**绝不用 user-X**。先 GetDynamicTools 确认 `x` 可用；出错按 x-api-mcp-guide 处理（429 等一次重试一次，5xx 退避一次，仍失败就写 empty+error 文件并在摘要里说明）。

## 1. 窗口
- 读 `/workspace/xinci/xscan_state.json`：`last_scan`（UTC ISO）、`reported`（已报的规范化名 → {name, first_seen, file}）。
- start = last_scan（不存在则 now-24h），end = now。时间一律以 UTC 传给 X，输出转北京时间 `YYYY-MM-DD HH:MM`。

## 2. 抓取（search_posts_all，write_to_file=true，sort_order=recency，max_results=100，翻页直到无 next_token 或超过 3 页）
通用参数：`start_time`=start，`post.fields=created_at,public_metrics,author_id`，`expansions=author_id`，`user.fields=username`。
A. 重点账号：
`(from:_akhaliq OR from:huggingface OR from:OpenAI OR from:OpenAIDevs OR from:Google OR from:GoogleDeepMind OR from:GoogleAI OR from:AnthropicAI OR from:claudeai OR from:ClaudeDevs OR from:AIatMeta OR from:xai OR from:deepseek_ai OR from:Alibaba_Qwen OR from:Qwen_AI OR from:ModelScope2022 OR from:MistralAI OR from:MiniMax_AI OR from:AntLingAGI OR from:canva) -is:retweet -is:reply`
B. 首发关键词（sort_order=relevancy，max_results=50）：
`("open-weight" OR "open weights" OR "introducing" OR "we're releasing" OR "now available" OR "model is here" OR "has landed") (model OR agent) -is:retweet -is:reply min_likes:500 lang:en`
B 里发现的新品，作者不是官方/创始人时，再用 `"<产品名>" (from:<官方号>)` 或 `get_posts_by_id` 找到官方首发帖，用官方帖作 url；找不到官方帖=传闻，不收。

## 3. 筛选规则
- AI 新品：只收真实首发帖（产品/模型首次发布）。每条：name、desc（一句中文）、source(@账号)、url、first_seen(北京)、views、bookmarks。
- 合作/上架/收购/科研成果/功能更新/报告：可收，desc 末尾标「不是新模型」，`kind:"not_model"`。
- 招聘、活动、人事、营销转发：不收。
- 名字规范化（同 merge_board.norm）后已在 `reported` 里 → 不再收；本窗口之前首发、但上档漏报的 → 收，并加 `"backfill": true`，desc 前加「【补报】」。
## 4. 建站热词（≤3，宁缺勿滥）
从本档新品（`kind:"model"/"product"`，非 not_model 优先）挑：名字全新（非老品牌泛词）、views ≥ 50万 或 bookmarks ≥ 1000、明显有搜索需求、通用词竞争小。给 `keyword_rank`/`keyword`/`reason`（含一句"适合做什么页面"）。
## 5. 输出 `/workspace/xinci/xnew-YYYYMMDD-{am|pm}.json`（北京日期；10:20=am，21:20=pm）
与看板 radar 文件同形：`label`("YYYY-MM-DD 下午/晚上 书签X")、`run_at`、`window_start`、`window_end`、`empty`、`items[]`（name, desc, source, url, first_seen, keyword_rank?, keyword?, reason?, kind, views, bookmarks, backfill?）、`keywords[]`({keyword, reason})、`error?`。
## 6. 更新状态
写成功后：`last_scan`=end，把本档所有 items 加进 `reported`。保留 30 天内的 reported。
## 7. 之后
运行 `python3 merge_board.py`（会读 xnew-*.json，来源标「书签X」，建站热词进 board_keywords.json）。摘要里 AI 新品一节列 name / 一句话 / 链接 / 首发时间 / 来源。

---

## 8. 双轨补源（游戏轨 + AI工具轨）

详细设计见 [`TRACKS.md`](./TRACKS.md)。本档 XSCAN 只列 **X 查询**（用免费 `x` MCP）；公开网页源由 `track_scan.py` 自抓。

**例程插入点：** 写完 `xnew-*.json` 之后、跑 `merge_board.py` 之前：

```bash
cd /workspace/xinci
# 可选：把下面查询的结果整理成 JSON 后 --x-input 喂入
python3 track_scan.py --mode am   # 或 pm
python3 merge_board.py
```

### 8.1 游戏轨 — X 查询（例程执行，不在 Shell）

用 `CallDynamicTool namespace="x"` → `search_posts_all`（`sort_order=Recency`，`max_results`≤100，`-is:retweet`）。窗口同 §1。

1. `(Roblox OR "roblox game" OR "steal a" OR survivors OR poki OR "unblocked games" OR itch.io) (viral OR trending OR "new game" OR exploded OR 爆款 OR 新游) -is:retweet lang:en OR lang:zh`
2. `("steam charts" OR "steam top" OR "new on steam" OR "steam next fest") (game OR play) -is:retweet lang:en`
3. `(游戏站 OR unblocked OR "在线玩" OR "网页游戏" OR Poki OR Roblox) (新词 OR 热词 OR 爆了 OR 日pv OR 建站) -is:retweet lang:zh`

收成 `{name, desc, url, source, first_seen}` 列表，写入临时 JSON 的 `game` 数组。公开源（无需 X）：Steam charts JSON、Roblox explore API、Poki `/en/g/` — 已由 `track_scan.py` 自动抓。

### 8.2 AI工具轨 — X 查询

1. `("new ai tool" OR "ai tool launch" OR "just launched" OR "product hunt") (ai OR generator OR agent) -is:retweet lang:en min_faves:50`
2. `(Toolify OR Futurepedia OR Aixploria OR "ai directory") (new OR added OR growth OR 增长) -is:retweet`
3. `(AI工具站 OR "ai generator" OR "ai alternative" OR Toolify) (新上 OR 增长榜 OR 挖词 OR 热词) -is:retweet lang:zh`

写入同一 JSON 的 `ai_tools` 数组后：

```bash
python3 track_scan.py --mode pm --x-input /tmp/tracks_x_fill.json
```

公开源（无需 X）：Toolify / Futurepedia / Aixploria **sitemap 增量**（`track_state/` 快照）、Product Hunt Atom feed、HN `AI tool` RSS。

**注意：** 首次跑 sitemap 只建快照、`new=0`；第二次起才出导航站新工具名。doable 门槛不变（KD≤31 等）。
