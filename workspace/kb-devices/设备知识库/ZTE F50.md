---
title: 中兴 ZTE F50（Pro）随身 Wi‑Fi · UFI-TOOLS
aliases: [F50, F50 Pro, UFI-TOOLS, 随身WiFi]
tags: [设备知识库, 随身WiFi, ZTE, UFI-TOOLS, mihomo]
updated: 2026-10-09
---

# 中兴 ZTE F50（Pro）· UFI-TOOLS

返回 [[00 索引]] · 相关设备 [[GL.iNet GL-MT3600BE]]

## 设备概况

| 项目 | 内容 | 依据 |
|---|---|---|
| 型号 | 中兴 ZTE **F50 Pro**（5G 随身 Wi‑Fi，安卓系统，arm64） | `f50/config.yaml` 和 `relay.sh` 文件头都写的是「F50 Pro」 |
| 系统 / 固件 | 中兴原厂安卓系统，版本 **待确认**；已经拿到 root（插件都用 root 执行命令） | `maomao13.js` 里调用 `runShellWithRoot` |
| 管理工具 | **UFI-TOOLS**（kanoqwq/UFI-TOOLS，安卓包名 `com.minikano.f50_sms`）。共享电脑上的源码是 v4.1.5（上游 2026-09-19 的提交，没有本地修改）；F50 上实际装的版本 **待确认** | `/workspace/UFI-TOOLS` git，`app/build.gradle.kts` |
| 访问地址 | LAN 网段是 `192.168.0.0/24`，设备地址 `192.168.0.1`。mihomo 面板在 `http://192.168.0.1:7788/ui/`，局域网代理端口 `192.168.0.1:7890`。面板密钥不写在这里 | `f50/config.yaml` 文件头 |
| 角色 | 随身热点，在外面给手机、电脑上网。热点上的设备通过「猫猫」插件里的 mihomo 透明代理出去，分流规则和家里 GL 路由器一致 | `gen.py` |

> 这台 F50 没有电池，一直插 USB 供电，面板上的电池读数不准。

## 功能清单

1. **「猫猫」mihomo 透明代理插件**
   - 来源：UFI-TOOLS 插件商店里的 mihomo-tproxy 包（`/workspace/f50/mihomo-tproxy.zip`）。插件脚本留了一份在 `/workspace/maomao13.js`。
   - 装在 F50 的 `/data/clash/`：内核在 `Proxy/Clash.Core`，启停脚本是 `Scripts/Clash.Service` 加 `clashctl_arm64`，监听脚本是 `Clash.Inotify`。面板界面有 zashboard、metacubexd 和 dashboard 三套。另外带了 mosdns。
   - 开机自启：插件会把 `Clash.Service start` 和 inotifyd 两行写进 `/sdcard/ufi_tools_boot.sh`。
   - 改配置前插件会备份成 `/data/data/com.minikano.f50_sms/files/uploads/mm_config_backup_<时间>.yaml`。
   - 用的是 tproxy 模式（`cmfa-plugin: {mode: tproxy}`）。注意：这个模式**不代理 F50 本机发出的流量**。插件说明里写了，F50 自己的「短信转发到 Telegram」要另外设置走 7890 代理，或者换成 tun 模式。
2. **按家里路由器的规则生成的代理配置**（2026-10-08，由 `gen.py` 生成）
   - 一共 38 个策略组、784 条规则、20 个规则集，规则基本照搬 GL 路由器。
   - **节点来源**有 4 个：selfbuilt（自建 VPS，含洛杉矶 QQG）、xingji（星际穿越）、crosswall（CrossWall）、sakura（樱花猫）。都是每天更新一次，自动过滤剩余流量、到期这类信息行和 2 倍以上的倍率节点。
   - **出口**：「🚀 总出口」默认走「自动备用」。备用顺序是 洛杉矶QQG → 自建VPS → 星际穿越自动 → CrossWall自动 → 樱花猫自动 → 樱花猫，前一个不通就自动换下一个，每 120 秒检查一次。
   - **地区组**：美、日、新、港、台、韩、马、德、英、法，每组自动选最快节点。不放樱花猫，樱花猫只能手动选，或者作为备用的最后一档。
   - **服务组**：AI 只用美、洛杉矶QQG、新、日、台，不用香港。另外还有 Twitter、YouTube、Google、Netflix、Spotify、PayPal（美国优先）、Maya（新加坡优先），Apple 和 Microsoft 默认直连，广告拦截默认拒绝，漏网之鱼走总出口。
   - **Telegram 专用**：「Telegram自动」组按「Telegram新加坡 → 美 → 日 → 自动备用」的顺序自动切换，测速直接测 Telegram 的服务器，而不是通用测速地址。所有 Telegram 的域名和 IP 段都强制走 Telegram 组；旧的路由器规则会把它们发到总出口，这里已经改正。
   - **DNS**：用 redir-host 模式，监听 1053。海外 DNS 用 1.1.1.1 和 8.8.8.8 的加密 DNS，走「DNS出口」组（洛杉矶QQG → 新加坡 → 星际穿越 → CrossWall），每 90 秒用一次真实的 DNS 查询检测是否可用。机场订阅的域名单独设了 DNS 策略。
   - **不选「实验」节点**：CrossWall 带「实验」字样的节点在 10-08 出现过 TLS 握手失败和卡顿，所以地区组、Telegram 新加坡组和 CrossWall 自动组都不会选它们。
   - **广告拦截**：用 geosite 的 category-ads-all 规则，外加从 Loon 搬来的 128 条拦截 IP。
   - 去掉了路由器配置里和 gl-inet 相关的规则和 DNS 项，局域网 `192.168.0.0/24`、`.lan`、`.local` 都走直连。
