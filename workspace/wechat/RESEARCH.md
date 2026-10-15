# iLink（微信 ClawBot）协议调研 —— 2026-10-09

主要依据：腾讯官方插件 **`@tencent-weixin/openclaw-weixin` v2.4.9**（npm，作者 Tencent，MIT，2026-09-17 发布）。
TS 源码已解包在 `/workspace/wechat/src/package/`。
- npm：https://www.npmjs.com/package/@tencent-weixin/openclaw-weixin
- tarball：https://registry.npmjs.org/@tencent-weixin/openclaw-weixin/-/openclaw-weixin-2.4.9.tgz

标签：**[源码]** = 官方插件源码里直接读到；**[实测]** = 2026-10-09 01:16（UTC+8）在 box 上匿名调用过一次；**[社区]** = 第三方逆向文档或 issue；**[推断]** = 我的推论。

## 0. 通用

| 项目 | 值 | 来源 |
|---|---|---|
| 业务 base URL | `https://ilinkai.weixin.qq.com`（扫码登录固定用这个；登录后改用 `confirmed.baseurl`） | [源码] `src/auth/accounts.ts` DEFAULT_BASE_URL；`src/auth/login-qr.ts` FIXED_BASE_URL |
| 媒体 CDN | `https://novac2c.cdn.weixin.qq.com/c2c`（纯文本用不到） | [源码] accounts.ts CDN_BASE_URL |
| 传输 | HTTPS + JSON，只有出站请求，没有 webhook，也不需要公网端口 | [源码] api.ts |

**所有 POST 请求的请求头** [源码] `src/api/api.ts` 里的 `buildHeaders` 和 `buildCommonHeaders`：

```
Content-Type: application/json
AuthorizationType: ilink_bot_token
Authorization: Bearer <bot_token>          # 登录后才有；get_bot_qrcode 不带
X-WECHAT-UIN: base64(str(random_uint32))   # 每次请求重新随机，例如 "MjE3ODM0OTcxOA=="
iLink-App-Id: bot                          # 来自 package.json 的 "ilink_appid": "bot"
iLink-App-ClientVersion: 132105            # uint32 (major<<16)|(minor<<8)|patch，2.4.9 -> 132105
SKRouteTag: <可选>                          # 只在配置了 routeTag 时才带
```

**GET 请求**（`get_qrcode_status`）只带 `iLink-App-Id` 和 `iLink-App-ClientVersion`。[源码] apiGetFetch

**每个 POST body 都要带** `"base_info": {"channel_version": "2.4.9", "bot_agent": "OpenClaw"}`。bot_agent 是类似 UA 的 `Name/Version`，只用于观测，可以自己填。[源码] buildBaseInfo；types.ts BaseInfo

**超时** [源码]：getupdates 35s，get_qrcode_status 35s，sendmessage 15s，getconfig 和 sendtyping 10s。

## 1. 扫码登录和绑定

### 1.1 取二维码 [源码] login-qr.ts `fetchQRCode`；[实测]

```
POST https://ilinkai.weixin.qq.com/ilink/bot/get_bot_qrcode?bot_type=3
Headers: 上面的 POST 头（不带 Authorization）
Body: {"local_token_list": []}   # 本地已有的 bot_token，最多 10 个，最新的在前；没有就传空数组
```

实测响应（HTTP 200，qrcode 已打码）：

```json
{"qrcode": "<32 位字符串>",
 "qrcode_img_content": "https://liteapp.weixin.qq.com/q/7GiQu1?qrcode=<同上>&bot_type=3",
 "ret": 0}
```

- `qrcode`：轮询状态用的 id。
- `qrcode_img_content`：一个 URL，不是图片。插件把它渲染成终端二维码，并提示「若二维码未能显示或无法使用，你可以访问以下链接以继续」，然后打印同一个 URL。[源码] `displayQRCode`
- **备用链接就是这个 URL**（liteapp.weixin.qq.com），可以在微信里直接打开。
  - 「打开后能在微信内确认」是 [推断]，依据是插件的文案和域名。我没有实际打开过。

### 1.2 轮询状态 [源码] login-qr.ts `pollQRStatus` 和 `waitForWeixinLogin`

```
GET {base}/ilink/bot/get_qrcode_status?qrcode=<qrcode>[&verify_code=<数字>]
Headers: 只带 iLink-App-Id 和 iLink-App-ClientVersion
```

- 这是长轮询，客户端超时 35s。超时或网关错误（例如 Cloudflare 524）都当作 `wait` 处理。
- 每轮之间 sleep 1s。整体默认等待 480s。

