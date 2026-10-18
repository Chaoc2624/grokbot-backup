---
title: GL.iNet GL-MT3600BE（Beryl 7）
aliases: [GLI net 3600B, MT3600, GL-MT3600BE, Beryl 7, GL 路由器]
tags: [设备知识库, 路由器, GL-iNet, OpenClash, mihomo]
updated: 2026-10-09
---

# GL.iNet GL-MT3600BE（Beryl 7）

返回 [[00 索引]] · 相关设备 [[ZTE F50]]

## 设备概况

| 项目 | 内容 | 依据 |
|---|---|---|
| 型号 | **GL-MT3600BE（Beryl 7）**，Wi‑Fi 7 双频旅行路由器 | 配置文件头写的是「GL-MT3600BE」；Neko 后端名为「GL-MT3600BE OpenClash」；软件源路径是 `mt7987a`；Wi‑Fi 名是 MT3600-WIFI7 |
| 硬件（官网） | 联发科 MT7987A 四核 A53，2.0GHz；内存 512MB DDR4；闪存 512MB NAND；2 个 2.5G 网口；1 个 USB 3.0 | [GL.iNet 官网](https://www.gl-inet.com/en-us/products/gl-mt3600be)、[OpenWrt Wiki](https://openwrt.org/toh/gl.inet/gl-mt3600be) |
| 固件 | GL 4.x 固件，基于 OpenWrt 21.02，用 fw3/iptables 防火墙；软件源为 `fw.gl-inet.com/releases/v21.02-SNAPSHOT/mt7987a`。具体版本号 **待确认** | `/workspace/router/oc/urls.txt`、`pkg/etc/init.d/mihomo` 注释 |
| 管理地址 | 早期 mihomo 面板在 `192.168.8.1:9090`（GL 默认网段）。OpenClash 面板端口取自 uci `openclash.config.cn_port`，默认 9090。目前的 LAN 地址 **待确认** | `router/t/config.yaml`、`add-sub` |
| 角色 | 家用主路由，用 OpenClash 给全屋设备做透明代理。默认出口是「QQG 优先」，即洛杉矶 QQG 自建节点优先，不通再走自动选择 | `router.yaml`、Grok总管 语音记录 |
| 命名提示 | 早期配置文件头误写成「GL-BE3600」。GL-BE3600 是另一款高通方案的机型，实际是 MT3600BE，以此为准 | `router/t/config.yaml` 第 1 行 |

## 功能清单

1. **OpenClash 透明代理（主方案）**
   - 插件是 luci-app-openclash 0.47.156。另外装了 ruby、bash、luci-compat 等依赖包，安装包放在 `oc/deps/`。
   - 主配置 `router.yaml` 参照你的 Loon 配置生成（2026-10-03），用 fake-ip DNS，监听 `0.0.0.0:7874`，假 IP 段 `198.19.0.1/16`。
   - 有 23 个策略组：默认出口、QQG优先、洛杉矶QQG、自动、手动、AI、Telegram、YouTube、Google、Netflix、Spotify、PayPal、Maya、Apple、Microsoft、广告拦截、国内直连、漏网之鱼，以及美、日、港、新、马五个地区组。后来又加了「樱花猫 / 樱花猫自动」。
   - 约 775 条规则和 20 个规则集。规则集来自 geosite/geoip 的 mrs 文件，外加从 Loon 搬过来的广告拦截名单：域名约 5.3 万条、IP 128 条。国内直连另有约 755 条（`loon_custom_rules.txt`）。
   - 节点来自订阅「omni-sub」，OpenClash 每 12 小时更新一次。**不要把 omni-sub.yaml 选成正在用的配置**，配置文件头里专门提醒过。
2. **自定义防火墙规则**（`openclash_custom_firewall_rules.sh`，2026-10-03 加）
   - 在 OpenClash「访问控制」黑名单里的设备（即绕过代理的设备）如果还连着旧的假 IP，会被直接拒绝，迫使它重新向 dnsmasq 查真实 IP。
   - OpenClash 的 IPv6 代理是关着的，所以局域网的 IPv6 DNS 也被转到 OpenClash 的 DNS，避免拿到被污染的结果。绕过代理的设备除外。
   - 每条规则都带 `OpenClash` 注释，OpenClash 停止时会自动清掉。
3. **订阅自动合并 openclash-auto-sub**
   - cron 每 2 分钟跑一次。OpenClash「配置订阅」里的每个订阅都会自动变成节点来源（proxy-provider），并生成「<名称>」手选组和「<名称>自动」测速组。
   - 新组会自动加进 默认出口、手动、AI、Telegram、YouTube、Google、Netflix、Spotify、Twitter 这些组的选项，同时加进「英国」组（只保留英国节点）。
   - 自动过滤剩余流量、套餐到期这类信息行；倍率节点不参与自动测速。
   - 订阅删掉后对应的组也会删掉，omni-sub 除外，它是固定的。节点有变化时通过 Clash API 刷新，不用重载。
   - 每次改动前先用 `mihomo -t` 校验、再备份，然后热重载。日志用 `logread -e openclash-auto-sub` 看。
   - 对应表里已有：omni-sub=omni（固定）、樱花猫=sakura、蓝天云=lantian。
4. **手动加订阅工具 add-sub**：`add-sub <订阅名> <key>`，作用和上面的自动合并一样，只是手动跑一次。会备份成 `router.yaml.bak-pre-<key>`，校验通过才生效，并给节点域名加 DNS 策略。
5. **智能选节点 smartsel**（2026-10-06）
   - 只管「🚀 总出口」和「Telegram」两条线路上的自动测速组，只在组内节点之间切换。
   - 每 10 分钟测一次延迟，每小时测一次实际带宽（下载 1MB）。
   - 当前节点延迟超过 800ms 或超时、带宽低于 300KB/s、或者不到最快候选的一半时，就切到最快的节点，并发 Telegram 通知。
   - 测速走专用入口 `127.0.0.1:7899`（隐藏组「测速专用」），不影响正在用的连接。
   - 所有候选都慢时，会顺便测直连国内的速度，判断是宽带的问题还是节点的问题。这类提醒 6 小时最多发一次。
   - Telegram 机器人的配置从 `/etc/linkmon.conf` 读取（TG_TOKEN、TG_CHAT），不写在这里。
6. **Neko Master 流量监控 agent**
   - agent 版本 v1.4.5（linux-arm64），把 OpenClash/mihomo 的流量上报到 Neko Master 面板（neko.omnitools.cc，部署在洛杉矶 VPS，走 Cloudflare Tunnel）。
   - 在面板里的后端名是「GL-MT3600BE OpenClash」。
   - 服务限制了内存（GOMEMLIMIT=24MiB），挂了会自动重启。
7. **早期方案：直接跑 mihomo（已被 OpenClash 取代，待确认是否已卸载）**
   - `/usr/bin/mihomo`，配置在 `/etc/mihomo`，服务是 `/etc/init.d/mihomo`。用 TPROXY 端口 7894、DNS 端口 1053、路由表 233 做透明代理。
   - 当时 GL 4.x 固件不支持 Nikki 插件，所以直接跑的二进制。
   - 配套工具 `proxy-bypass add|del|list <MAC>`，可以按 MAC 让设备不走代理，改完马上通过 ipset 生效。名单里有一台 H3C-RW3000（另一台路由器）。

## 改动日志

> 新的在上。日期来自文件里的注释或文件修改时间。共享电脑上标着 10-06 14:21 的文件是那时统一拷进来的，实际改动可能更早。

### 2026-10-17 · 关闭自建 VPS 出口切换的 Telegram 通知
- 原因：自建 VPS（含 QQG）暂时不可用，用户要求不要再为这类失败/切换发 TG。
- 改动：注释掉 crontab 里的 `* * * * * /usr/bin/exitmon`（脚本本身未删）。
- 保留：`linkmon`（网口降速）、`bwmon`（总出口/Telegram 带宽变慢）照常。
- 备份：`/root/bak-exitmon/exitmon.20261017-115016`、`/root/bak-exitmon/crontab.20261017-115016`
- 恢复：把 crontab 里那行 `# * * * * * /usr/bin/exitmon` 前面的注释去掉即可。

### 2026-10-08 · 导出当前配置给 F50 用
- 当时路由器上在用的 OpenClash 配置被拷了一份到 `/workspace/f50/src/gl-work-router.yaml`。这时已经有「樱花猫 / 樱花猫自动」组，节点来源是 omni + sakura。
- F50 的配置就是以它为模板生成的，见 [[ZTE F50]]。
- 验证：两份配置的组名和规则应该基本一致。

### 2026-10-06 · 内存实测、拦截猫域名直连（Grok总管 提供）
- 实测总内存约 480MB、空闲约 80MB；OpenClash 平时约 94MB，加星际穿越后峰值约 104MB，结论是暂不加内存。
- 拦截猫官方域名 `lanjiemao.com`、`c.team`、`lanjiejingling.com` 设为直连，放在规则最前面。

### 2026-10-06 · 智能选节点 smartsel
- 设计（Grok总管）：每 10 分钟测延迟、每小时测带宽，只在现有策略组内切节点，切换时发 Telegram 通知。记录停在 10-06 晚：待装到 `/usr/bin/smartsel` 并重启 OpenClash，之后因 Mac 掉线未确认是否装上。**仍待确认**，分组名「🚀 总出口」与配置里的「默认出口」不一致也待核实。
- 新增：共享电脑上的 `/workspace/router/smartsel`（Ruby 脚本），部署用的打包是 `smartsel.b64`。
- 依赖：`/etc/linkmon.conf`（Telegram 通知配置），隐藏组「测速专用」和入口 7899。
- **待确认**：
  - 路由器上的安装路径和 cron 设置。
  - 脚本里用的组名是「🚀 总出口」，但 10-08 导出的路由器配置里叫「默认出口」，脚本会不会因此不生效。
  - 测速入口 7899 是不是真的已经加进路由器配置。
- 验证：`logread -e smartsel`。
- 回滚：删掉对应的 cron 项即可，脚本只调用 API 切节点，不改配置文件。

### 2026-10-06 之前（具体日期待确认）· 订阅自动合并和手动加订阅
- 新增：
  - `/usr/bin/openclash-auto-sub`（推测路径，待确认）和 `/usr/libexec/openclash-auto-sub.rb`，数据放在 `/etc/openclash/custom/auto-sub/`（map、sig、present）。
  - `add-sub`。
  - `unomni.rb`：用来清掉多出来的 omni-sub 组。
- 打包：`autosub.tgz`（第一版），`autosub2.tgz`（第二版，只有 .rb 和 unomni.rb）。
- 验证：`logread -e openclash-auto-sub`；在面板里看新订阅是不是出现了对应的两个组。
- 回滚：去掉 cron 项，用 `router.yaml.bak-pre-<key>` 恢复配置。

### 2026-10-06 之前 · Neko Master agent
- 新增：`/usr/bin/neko-agent`、`/etc/init.d/neko-agent`、`/etc/neko-agent/gl.env`（里面有凭据，不写在这里）。
- 验证：`/etc/init.d/neko-agent status`，再到 Neko 面板看后端是否在线。
- 回滚：`/etc/init.d/neko-agent stop && /etc/init.d/neko-agent disable`。

### 2026-10-05 · 加 256MB zram（Grok总管 提供）
- 加了 256MB zram 内存压缩，开机自动启用，重启后验证过。加内存条（2GB 约 ¥110）是可选方案，用户未决定。

### 2026-10-04 · OpenClash 被杀、路由器自重启（Grok总管 提供）
- 内存不足 OpenClash 被系统杀掉，看门狗约 9:53、20:13 两次自动拉起。约 6:00 路由器自己重启一次，原因不明。

### 2026-10-03 · 换成 OpenClash，生成主配置
- Grok总管 补充：地区绕过、域名嗅探、DNS 代理、流媒体解锁四个快捷开关建议保持关闭，因为局域网 DNS 已由防火墙转给 OpenClash，H3C 排除规则也依赖这个转发。改完后后台一直报「No related RPC reply」，代理本身可用。
- 装了 luci-app-openclash 0.47.156 和 ruby 等依赖包（安装包在 `oc/deps/`、`oc/stage/deps/`）。
- 生成 `/etc/openclash/config/router.yaml`（参照 Loon 配置），运行时用的是 `/etc/openclash/router.yaml`。
- 规则集放在 `/etc/openclash/rule_provider/`，包括 geosite/geoip 的 mrs 文件和 loon_reject_domain/ip。
- 自定义防火墙规则：`/etc/openclash/custom/openclash_custom_firewall_rules.sh`（标准位置，具体路径待确认）。
- 验证：OpenClash 页面显示运行中；手机连上后访问外网正常，国内网站走直连。
- 回滚：在 OpenClash 里停用。防火墙规则带 OpenClash 注释，会自动清掉。

### 2026-10-03 之前 · 直接跑 mihomo 做透明代理（第一版 / v3）
- `t/` 是第一版的配置和防火墙规则（和 `pkg/` 一样）；`v3/` 加了 MAC 绕过（ipset `mihomo_bypass`）、`proxy-bypass` 工具，以及让绕过设备的旧假 IP 连接直接失败的规则。
- 当时 mihomo 版本 **待确认**。共享电脑上的 `router/mihomo` 是 arm64 版，`router/mihomo-amd64` 是 v1.19.32。

## 相关文件与位置

**共享电脑（box）**
- `/workspace/router/oc/`：OpenClash 安装包、依赖包、`router.yaml`、`installed.txt`（路由器上已装软件包的列表，561 个）、`urls.txt`（软件包下载地址）、`loon_custom_rules.txt`、`rp/`（规则集）、`stage/`（部署前的暂存）
- `/workspace/router/autosub/`、`autosub*.tgz`、`add-sub`、`smartsel`、`smartsel.b64`
- `/workspace/router/t/`、`v3/`、`v3.tgz`、`pkg/`：早期直接跑 mihomo 的方案
- `/workspace/router/rules/`、`Country.mmdb`、`zashboard.zip`（面板界面）、`mihomo-router.tar.gz`
- `/workspace/neko-agent/`：agent 程序、启动脚本、`gl.env`（有凭据）、`neko-master-credentials.txt`（有凭据）
- `/workspace/f50/src/gl-work-router.yaml`：10-08 导出的路由器配置
- **密钥位置（只写位置）**：`/workspace/router/secret.txt`（面板密钥）；路由器上 uci `openclash.config.dashboard_password`；`/etc/linkmon.conf`（Telegram 机器人）；`/etc/neko-agent/gl.env`

**路由器上**
- `/etc/openclash/config/router.yaml`（主配置）、`/etc/openclash/router.yaml`（运行时配置）、`/etc/openclash/config/omni-sub.yaml`、`/etc/openclash/proxy_provider/*.yaml`
- `/etc/openclash/custom/auto-sub/`、`/usr/libexec/openclash-auto-sub.rb`
- `/etc/mihomo/`、`/usr/bin/proxy-bypass`、`/etc/init.d/mihomo`（早期方案）
- `/usr/bin/neko-agent`、`/etc/init.d/neko-agent`

## 待办 / 已知问题

- [ ] 确认固件版本号和当前 LAN 地址。
- [ ] 确认早期直接跑的 mihomo 是否已经停用或卸载，避免和 OpenClash 抢端口、抢防火墙规则。
- [ ] 确认 smartsel 是否在跑：组名「🚀 总出口」和「默认出口」对不上，测速入口 7899 是否存在。
- [ ] 内存升级：你在语音里提过闲鱼有改 1G/2G/4G 内存的服务，想改 2G 以便再装广告过滤插件。当时的建议是「家用加广告过滤 2G 基本够用」，还没有执行。
- [ ] 想了解的扩展：用 VHome 加 eSIM 读卡器给路由器上网（拓拔鼠 2026 年下半年的帖子），以及其他常用的 GL 插件。只做过调研，没有改动。
- [ ] Neko 凭据和面板密钥目前以明文放在共享电脑上（见上面的位置），可以考虑换掉。

#路由器 #OpenClash #mihomo #GL-iNet
