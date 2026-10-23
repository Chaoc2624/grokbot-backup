# Loon → OpenClash 广告规则抽取（2026-10-23）

来源：`/workspace/anytls/2026_10_17-anytls-v2.lcf`（与 Mac Downloads 同名配置）

## 可上路由器（域名/IP REJECT）

- 条数：53068（已去重）
- 文件：`adblock-reject.rules`（每行 `TYPE,value,REJECT`，可直接贴进 OpenClash 自定义规则，放在最终 MATCH 前）
- 也可：`rule-provider-adblock.yaml` 作 rule-provider，再写 `RULE-SET,adblock-loon,REJECT`

## 不能上路由器（需手机 Loon / MITM / Script）

### Plugin（97）
- `wloc.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Auto_Join_TF.lpx, enabled=false`
- `https://kelee.one/Tool/Loon/Lpx/ZhuanZhuan_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/ZhiLianZhaoPin_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Zhihu_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/LOL_Bible_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/YouKu_Video_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/CosmosPodcast_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/iMaiCai_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/XiaojukejiCharge_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/RedPaper_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/OraySunlogin_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/FleaMarket_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Walmart_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/WexinMiniPrograms_Remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Weixin_external_links_unlock.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Weixin_Official_Accounts_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Weibo_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/NeteaseCloudMusic_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/MailMaster_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/TXDocs_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Tencent_Video_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Taopiaopiao_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Taobao_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/ShuQiCenterReader_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/SF-Express_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/smzdm_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/QQKSong_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/LuckinCoffee_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/SodaMusic_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/SevenCat_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/AutoHome_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/51Job_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/PuPuMall_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Block_HTTPDNS.lpx, pin=true, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/BlockAdvertisers.lpx, pin=true, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/QuickSearch.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Prevent_DNS_Leaks.lpx, policy=默认出口, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Node_detection_tool.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/TestFlightRegionUnlock.lpx, policy=DIRECT, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/BoxJs.lpx, policy=默认出口, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Sub-Store.lpx, policy=默认出口, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Script-Hub.lpx, policy=默认出口, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/PinDuoDuo_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/FerrisWheel_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/MaiMai_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/MeiTu_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/MangoTV_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/MaFengWo_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/RoboTaxi_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/2bulu_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/QuarkScanking_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/QuarkBrowser_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/KwaiVideoeditor_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/KuaiShou_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/KuaiDi100_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Remove_ads_by_keli.lpx, enabled=false`
- `https://kelee.one/Tool/Loon/Lpx/WPS_Documents_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/JDWaimai_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/JD_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/JD_Price.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Huxiu_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/HUPU_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/HantingHotels_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/MrHema_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Umetrip_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Amap_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/LiveLab_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/FC_Box_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/TaobaoTravel_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/DragonRead_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Douyu_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/DiDi_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Dewu_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Damai_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/NodeLinkCheck.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/ColorfulClouds_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Cainiao_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Bilibili_remove_ads.lpx, enabled=true`
- `https://kelee.one/Tool/Loon/Lpx/Beike_remove_ads.lpx, enabled=true`
- …

### Script（0）


### Rewrite（0）


### Mitm（6 行）
路由器侧无法做 MITM 证书劫持；YouTube 等去广告依赖这些，请留在 Loon。

### 未能转换的 REJECT 行（0）


## 未验证

尚未写入 GL-MT3600BE OpenClash（办公室网段摸不到 192.168.8.1）。回家连上 GLi3600-7 后再导入并实测。

## 回家导入步骤（GL OpenClash / mihomo）

优先用 rule-provider（文件大时更稳）：

1. 把 `rule-provider-adblock.yaml` 拷到路由器，例如 `/etc/openclash/rule_provider/adblock-loon.yaml`
2. 在配置里加 rule-provider（type: file，behavior: domain，path 指向上面文件）
3. 在规则列表、最终 `MATCH` 之前加一行：`RULE-SET,adblock-loon,REJECT`
4. 保存后重载 OpenClash，用手机关 Loon、连 GLi3600-7，打开常见带广告 App 抽测

备选：把 `adblock-reject.rules` 整段贴进「自定义规则」，同样放在 `MATCH` 前。约 5.3 万行，面板可能卡，优先 rule-provider。

注意：先备份当前 `config.yaml`；若误伤正常站，在 REJECT 规则之上加对应 DOMAIN 直连或 PROXY。
