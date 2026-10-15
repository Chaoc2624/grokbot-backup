# XBM 看板交接文档（x.omnitools.cc / xbm.omnitools.cc）

> 整理时间：2026-10-10（北京时间）。全部来自只读检查，未改动任何东西。文中不含任何密钥，需要的令牌、密码请向 Halo Z 索取。

## 1. 域名与入口
- `https://x.omnitools.cc` 和 `https://xbm.omnitools.cc` 是**同一个服务的两个域名**（不是跳转）：两者返回内容完全一致，都在 Cloudflare Tunnel 里指向同一个本地端口 `127.0.0.1:10091`。`x.` 是 10-08 新加的（cloudflared 配置备份名 `config.yml.bak.x-domain-20261008115446`）。
- 另有 `https://sub.omnitools.cc/board/...` 也指向同一服务（路径前缀 `/board`）。
- 走 Cloudflare（响应头 `server: cloudflare`），源站不对公网开放端口，靠 `cloudflared` 隧道。TLS 由 Cloudflare 终结，源站是纯 HTTP。
- 标签页靠 hash 区分，如 `#tg` 打开「💬 TG 群总结」。

## 2. 服务器
- RackNerd VPS，主机名 `racknerd-d092a9b`，IP `192.255.151.85`，Ubuntu（内核 6.8）。
- 登录：`ssh root@192.255.151.85`（密钥登录；共享电脑上已有可用密钥。同事需让 Halo Z 把其公钥加到服务器上，**不要拷贝现有私钥**）。
- 同机还跑着其他服务（xray 占 443、neko、radar、sub 等），改动时别碰。

## 3. 技术栈
- **后端**：单文件 Python，`/opt/xbm-board/app.py`，只用标准库（`http.server.ThreadingHTTPServer` + `sqlite3`），无框架、无依赖。
- **前端**：单文件 `/opt/xbm-board/index.html`（原生 HTML/JS，无构建），另有 `tg-login.html`（TG 登录页）。
- **数据库**：SQLite，`/opt/xbm-board/board.db`（WAL 模式）。表：`items, briefs, brief_items, radar_keywords, radar_runs, radar_items, tg_digests, tg_pull_jobs, tg_pull_summaries, events, _migrate`。
- **进程管理**：systemd `xbm-board.service`（`/etc/systemd/system/`），`Restart=always`，`MemoryMax=80M`，监听 `127.0.0.1:10091`，环境变量来自 `/opt/xbm-board/.env`。
- **反向代理**：没有 nginx/caddy，直接由 `cloudflared.service` 转发，配置 `/etc/cloudflared/config.yml`。
- **Git**：`/opt/xbm-board` **不是 git 仓库**，没有远程仓库。版本靠目录里的 `bak.*` 快照。
- 相关服务：`xbm-tg.service`（`/opt/xbm-tg`，只读 Telegram 拉取器，独立用户 `xbmtg`、受沙箱限制）。

## 4. 配置（只列变量名）
`/opt/xbm-board/.env`（权限 600）：`XBM_DB, XBM_PASSWORD, XBM_API_TOKEN, XBM_SECRET, XBM_PORT, XBM_BASE, XBM_PUBLIC`
`/opt/xbm-board/webhook.env`：`TG_SUMMARY_WEBHOOK_URL, TG_SUMMARY_WEBHOOK_KEY`
值请找 Halo Z 要，不要提交到任何仓库或聊天。

## 5. 鉴权与 API
- 浏览器：密码登录（`/login`、`/logout`），用 cookie 会话。
- 机器写入：请求头 `Authorization: Bearer <XBM_API_TOKEN>`。
- 主要路由（`app.py` 约 739–890 行）：
  - 公开/页面：`/`、`/healthz`、`/login`、`/logout`、`/tg-login`
  - 前端读取：`/api/items`、`/api/briefs`、`/api/radar`、`/api/tg`、`/api/tg/groups`、`/api/tg/raw`、`/api/tg/raw/msgs`、`/api/version`（用于轮询是否有新内容）
  - 代理写入（Bearer）：`/api/agent/ingest`（书签）、`/api/agent/brief`、`/api/agent/radar`（POST / DELETE `?label=`）、`/api/agent/tg`、`/api/agent/carryover`、`/api/agent/ids`
  - TG 登录/拉取：`/api/tg/login`、`/api/tg/login/qr`、`/api/tg/login/password`、`/api/tg/pull`、`/api/tg/pull/current`

