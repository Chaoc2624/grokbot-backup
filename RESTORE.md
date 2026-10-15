# grokbot-backup 恢复说明

这是 Grok Bot 云电脑（box）上值得保留的脚本、配置、调研和文档的每日备份。仓库内路径与原机器一致：`workspace/...` 对应 `/workspace/...`，`home/box/...` 对应 `/home/box/...`。

## 包含
- `workspace/xbm`：X 书签助手、看板客户端（board_client.py）、xbm-tg 等脚本与结果
- `workspace/tg`：TG 群总结脚本、specs、工具、`digests/`（AI 总结，原始聊天记录未备份）
- `workspace/f50`、`workspace/router`、`workspace/wechat`、`workspace/lpx`、`workspace/play`、`workspace/handoff`、`workspace/kb-devices`、`workspace/ufiweb` 等：源码、调研、交接文档
- `workspace/loon_fixed_v3.lcf`（订阅 token 已替换为 `<REDACTED>`）
- `home/box/sand-data/workflows`：自定义 skill（如 freetoken-bots）
- `home/box/.pi/agent`（settings.json、models-store.json）、`home/box/agent-tools/relay`、`home/box/reference`、`.bashrc`、`.profile`
- `home/box/backup/sync.sh`、`backup_helper.py`：备份脚本本身

## 不包含（需要时自行重建）
- 密钥/凭证：`~/.ssh`、`~/.xbm/board.env`、所有 `*.env`、`*.pem`、`*secret*`、`*credential*`、`*token*` 文件、auth.json
- 登录态：`~/.tg`（Telegram 会话）、`~/.wechat`、浏览器 profile / cookie、`~/.config/gh`
- 聊天记录：`workspace/tg/data`、`workspace/tg/archive`、`~/.pi/agent/sessions`
- 依赖与产物：venv、node_modules、`__pycache__`、build/dist/out、二进制（mihomo、xray 等）、压缩包、PDF、截图
- 代理订阅与节点配置：`workspace/f50/subs`、`f50/config.yaml`、`router/t/config.yaml`、`workspace/subtask`、安装命令文件
- X 原始数据：`xbm/raw-*.json`、`bookmarks-raw.json`
- 已在 GitHub 的仓库：halo-board、UFI-TOOLS、min-skill、neko-master（需要时直接 git clone）
- `tp/tp.py`、`shared.md`、`tg/digests` 中的密码/token 在备份里已替换为 `<REDACTED>`，原文件未改动

## 在新机器上恢复
1. 克隆（任选其一）：
   - 部署密钥：把私钥放到 `~/.ssh/grokbot_backup`（chmod 600），然后
     `GIT_SSH_COMMAND="ssh -i ~/.ssh/grokbot_backup -o IdentitiesOnly=yes" git clone git@github.com:Chaoc2624/grokbot-backup.git ~/grokbot-backup`
   - 或 `gh auth login` 后 `gh repo clone Chaoc2624/grokbot-backup ~/grokbot-backup`
2. 放回原位：
   `rsync -a ~/grokbot-backup/workspace/ /workspace/`
   `rsync -a ~/grokbot-backup/home/box/ /home/box/`
3. 重建依赖：
   - `cd /workspace/tg && python3 -m venv venv && venv/bin/pip install telethon pillow`（按脚本 import 补齐）
   - wechat 等 Node 项目：在含 package.json 的目录执行 `npm install`
   - Pi：`npm i -g` 安装 pi 后使用恢复的 `~/.pi/agent/settings.json`
4. 重新填写密钥（通过加密输入框，不要贴到聊天里）：
   - `~/.xbm/board.env`（看板推送 token / 地址）
   - `/workspace/xinci/.env`、`/workspace/f50/*.env`、`/workspace/neko-agent/gl.env`
   - `/workspace/subtask/cfsm_secrets.env`、`/workspace/neko-agent/neko-master-credentials.txt`、`/workspace/router/secret.txt`
   - `/workspace/lightsail-singapore.pem`（Lightsail SSH 私钥）
   - 代理订阅（f50/subs、Loon 订阅 token）
   - `~/.ssh/grokbot_backup`（备份部署密钥）
5. 重新登录：Telegram（tg/qr_login.py 生成 `~/.tg` 会话）、微信 bridge（wechat/bind.py）、浏览器里的各网站、`gh auth login`。

## 运行备份
`/home/box/backup/sync.sh`
流程：按规则挑选文件 → 复制到 `/home/box/backup/repo` → 脱敏 → 严格密钥扫描（sk-、ghp_、github_pat_、AKIA、xox、私钥头，以及 password/token/secret/Bearer 赋值）→ 有命中立即中止并只打印 路径:行号 → commit → push 到 main（从不 force push）。
日志：`/home/box/backup/last.log`。失败时退出码非 0。
