=== waika
### 家宽节点 / 联通光纤 (2 条 / 1 人)
> For Freedom：外面卖的很多所谓家庭宽带节点，是用机房 IP 伪装的。我用的都是用国外朋友家的宽带光纤搭建的节点
> For Freedom：我用的中国联通节点也是中国的朋友在联通宽带光纤上搭建的
~ 话题活跃成员（近 7 天话题消息）：For Freedom 35（SIM/VPS）、一隻北極熊 29（SIM/VPS）、June Park 26（SIM）
### 零星消息
> 一隻北極熊：看本地電訊商給力不給力了 · 香港本地的就不給力
--- 核验
- 所谓家宽节点用机房 IP 伪装｜IPWeb 住宅IP指南（2026-10-23 查阅）：市场多数「静态住宅」实为 ==ISP 代理==——服务器托管在数据中心，IP 段向运营商租赁并在 GeoIP 库标为 Residential https://ipweb.cc/residential-ip-guide/
- 伪住宅 / 机房伪装｜RESIP.NET（2026-10-23 查阅）：对比真实家宽 ASN（Verizon/AT&T 等）与伪住宅骨干 ASN（NTT/GTT/Lumen 等常被包装成「静态住宅」） https://resip.net/
- 联通家宽骨干｜搬瓦工中文网（2026-10-23 查阅）：普通联通家宽多走 ==AS4837==（CHINA169）；==AS9929== 多用于企业/IDC https://www.bandwagonhost.net/10880.html

=== haiwufang
### 零星消息
> Yll Yl：有币安 没睡的来捡钱

=== inficheesy
### 零星消息
> Yll Yl：有币安没睡的 来捡钱了

=== loon0x00
### Loon YouTube 双语字幕 (2 条 / 1 人)
> Black Long：这个可以有翻译吗？ · 我记得以前老版本的 loon 和老版本的youtube 都有双语翻译，为什么现在都失效。加载字幕失效
### SideStore / LocalDevVPN (1 条 / 1 人)
> Ray：dev-loopback.lpx 有可能替代LocalDevVPN 刷新SideStore吗？
~ 话题活跃成员（近 7 天话题消息）：Tartarus 148（VPS）、姥 舅 40（VPS）、R 35（VPS）
### 零星消息
> z zz：懒人配置
--- 核验
- Loon/YouTube 双语字幕 tlang 失效｜DualSubs YouTube Changelog v1.6.0（2026-10-11）：修复 YouTube App ==tlang== 翻译字幕请求可能返回 ==529==、无法显示双语字幕；保留已有 Cookie 的 Web 请求头 https://dualsubs.github.io/changelog/youtube.html
- DualSubs YouTube 模块｜GitHub DualSubs/YouTube Releases（2026-10-11）：v1.6.0 同上修复说明 https://github.com/DualSubs/YouTube/releases
- SideStore 刷新依赖 LocalDevVPN｜SideStore #1200 / Reddit r/sideloaded（2026-03～2026-04 查阅）：刷新需 Wi-Fi + ==LocalDevVPN==（本地 loopback/TUN，常见 ==10.7.0.1==）；部分 iOS 版本需先连 IKEv2 Personal VPN 再连 LocalDevVPN https://github.com/SideStore/SideStore/issues/1200
- Clash loopback 刷新 SideStore｜LiveContainer #1478（2026-07 查阅）：可用 Clash ==loopback-address: 10.7.0.1== 替代 LocalDevVPN；SideStore 设置里 Device IP 需与 loopback 一致 https://github.com/LiveContainer/LiveContainer/issues/1478