## 6. 前端模块
- 📰 每日简报、待办书签、🔥 X 热词、💬 TG 群总结（`#tg`）。
- 自动刷新：每 60 秒轮询（`setInterval(poll,60000)`），有更新时显示「有 N 条新内容」提示，不自动重排页面。

## 7. 谁在往里写数据
| 写入方 | 工具 | 频率 |
|---|---|---|
| X 书签助手（AI 助手） | 共享电脑 `/workspace/xbm/board_client.py`（命令：ingest、brief、radar、radar-delete、carryover、ids） | 每天北京时间 10:00、22:00 |
| TG 群总结（AI 助手） | 共享电脑 `/workspace/tg/tg_digest_push.py` | 每 3 小时一次，并维护当日合并总结 |
| xbm-tg.service | 服务器本地 | 常驻 |
- 客户端优先走 `https://x.omnitools.cc`，失败时回退为 `ssh root@192.255.151.85` 后 curl `127.0.0.1:10091/board...`。
- 这两个助手的定时任务由 Grok Bot 平台调度，不在共享电脑或服务器的 crontab 里。**改 API 字段时必须保持兼容，否则这两路写入会坏。**

## 8. 部署 / 重启 / 回滚
没有 CI，手动部署：
```bash
# 1) 先备份
ssh root@192.255.151.85 'cd /opt/xbm-board && d=bak.$(date +%Y%m%d-%H%M%S) && mkdir $d && cp app.py index.html tg-login.html $d/'
# 2) 上传
scp app.py index.html root@192.255.151.85:/opt/xbm-board/
# 3) 重启（只改 index.html 也建议重启，以便更新版本号）
ssh root@192.255.151.85 'systemctl restart xbm-board && sleep 2 && curl -s 127.0.0.1:10091/healthz'
```
- 回滚：把某个 `bak.*` 目录里的文件拷回 `/opt/xbm-board/` 再重启。
- 日志：`journalctl -u xbm-board -f`；隧道：`journalctl -u cloudflared`。
- 改 cloudflared 后：`systemctl restart cloudflared`（会影响同机其他域名，先备份 config.yml）。

## 9. 备份
- root crontab：每天 04:41（服务器时区）运行 `/opt/xbm-board/backup.sh`，用 SQLite backup 生成 `backups/board-YYYY-MM-DD.db`，保留 30 天。
- 只在同一台机器上，**没有异地备份**。

## 10. 用户的界面偏好（必须遵守）
- 不能出现布局跳动或重新排序（新内容只提示「有 N 条新内容」，不自动插入/打乱）。
- 紧凑的、按日期分组的时间轴，**最新的在最上面**。
- 空的条目或模块直接隐藏，不要显示占位。
- 按钮要有文字标签，不要只有图标。
- 不要彩色左边框竖条。

## 11. 修改快速上手
1. 让 Halo Z 把你的 SSH 公钥加到服务器，并拿到看板登录密码（只读浏览用）。
2. 从服务器拉最新代码：`scp root@192.255.151.85:/opt/xbm-board/{app.py,index.html,tg-login.html} .`（**以服务器为准**，见下方问题 1）。
3. 本地运行：设置 `XBM_DB=./test.db XBM_PORT=10091 XBM_PASSWORD=... XBM_API_TOKEN=... XBM_SECRET=...` 后 `python3 app.py`，打开 `http://127.0.0.1:10091`。不要用生产库做测试。
4. 改完按第 8 节部署，刷新页面（Cmd+Shift+R）检查各标签页和手机端。
5. 改动后在共享电脑跑一次 `python3 /workspace/xbm/board_client.py ids` 确认写入接口仍可用。

## 12. 待解决问题 / 未确认事项
1. **代码版本不一致**：服务器上的 `index.html`（10-09 15:22 修改）比共享电脑 `/workspace/xbm/board` 和 `board-live` 里的副本新，`app.py` 相同。没有 git，建议先把服务器版本初始化成一个私有仓库再开始改。
2. 没有 git、没有 CI、没有异地备份。
3. `XBM_BASE`/`XBM_PUBLIC` 的具体作用、`/sub.omnitools.cc/board` 前缀的兼容逻辑未逐行确认。
4. `sub.omnitools.cc/board` 这条入口是否仍在使用未确认。
5. Cloudflare 侧（DNS 记录、Access、缓存规则）只能从响应头推断，没登录 Cloudflare 后台核实；账号归 Halo Z。
6. `webhook.env`（TG 总结 webhook）的接收方未核实。