| status | 含义和处理 |
|---|---|
| `wait` | 还没扫，继续轮询 |
| `scaned` | 已扫码，等手机上确认 |
| `need_verifycode` | **手机微信上会显示一串数字**，需要用户输入，下一次轮询带上 `&verify_code=` |
| `verify_code_blocked` | 数字输错太多次，需要换新二维码 |
| `scaned_but_redirect` | 机房切换：之后用 `https://{redirect_host}` 继续轮询 |
| `binded_redirect` | 这个 bot 已经绑定过本端，不会下发新凭证，旧凭证继续有效 |
| `expired` | 二维码过期，重新调用 get_bot_qrcode。插件最多刷新 3 次 |
| `confirmed` | 成功，返回下面这些字段 |

`confirmed` 的响应：

```json
{"status": "confirmed",
 "bot_token": "...",
 "ilink_bot_id": "xxxx@im.bot",
 "baseurl": "https://...",
 "ilink_user_id": "xxxx@im.wechat"}
```

- `ilink_user_id` 是**扫码人**的 id。插件提示把它加进 allowFrom，可以直接当作「只认这一个人」的白名单。
- `bot_token`、`ilink_bot_id`、`baseurl` 都要持久化保存。

### 1.3 二维码有效期

- 插件本地 TTL 是 `ACTIVE_LOGIN_TTL_MS = 5 * 60_000`（5 分钟）。[源码]
- 服务端没有单独返回有效期字段，过期时 status 会变成 `expired`。[源码] + [社区] Chrysochrome spec §3
- 所以「约 5 分钟」是插件的本地设定。服务端的实际过期时间没有公开，以 `expired` 为准。

## 2. getupdates 长轮询收消息 [源码] api.ts `getUpdates`、monitor.ts、types.ts

```
POST {base}/ilink/bot/getupdates
Headers: 完整 POST 头（含 Bearer token）
Body: {"get_updates_buf": "<上次返回的值，首次传空串>", "base_info": {...}}
```

响应：

```json
{"ret": 0,
 "msgs": [{
   "seq": 1, "message_id": 9812451782375,
   "from_user_id": "xxxx@im.wechat", "to_user_id": "xxxx@im.bot",
   "client_id": "...", "create_time_ms": 1760000000000, "session_id": "...",
   "message_type": 1, "message_state": 2,
   "context_token": "AARzJWAF...==",
   "item_list": [{"type": 1, "text_item": {"text": "你好"}}]
 }],
 "get_updates_buf": "<新游标>",
 "longpolling_timeout_ms": 35000}
```

**游标怎么推进**
- 只有当返回的 `get_updates_buf` 非空时，才保存并用于下一次请求。
- 插件把它落盘，重启后从上次位置继续。[源码] monitor.ts L152-156；storage/sync-buf.ts

**超时怎么设**
- 如果响应带了 `longpolling_timeout_ms`，下一轮就用它做超时。
- 客户端超时属于正常情况，原样拿旧游标重试即可。

**错误怎么处理** [源码] monitor.ts
- `ret` 或 `errcode` 非 0 时：
  - 等于 -14：暂停这个账号 1 小时。
  - 其他错误：重试间隔 2s，连续失败 3 次后退避 30s。

**消息类型**
- `message_type`：1=USER，2=BOT。
- `message_state`：0=NEW，1=GENERATING，2=FINISH。
- `item.type`：1 文本、2 图片、3 语音（`voice_item.text` 是语音转出的文字）、4 文件、5 视频、11/12 是工具调用。
- 还有 `ref_msg`，表示引用消息。

**ID 解析**：`message_id`、`msg_id`、`svr_id` 是 uint64，插件按字符串无损解析。

## 3. sendmessage 发消息 [源码] send.ts `buildTextMessageReq`、api.ts `sendMessage`

```
POST {base}/ilink/bot/sendmessage
Headers: 完整 POST 头
```

Body：

```json
{"msg": {"from_user_id": "",
         "to_user_id": "xxxx@im.wechat",
         "client_id": "openclaw-weixin:1760000000000-a1b2c3d4",
         "message_type": 2,
         "message_state": 2,
         "context_token": "<该用户最近一条入站消息的 context_token>",
         "item_list": [{"type": 1, "text_item": {"text": "纯文本回复"}}]},
 "base_info": {"channel_version": "2.4.9", "bot_agent": "OpenClaw"}}
```

- 响应是 `{"message_id": "...", "ret": 0}`。`ret` 非 0 时插件直接抛错。
- `client_id` 的格式是 `前缀:毫秒时间戳-8位hex`，只要求唯一。[源码] util/random.ts
- `item_list` 每次只放 1 个 item。[源码] send.ts 注释
- 插件把长文本按 4000 字切分（`textChunkLimit: 4000`）。[源码] channel.ts L269。这是插件自己的设定，服务端硬上限不明。
- 插件有一个 Markdown 过滤器，会把不支持的 Markdown 剥掉。[源码] markdown-filter.ts。这说明微信不渲染 Markdown，应该发纯文本。

