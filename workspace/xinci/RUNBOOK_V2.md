# 新词雷达 v2 运行手册（每日 10:00 Asia/Shanghai）

本 Bot **不修改例程**。请父线程按下面的已验证入口更新例程，时间保持 10:00±15 分钟，enabled。

## 已验证入口（例程建议替换为）

1. 只用免费 `x` 命名空间（`search_posts_all`）。**不要用 user-X / 付费 API x。**
2. 按 `XSCAN.md` 跑官方首发 + 游戏/工具 + AI 视频玩法查询，写出：
   - `/workspace/xinci/xnew-YYYYMMDD-am.json`（推荐用 `--xnew` 显式传入）
   - 可选 `/workspace/xinci/v2_run/x-input-YYYYMMDD-am.json`（给 `track_scan --x-input`）
3. 查一次 AIsa `account`（免费）：记下 `usage.today.charged_usd` 作为 `--today-prior`（不回传密钥）。本轮硬上限 **$1.00 含今日已用**。不要充值。
4. 运行：

```bash
cd /workspace/xinci
PYTHONUNBUFFERED=1 PYTHONPATH=/workspace/xinci python3 run_v2.py \
  --date YYYY-MM-DD --slot am \
  --today-prior <今日已用美元> \
  --xnew /workspace/xinci/xnew-YYYYMMDD-am.json \
  --x-input /workspace/xinci/v2_run/x-input-YYYYMMDD-am.json
```

5. 读 `v2_run/summary-YYYY-MM-DD-am.json`、`v2_run/coverage-YYYY-MM-DD-am.json` 与看板回执。覆盖记录含 track / news / higgsfield / video / verify / legacy_sources / legacy_daily / finders / doable / merge / push，状态为成功、失败、`skipped_budget`、缓存复用或离线 skip，禁止把未跑步骤写成已跑。

### `--xnew` 与可选文件缺失

- `--xnew`：显式指定本轮 `xnew-*.json`。省略时按顺序查找：
  - `/workspace/xinci/xnew-YYYYMMDD-{slot}.json`
  - `/workspace/xinci/xnew-YYYYMMDD.json`
  - `/workspace/xinci/v2_run/xnew-YYYYMMDD-{slot}.json`
- 若以上都不存在：`x_status=missing`，流水线**继续**跑（游戏/新闻/视频等不受阻），不把“没有 xnew”写成采集失败。
- `--require-x`：在 xnew 缺失时以退出码 3 停止（例程若必须先有 X 再跑，可打开）。
- `--x-input`：**可选**。缺失则 `track_scan` 只跑公开游戏榜/sitemap，不注入 X 交叉条目。
- 过期或无日期的 `report.json` 会被跳过，不会污染当日看板。

### 本入口实际覆盖（不要把未跑步骤说成已跑）

`run_v2.py` **会调度**：track_scan、news_scan、higgsfield_scan、aisa_video_scan、优先词 verify（报价后 use）、本地 `finders.py --skip trends`（仅已验证零费分支：ac/appstore/hn）、`doable.py --only-extra`、merge、select、push_board。

### 原范围 legacy sources/daily：费用不可控，默认暂降级（不得称全部上游覆盖）

2026-11-19 实测：即使给 `radar daily` 加上官方 `--skip` 付费组（`x,review,usecases,judge,newsites,asks,sellers,builders,money,revenue,feeds`，以及 help 中的 `tutorials,sidelights`），日报仍记录 AIsa 数据花费约 $0.242，账户实扣约 $0.243。官方 CLI 的 `--max-usd` **仅用于 history**，不能给 `sources` / `daily` 做硬封顶。`--skip` 不是可验证硬费用控制。

因此**默认入口不再执行** `python3 -m radar sources` 与 `python3 -m radar daily`。覆盖记录必须是：

- `legacy_sources`: `status=skipped_budget`，`block=blocked_unbounded_cost`
- `legacy_daily`: `status=skipped_budget`，`block=blocked_unbounded_cost`

不得把这两步写成已跑或已完整覆盖上游。免费替代源由现有 **track / news / higgsfield**（外加免费 `x` MCP 的 xnew）提供。本次**不实现**上游硬费用控制；在可验证硬上限落地之前，默认保持封锁，不提供“再跑一遍无上限 daily”的开关。

- **finders**：默认只跑已验证零费分支 `python3 /workspace/xinci/finders.py --date YYYY-MM-DD --skip trends`（ac / appstore / hn）。`trends` 无 `--max-spend` 且报价 `may_exceed`，记 `skipped_budget`，即使看起来有报价也不跑。
- 既有已抓的 video / verify / doable 付费结果不要重复采集。`--legacy-only` 也不得默认重开无上限的 sources/daily。
- 禁止把过期无日期的 `report.json` 当作今日报告并入看板。

离线验收：`PYTHONPATH=/workspace/xinci python3 -m unittest tests.test_v2_offline tests.test_v2_quality_and_replay`  
其中 `test_run_v2_replay_exits_zero_and_payload_compliant` 用 `--replay-dir --no-paid --no-push` 贯通真实 `run_v2.py`（外部连接跳过/mock，日志标明 OFFLINE REPLAY/FIXTURE）。

## 规则摘要

- 发现种子（如 CapCut AI template）只作查询锚，**不得作为本轮新词进入 40 词**。
- 机械派生 `{name} ai` / unblocked/online/play/alternative 在已有基词时剔除。
- 缺数 / nodata 不是 0。发现层不用月搜≥500 淘汰。立项门槛仍为 KD≤31 等，未过线不得声称通过。
- 看板最多 40 词，允许更少，不凑数。游戏最多 10（首次快照不是新游，去掉 CS2/Dota 类无事件旧头部），视频最多 10（只收有原文依据的具体玩法；没有就留空，不为了“视频不为 0”回填种子）。书签X 最多 5，官方发布优先。
- 无本轮画面核验不得称独立成片。更早已用 watchVideo 核过的词（如 Jatayu）按教程去重保留，不得写成「从未核验」。Trends 无原始回执不得用 Semrush 缓存冒充本轮 Trends；本批丢失的优先词 Trends 禁止重查。
- AIsa 必须先 `aisa-batch-quote` 再 `aisa-batch-use`。密钥只读 `/workspace/xinci/.env` 的 `AISA_API_KEY`，禁止打印或打包。
- Higgsfield 只差分公开 sitemap：effects / apps / motion / mixed-media-presets。首次基线 `new=0`。
