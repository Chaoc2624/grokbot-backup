# 2026-11-15 新 AI 视频玩法词验证报告

## 1. 标题与范围
- **任务说明**：这是 2026-11-15 新 AI 视频玩法词验证，并非重跑晚间 60 词。
- **时区说明**：拉取时间为台北时间（Asia/Taipei，UTC+8）。

## 2. 方法
- **Semrush 查询规则**：美国库先查 overview，无行则不查 KD；Jatayu 等同时分查印度库，但美印两库明确区分，禁止相加。ERROR 50 NOTHING FOUND 表示无覆盖，不得视作月搜 0。
- **Google Trends 方法**：使用 DataForSEO 官方预设 `past_30_days`（API 映射至 `today 1-m`，覆盖 2026-10-15 至 2026-11-15 日点）和 `past_90_days`（API 映射至 `today 3-m`，覆盖 2026-08-15 至 2026-11-15 日点）。`past_7_days` 文档支持但本轮未跑。
- **对比与归一化规则**：同请求最多 5 词、同地区同时窗才可比。中间锚词 `ai photo to video` 已证实可在所有测试地区和时间窗查询。宽基准 `ai video generator` 会压扁小词，因此候选词与中间锚词同请求对比，而不是与宽基准同请求对比。0-100 是相对指数，不是月搜。
- **数据完整性**：2026-11-15 当日点带有 `missing_data=true`，不得当作完整日处理。

## 3. Semrush 结果表
包含 7 个确切拼写：
- `Jatayu AI video`
- `Jatayu AI video generator`
- `AI lion ride`
- `AI lion ride generator`
- `lion riding AI template`
- `Sheru Bhai AI`
- `King Jin AI trend`

- **美国库 (US)**：全部 7 个词均无覆盖（`ERROR 50 NOTHING FOUND`），费用 \$0。
- **印度库 (IN)**：全部 7 个词均无覆盖（`ERROR 50 NOTHING FOUND`），费用 \$0。
- **关键词难度 (KD)**：未运行（因美/印库均无 overview 行，故不查 KD/CPC）。

## 4. Trends 结果
### 锚词组证实（中间锚与宽基准）
- 中间锚 `ai photo to video` 证实可在每种地理位置和时间窗查询。
- 宽基准 `ai video generator` 指数更大，会压扁小词。例如在美国 30 天请求中，中间锚均值 6（最大值 9）、`image to video` 均值 58（最大值 70）、`ai video generator` 均值 88（最大值 100）。

### 各词详细结果（印度/美国/全球对比）
- **Sheru Bhai AI**：
  - **美国**：30 天与 90 天均为 `null`。
  - **印度**：在 30 天印度/Jatayu 同请求中，11 月 1 日起连续上升（15/32 天非空）。完整日峰值为 2026-11-11 的 84（当天同请求中间锚为 37）。90 天窗内显示，9 月仅有孤立点（2026-09-04 值为 16；2026-09-22 值为 53），连续波发生在 11 月。
  - **全球 (WW)**：30 天请求中可见 11 月上升（11-01 至 11-14 完整日为 6,6,6,6,6,8,11,11,18,28,43,44,39,39，完整日峰值 11-12 为 44；部分日 11-15 为 48。同请求中间锚完整日约 55-68。不可与印度请求中的 84 直接比较）。
- **Jatayu AI video**：
  - **美国**：30 天全为 `null`；90 天仅有一个孤立日（2026-09-16 值为 51，当天中间锚为 `null`），无连续序列。
  - **印度**：30 天和 90 天请求中，目前仅有 2026-11-14 完整日值为 9，11-15 部分日值为 33/34，无更早点。
  - **全球**：2026-11-14 完整日值为 5，11-15 部分日值为 22。
- **Jatayu AI video generator**：
  - **美国**：30 天全为 `null`；90 天仅有单日孤立点（2026-10-01 值 65，当天中间锚 100）。
  - **印度**：仅 2026-11-15 部分日可见（30 天请求中值为 2，90 天请求中值为 1）。
  - **全球**：部分日 11-15 值为 1 或字面量 0（非 `null`）。
- **King Jin AI trend**：
  - **美国、全球**：30 天与 90 天全为 `null`。
  - **印度**：30 天全为 `null`；90 天仅有单日孤立点（2026-09-05 值 22），无 11 月波形。
- **Lion 词组（`AI lion ride`, `AI lion ride generator`, `lion riding AI template`）**：
  - **Semrush**：美印两库均无覆盖。
  - **印度、全球**：30 天与 90 天全为 `null`。
  - **美国**：30 天全为 `null`；90 天仅有零星孤立点（`AI lion ride` 在 2026-10-02 值为 56；`AI lion ride generator` 在 2026-10-07 和 2026-10-20 值为 51），`lion riding AI template` 无任何点，无 11 月波形。

