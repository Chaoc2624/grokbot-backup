# TG 总结里的图片：字段说明（2026-10-21）

只存图，不做 AI 看图；总结正文 `content` 一字不改。不推看板。

## 1. 存储
```
/workspace/tg/media/<YYYY-MM-DD>/<chat_key>/<msg_id>.jpg     大图，长边 ≤1280px，JPEG q80
/workspace/tg/media/<YYYY-MM-DD>/<chat_key>/<msg_id>_t.jpg   缩略图，长边 ≤320px，JPEG q70
```
- 只抓 photo，以及 mime 为 jpeg/png/webp、≤8 MB 的图片文件；跳过视频、GIF、贴纸、其他文件。
- 按 chat+msg_id 去重：文件已存在就不再下载。单张下载超时 45 s 就跳过。
- 日期 = 消息时间（Asia/Shanghai）。所有 path 都相对 `/workspace/tg`，以 `media/` 开头。

## 2. 原始数据 data/<date>/hourly/<HH>.json
有图的消息会多一个字段（原来的 `media: "photo"` 不变）：
```json
"image": {"path": "media/2026-10-21/haiwufang/100852.jpg", "thumb": "media/2026-10-21/haiwufang/100852_t.jpg",
          "w": 1280, "h": 960, "bytes": 81234}
```

## 3. 总结 JSON（hourly 片段、6h 块 00-06…、daily.json）
每个 `items[]` 里可能多一个 `images` 数组（没有图就没有这个字段）：
```json
"images": [
  {"path": "media/2026-10-21/haiwufang/100852.jpg", "thumb": "media/2026-10-21/haiwufang/100852_t.jpg",
   "w": 1280, "h": 960, "msg_id": 100852, "chat": "haiwufang", "time": "2026-10-21 14:33:26",
   "sender": "LXF🕊", "link": "https://t.me/...",
   "line": "> LXF🕊：在哪查的… {{2026-10-21 14:33:26}}"}
]
```
- `line`：这张图所属发言行的**完整原文**（去掉首尾空格后和 `content` 里那一行完全相同）。
  匹配规则：发言人名一致 + 消息时间落在该行 `{{t}}` / `{{t1~t2}}` 范围内。
- `line: null`：该时段内没有被引用的图（hourly / 6h 每组最多 8 张；daily 不放）。
- 6h 块 / daily 由 `tg_merge6h.py` 和 `tools/attach_images.py` 重新计算，不依赖片段里的 images。

## 4. 看板（halo-board, Node）怎么显示
1. 拿图：二选一
   - 静态服务：看板能访问本机时，把 `/workspace/tg/media` 挂成 `/tg-media`（express: `app.use('/tg-media', express.static(dir, {maxAge:'7d', immutable:true}))`），URL = `/tg-media/` + path 去掉开头的 `media/`。
   - 看板在别的机器（x.omnitools.cc）：需要同步文件（rsync/对象存储上传），这一步现在没做，等你决定。
2. 渲染：逐行渲染 `content` 时，把每行 `trim()` 后的文本当 key，`images.filter(i => i.line === key)` 的缩略图（thumb）显示在该发言下面，点击开大图（path），可再附 `link` 跳 Telegram 原消息。
3. `line === null` 的图放在该组底部一个 "其他图片" 缩略图条。
4. 用 `w`/`h` 先占位，避免页面跳动；thumb 用 `loading="lazy"`。

## 5. 命令
- `tg_fetch.py ...` 默认抓图；`--no-images` 或环境变量 `TG_NO_IMAGES=1` 关闭；`TG_MEDIA_DIR` 改存储目录（测试用）。
- `tools/backfill_images.py data/<d>/hourly/<HH>.json [--out X]`：给已抓的数据补图。
- `tools/attach_images.py <digest.json> [--data-dir D] [--out X] [--max-extra N]`：把图挂到总结 JSON。