3. **Wi‑Fi 中继和 alibaba-guest 自动认证（2026-10-09 已上线）**
   - wlan1 连上游 Wi‑Fi，wlan0 继续开热点，两边同时工作。
   - UFI 面板新增「WiFi 中继」插件：扫描选网、连接、断开；可填本机号、读短信验证码、全自动认证。认证模块平时收起，需要认证时才弹出。
   - alibaba-guest 认证已跑通，用 F50 自己的 SIM 收验证码，有效期 7 天。认证脚本 `/data/local/tmp/halo_portal_ali.sh`，中继工具 `/data/local/tmp/relay/relay.sh`。
   - 流量共享：中继在线且认证通过后，热点设备自动走上游 Wi‑Fi，猫猫出站也切到 wlan1；断开或认证失效自动退回蜂窝。后台每 30 秒检查一次，开机自启。IPv6 仍走蜂窝。
   - 猫猫会拦截上游 Wi‑Fi 回来的包导致认证失败，现在 wlan1 设为不经过猫猫，这条规则由后台循环每 30 秒补一次。
4. **面板与数据看板（2026-10-09）**
   - 新增「网络状态」插件；「系统状态总览」加了中文网口名、进程用途和开机脚本说明；原厂功能按钮移到功能列表顶部。
   - 修复数据看板内存、CPU 占用和频率为空：关闭的 4–7 号核心读取报错导致整组为空。核心保持关闭（用户的选择）。
5. **短信转发（2026-10-09）**：改为 SMTP 转发到用户 Gmail；营销短信按关键字和号码黑名单拦截，验证码和账单照常转发。Gmail 应用专用密码只存在面板设置里。
4. **研究过但没确认装上的插件**（2026-10-08 从插件商店下载来研究）：ADGuardHome 2.4、IPv6 设置、Mosdns 1.2、Tailscale 组网、U30/U20/F50 温控指示灯 1.4，都在 `f50/research/store/`。**是否已安装待确认。**

## 改动日志

> 新的在上。

### 2026-10-09 · Wi‑Fi 中继上线、自动认证、面板和短信转发（Grok总管 提供）
- Wi‑Fi 中继上线：wlan1 连上游、wlan0 保持热点；面板「WiFi 中继」插件可扫描、连接、断开、填本机号、读验证码、全自动认证。
- alibaba-guest 自动认证跑通（F50 自己的 SIM 收验证码，有效期 7 天）：`/data/local/tmp/halo_portal_ali.sh`、`/data/local/tmp/relay/relay.sh`。
- 流量共享：认证通过后热点和猫猫出站走 wlan1，失效自动退回蜂窝；每 30 秒检查，开机自启；IPv6 走蜂窝。
- 修猫猫拦截上游回包：wlan1 不经过猫猫，由后台循环每 30 秒补规则。
- 面板：新增「网络状态」插件；系统状态总览加中文网口名、进程用途、开机脚本说明；原厂按钮移到列表顶部。
- 数据看板：修复内存、CPU 占用和频率为空（4–7 号核心关闭导致读取报错），核心保持关闭。
- 短信转发：改用 SMTP 发到 Gmail，营销短信按关键字和号码黑名单拦截。
- 同日早些时候：准备 arm64 版 iw，写 `relay.sh`，11:23 抓取分析 alibaba-guest 认证页，并反编译 UFI-TOOLS 研究插件接口。
- 备份：Mac `~/agent-tools/ufi-plugins/custom_head.bak-*`；网络规则备份在设备 `/sdcard/relay/`。
- 回滚：`relay.sh disconnect` 加 `auto off`，恢复 custom_head 备份。