## 5. 费用
- **预算上限**：\$0.50
- **本轮实扣**：\$0.198
- **费用拆解**：
  - Semrush 7 词美库 Overview（报价 \$0.007，实扣 \$0）
  - Semrush 7 词印库 Overview（报价 \$0.007，实扣 \$0）
  - Semrush KD（未运行，实扣 \$0）
  - Google Trends 18 次调用（每次报价/实扣 \$0.011，18 次合计 \$0.198，覆盖 `past_30_days` 与 `past_90_days` 的美国、印度、全球）

## 6. 建议
基于多指标约束（Semrush 无覆盖、Trends 相对指数不能直接等于月搜、部分日不完整、视频流复刻证据需等待其他 Worker 归纳），各项结论如下：
- **Sheru Bhai AI**：**可立项（有约束）**。有明显的印度向 11 月连续上升曲线（峰值 84），但 Semrush 无覆盖、美国无序列，且需等待视频流复刻证据。
- **Jatayu AI video**：**观察**。仅在 11 月 14 日出现单个完整日点（值为 9），尚无成熟趋势。
- **Jatayu AI video generator**：**观察/暂缓**。仅见部分日零星微弱数据。
- **King Jin AI trend 与三个 lion 确切拼写**：**放弃/暂缓这些写法**。低数据并非无需求，但这几个确切拼写目前缺少可比较的连续序列。

## 7. 看板与快照
- **未合并看板**：本报告未合并其他看板。
- **原始快照目录**：`/workspace/xinci/_ai_video_kw_20261115/`
- **官方 Trends 验证链接（原样完整 URL，不改写为短链）**：
  - `https://trends.google.com/trends/explore?hl=en&geo=US&date=today%201-m&q=ai%20photo%20to%20video,image%20to%20video,ai%20video%20generator`
  - `https://trends.google.com/trends/explore?hl=en&geo=US&date=today%201-m&q=Jatayu%20AI%20video,Jatayu%20AI%20video%20generator,Sheru%20Bhai%20AI,King%20Jin%20AI%20trend,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=US&date=today%201-m&q=AI%20lion%20ride,AI%20lion%20ride%20generator,lion%20riding%20AI%20template,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=IN&date=today%201-m&q=ai%20photo%20to%20video,image%20to%20video,ai%20video%20generator`
  - `https://trends.google.com/trends/explore?hl=en&geo=IN&date=today%201-m&q=Jatayu%20AI%20video,Jatayu%20AI%20video%20generator,Sheru%20Bhai%20AI,King%20Jin%20AI%20trend,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=IN&date=today%201-m&q=AI%20lion%20ride,AI%20lion%20ride%20generator,lion%20riding%20AI%20template,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&date=today%201-m&q=ai%20photo%20to%20video,image%20to%20video,ai%20video%20generator`
  - `https://trends.google.com/trends/explore?hl=en&date=today%201-m&q=Jatayu%20AI%20video,Jatayu%20AI%20video%20generator,Sheru%20Bhai%20AI,King%20Jin%20AI%20trend,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&date=today%201-m&q=AI%20lion%20ride,AI%20lion%20ride%20generator,lion%20riding%20AI%20template,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=US&date=today%203-m&q=ai%20photo%20to%20video,image%20to%20video,ai%20video%20generator`
  - `https://trends.google.com/trends/explore?hl=en&geo=US&date=today%203-m&q=Jatayu%20AI%20video,Jatayu%20AI%20video%20generator,Sheru%20Bhai%20AI,King%20Jin%20AI%20trend,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=US&date=today%203-m&q=AI%20lion%20ride,AI%20lion%20ride%20generator,lion%20riding%20AI%20template,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=IN&date=today%203-m&q=ai%20photo%20to%20video,image%20to%20video,ai%20video%20generator`
  - `https://trends.google.com/trends/explore?hl=en&geo=IN&date=today%203-m&q=Jatayu%20AI%20video,Jatayu%20AI%20video%20generator,Sheru%20Bhai%20AI,King%20Jin%20AI%20trend,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&geo=IN&date=today%203-m&q=AI%20lion%20ride,AI%20lion%20ride%20generator,lion%20riding%20AI%20template,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&date=today%203-m&q=ai%20photo%20to%20video,image%20to%20video,ai%20video%20generator`
  - `https://trends.google.com/trends/explore?hl=en&date=today%203-m&q=Jatayu%20AI%20video,Jatayu%20AI%20video%20generator,Sheru%20Bhai%20AI,King%20Jin%20AI%20trend,ai%20photo%20to%20video`
  - `https://trends.google.com/trends/explore?hl=en&date=today%203-m&q=AI%20lion%20ride,AI%20lion%20ride%20generator,lion%20riding%20AI%20template,ai%20photo%20to%20video`
