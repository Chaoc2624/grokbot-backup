=== donni_jj
### 零星消息
> Felix John：哈哈哈，晓得原因了我 p 的 mz 的地址，那会已经传上去了
~ 话题活跃成员（近 7 天话题消息）：C酱です 532（银行开户/U卡/SIM）、Valerio（tz） 348（银行开户/U卡/SIM）、huo yan 321（银行开户/U卡/羊毛）
--- 核验

=== inficheesy
### Wise / 币安·欧易 (7 条 / 2 人)
> c e：币安欧易哪个好用一点
> JimmyC：都差不多 · 我个人感觉币安好用
> c e：我想激活wise没有港卡这俩我得注册一个 · 那我注册币安吧
> JimmyC：为什么激活wise要拿交易所激活 · 我之前拿支付宝激活的 用了一年 从paypal 提现资金到wise给我整关户了
~ 话题活跃成员（近 7 天话题消息）：Arion 88（银行开户/SIM/VPS）、猫e/acc 84（VPS/SIM/羊毛）、InfiCheesy SC 81（银行开户/SIM/羊毛）
--- 核验
- Wise 不接受来自币安的付款｜Wise Help Centre（2026-10-26 查阅）：Incompatible accounts 写明可接收受监管加密平台款项但「we're not able to accept any payments from Binance」 https://wise.com/help/articles/2932118/incompatible-accounts-and-payments
- Wise ← PayPal 提现｜Wise Help Centre（2026-10-26 查阅）：可从 PayPal 收款，前提是 PayPal 接受将 Wise 账户详情作为提现银行；业务收款须用 Wise Business https://wise.com/help/articles/5G6pZYCN1QXWYIlskNykYJ/how-do-i-receive-money-from-paypal-with-wise
- PayPal 提现导致 Wise 关户｜未找到公开「PayPal 提现即关户」公告（已查官网）：Wise 称可按 Acceptable Use / 风险关闭账户，但不披露具体原因 https://wise.com/help/articles/2961844/my-account-was-closed-by-wise

=== loon0x00
### Loon DNS / Claude no-resolve (10 条 / 4 人)
> 🔔🐈：为什么非得讨论这个dns泄漏 · 比如谷歌。在国内必须要代理，那肯定是交给节点服务器那边解析 · 不会在本地
> Lewis Jacqueline：能不泄露当然更好了 · 一条请求预期走代理，就没必要本地查一遍ip · loon当前是可以做到的，还是比较方便的 · 你加一条不带no-resolve的规则，会给苛刻的地区审查服务比如claude留下弱点，我国内待一会可不想20x max plan被封🤣
> Qingu LiLi：我感觉压根不存在这个概念。 · 我一直觉得dns远程解析是为了性能的不是为了奇怪的泄露的
> 🔔🐈：好了。没必要讨论这个。可能人家玩灰产类的 · 普通人不用在意这个东西 · 不参与就是了
### Claude Desktop STUN / Clash (11 条 / 3 人)
> Lewis Jacqueline：最新的claude desktop已经会通过stun发给google请求了，给桌面用clash verge/mihomo内核的提个醒，去搜一下stun阻断规则，省得又被精准狙击了，刚看了下loon是默认关闭的好评☺️ · ios的也就stash是clash系了吧 · 是的 · 肯定reject · 有依赖udp服务出问题再direct排查 · 需要代理的服务没几个用得到udp · 这个没太大所谓
> 🔔🐈：至于stun阻断规则这个我就没多了解了
> moyan：你说的是stun丢弃吧 · udp回落那里你是直连还是拒绝 · 其实不太懂这两个的具体区别😅 · 我以前也用reject，后来改direct了 · 那就行
### Loon geoip-url / [Host] 映射 (8 条 / 2 人)
> lafbd 32：请问在config中某条配置,比如geoip-url=https://raw.githubusercontent.com/xxx ,我给改成 https://raw.g.h/xxx ,然后再配置DNS映射raw.g.h = raw.githubusercontent.com,这样会生效吗 · dude我举得例子不太行,我是想问,配置里的一些资源文件能不能简写,然后在[host]里用映射改回去,不是在问geoip的事情 · 我刚才测试过了,获取资源的时候会显示SSL错误 · 这里不能发图 · 可以给你发私信的吗 · 好 · 发你了
> 🔔🐈：没有你这样的例子。geoip对应的是国家英文简写或者地区代码 · 这是你节点问题吧 · 拿上ui图来说好点。我不懂代码 · 宵禁了 · 明天你发给他们更好
~ 话题活跃成员（近 7 天话题消息）：Tartarus 139（VPS/羊毛/美卡）、姥 舅 43（VPS/羊毛/银行开户）、秦城二院彭医生｜夜勤病棟 39（VPS/羊毛）
--- 核验
- Claude Desktop / STUN 分流｜claude403 路由指南（2026-10-26 查阅）：检测页规则含 stun.l.google.com、stun.cloudflare.com，并写 WebRTC 用 STUN；社区 Clash/Mihomo 配置亦常见 DOMAIN-KEYWORD,stun 拦截 https://claude403.com/guide/routing/ https://github.com/jadchene/clash-config
- Loon disable-stun｜Loon 文档（2026-10-26 查阅）：General 提供 disable-stun，禁用后可缓解 WebRTC IP 泄露；另有 PROTOCOL,STUN,REJECT 协议规则 https://nsloon.bid/document/general https://nsloon.bid/document/protocol_rule