### 2026-10-08 18:41 · 第二版：DNS 出口和避开「实验」节点
- `gen.py` 改了这些：
  - 新增「DNS出口」组，海外 DNS 改走这个组，不再走总出口。
  - 「实验」节点不进地区组、Telegram 新加坡组和 CrossWall 自动组。
  - CrossWall 自动组改成每 300 秒常驻测速（不再是用到才测）。
  - Telegram 测速地址改成 `https://api.telegram.org`。
- 备份：`config.yaml.bak-20261008-181356`、`gen.py.bak-20261008-184102`。
- 验证：在面板里看「DNS出口」有没有选中节点；看「实验」节点是否没出现在自动组里。
- 回滚：把 `config.yaml.bak-20261008-181356` 用猫猫插件的「编辑配置」导回去。

### 2026-10-08 约 18:13 · 第一版：Telegram 专用组
- `gen.py` 新增「Telegram自动」和「Telegram新加坡」两个组，测速直接测 Telegram 的服务器（第一版测的是 149.154.167.51），所有 Telegram 域名和 IP 段都改走 Telegram 组。
- 备份：`gen.py.bak-20261008-181356`。

### 2026-10-08 14:00–14:47 · 从 GL 路由器配置生成 F50 配置
- 下载了猫猫插件包（mihomo-tproxy.zip）和 mihomo v1.19.19，抓了 4 个节点订阅存到 `f50/subs/`（里面有订阅链接，属于敏感文件）。
- `gen.py` 读取 `src/gl-work-router.yaml` 和 `subs/urls.env`，生成 `f50/config.yaml`。
- 14:47 在共享电脑上试跑过一次（`/tmp/f50t/`，改成本地端口），能正常加载。日志只提示订阅没返回流量信息，不影响使用。
- 怎么用到 F50 上：在猫猫插件的「编辑配置」里导入 `config.yaml`，插件会先自动备份。**实际导入的时间和结果待确认。**

## 相关文件与位置

**共享电脑（box）**
- `/workspace/f50/build/gen.py`：配置生成器，带两个备份
- `/workspace/f50/config.yaml`：生成的 F50 配置，带一个备份。**里面有面板密钥和订阅链接，属于敏感文件**
- `/workspace/f50/src/gl-work-router.yaml`：模板，GL 路由器的配置
- `/workspace/f50/subs/`：订阅原文和链接（`urls.env`），**敏感，权限 700**
- `/workspace/f50/bundle/`：猫猫插件解包后的内容，包括 Proxy、Scripts、Tools/mosdns
- `/workspace/f50/mihomo-1.19.19`、`mihomo-tproxy.zip`
- `/workspace/f50/research/store/`：从插件商店下载的插件脚本
- `/workspace/maomao13.js`：猫猫插件脚本
- `/workspace/UFI-TOOLS/`：上游源码 v4.1.5（含 API_Doc.md、User_Doc.md）
- `/workspace/ufi/`（反编译结果）、`/workspace/ufiweb/grep1.txt`、`/workspace/ufi_rg_out.txt`
- `/home/box/agent-tools/relay/relay.sh`（不完整）、`/tmp/iwbin/iw-arm64`

**F50 上**
- `/data/clash/`：Proxy/config.yaml、Proxy/Clash.Core、Scripts/、Tools/
- `/sdcard/ufi_tools_boot.sh`：开机自启
- `/data/data/com.minikano.f50_sms/files/`：UFI-TOOLS 的工作目录，里面有 curl、jq、ufi_req 和 uploads/ 配置备份
- `/data/local/tmp/relay/`、`/data/local/tmp/busybox`、`/data/local/tmp/iw`、`/sdcard/halo_portal_fail`

## 待办 / 已知问题

- [ ] 确认 F50 上实际的系统版本和 UFI-TOOLS 版本。
- [ ] 确认 10-08 生成的 config.yaml（第二版）已经导入 F50 并在跑。
- [x] Wi‑Fi 中继和 alibaba-guest 自动认证已上线（2026-10-09）。
- [ ] tproxy 模式不代理 F50 自己发出的流量。如果要用 F50 的「短信转发到 Telegram」，要么让它走 7890 代理，要么换成 tun 模式。
- [ ] 订阅链接和面板密钥目前以明文放在共享电脑的 `f50/subs/`、`f50/config.yaml` 里，以后分享或推到 GitHub 时要排除。
- [ ] F50 和路由器的规则都是从同一份来的，以后改分流规则时要同步改 `gen.py` 的生成逻辑，或者重新导出路由器配置再生成一次。

#随身WiFi #UFI-TOOLS #mihomo #ZTE
