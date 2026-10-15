# 新词表格：建站词标注（2026-10-08 起）

看板「新词」每次扫描的表格里，被选为建站词的产品会高亮、带 🔑 建站词，按名次排在最上面，理由显示成同一行里的「建议：…」。其余产品按首发时间从新到旧排列。表格下面原来的关键词块已经去掉。

**原来的写法照样能用**：`keywords: [{"keyword","reason"}]` 会按名称自动匹配产品（不分大小写，忽略空格和标点，互相包含或词都出现在名称和描述里就算匹配）。没匹配上的关键词会单独显示成最上面的一行（名称写关键词，描述写理由，没有链接）。

**推荐的写法**：直接在产品上标出来，不靠自动匹配：

```json
"items": [
  {"name": "Claude Haiku 5.5", "desc": "…", "source": "@claudeai", "url": "https://x.com/…", "first_seen": "2026-10-08 02:01",
   "keyword_rank": 1, "keyword": "Claude Haiku 5.5", "reason": "全新型号名，开发者会集中搜价格、API 用法…"}
]
```

- `keyword_rank`（整数，1 = 最重要）、`keyword`（建站词本身，省略时用 name）、`reason`（建议理由）三个字段都可选，有 `keyword_rank` 或 `keyword` 就算建站词。
- 产品上标了、但 `keywords` 里没有的词，服务器会自动补进 `keywords`，热词榜照常计数。也可以两边都写，名次以产品上的 `keyword_rank` 为准。
- `first_seen` 最好写完整的 `YYYY-MM-DD HH:MM`，排序更准（只写 `MM-DD HH:MM` 也能排）。
- 推送命令不变：`python3 /workspace/xbm/board_client.py radar payload.json`