## 4. 错误码和限制

| 码 | 含义 | 来源 |
|---|---|---|
| `-14`（`ret` 或 `errcode`） | **bot token 失效或过期**（STALE_TOKEN_ERRCODE）。2.4.6 版的变更日志写明「-14 表示 token 失效，而非 session 过期」。插件的做法是暂停这个账号的所有请求 1 小时；社区和插件重新登录流程的做法是重新扫码 | [源码] session-guard.ts；CHANGELOG.zh_CN.md 2.4.6；monitor.ts |
| `ret=-2`（sendmessage） | context_token 过期（用户长时间没发消息）或参数错误 | [社区] QwenPaw issue #4477；Chrysochrome spec §6 |
| 每个 context_token 约 10 条回复 | 超过后返回 `{"ret": -2}`，等用户再发一条消息才会恢复 | [社区] QwenPaw #4477 |
| 24 小时窗口 | 用户超过 24 小时没发消息，bot 就发不出去了 | [社区] weilink README、openilink.com |
| 频率限制 | 官方源码里没有找到明确的频率限制常量 | — |

## 5. 是否必须用户先发消息

- **必须。** context_token 只会出现在 getupdates 返回的入站消息里。[源码] inbound.ts 注释写着「issued per-message by the Weixin getupdates API and must be echoed verbatim in every outbound send」。
- 插件在缺 token 时只打 warn，仍然会发送。但社区实测：不带 token 时接口返回 200，消息却不会投递。[社区] 简书 e51d38d1b8cc
- 所以绑定以后，用户要先给 ClawBot 发一句话，并且每次回复都用该用户最新的 context_token。

## 6. typing 和 getconfig（可选）

- `POST ilink/bot/getconfig`，body `{"ilink_user_id", "context_token", "base_info"}`，返回 `{"ret": 0, "typing_ticket": "<base64>"}`。[源码]
- `POST ilink/bot/sendtyping`，body `{"ilink_user_id", "typing_ticket", "status": 1 正在输入 / 2 取消}`。插件每 5s 发一次保活。[源码] process-message.ts
- **这两个是可选的**：getconfig 失败时插件只记日志（ignored），typingTicket 为空时就跳过 typing，消息照常收发。[源码] config-cache.ts、process-message.ts L329
  - 有一份社区文档写 getconfig「必须调用」，和官方源码的行为不一致。
- `ilink/bot/msg/notifystart` 和 `notifystop` 是插件启动和停止时的通知，body 只有 base_info。可选。

## 7. 对我们转发程序的建议 [推断]

1. 白名单：`from_user_id == confirmed.ilink_user_id` 的消息才处理，并且只处理 `message_type == 1`。
2. 每条入站消息都把 `context_token` 落盘（按 user 存最新的一个），回复时读出来用。
3. 遇到 -14：停止轮询，提醒用户重新扫码（插件本身的做法是暂停 1 小时）。
4. 遇到 `ret=-2`：提示「请在微信里再发一句话」，不要死循环重试。
5. 重新扫码后清空本地的 get_updates_buf 和 context_token。[社区] spec §4

## 来源

- 官方插件源码（npm tarball，已下载到 `/workspace/wechat/src/package`）：`src/api/api.ts`、`src/api/types.ts`、`src/auth/login-qr.ts`、`src/auth/accounts.ts`、`src/api/session-guard.ts`、`src/api/config-cache.ts`、`src/monitor/monitor.ts`、`src/messaging/send.ts`、`src/messaging/inbound.ts`、`src/messaging/process-message.ts`、`src/channel.ts`、`CHANGELOG.zh_CN.md`、`package.json`
- DeepWiki（基于 Tencent/openclaw-weixin 仓库）：https://deepwiki.com/Tencent/openclaw-weixin/7.1-ilink-bot-api-client
  - 注意：它把发送接口写成了 `sendmsg`，源码里实际是 `sendmessage`。
- 社区协议规范：https://github.com/Chrysochrome/ilink-bot-server/blob/main/docs/protocol-spec.md
- epiral/weixin-bot PROTOCOL.md：https://github.com/epiral/weixin-bot/blob/main/PROTOCOL.md
- SiverKing Python 文档：https://github.com/SiverKing/weixin-ClawBot-API/blob/main/weixin-openclaw-api-py-docs.md
- 简书逆向文章：https://www.jianshu.com/p/e51d38d1b8cc
- QwenPaw issue #4477（ret=-2，以及每个 token 10 条的限制）：https://github.com/agentscope-ai/QwenPaw/issues/4477
- weilink（24h 窗口）：https://github.com/Oaklight/weilink
- OpeniLink 背景：https://openilink.com/docs/guide/background
