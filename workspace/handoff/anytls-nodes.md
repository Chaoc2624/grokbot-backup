# AnyTLS 节点（2026-10-17）— 含密码，勿外传

服务端：sing-box，自签 SNI=www.bing.com，客户端需 skip-cert-verify=true

| 节点 | 地址 | 端口 | 状态 | 证书 SHA256 |
|---|---|---|---|---|
| RackNerd | 192.255.151.85 | 443 | ✅ 可用 | 38:5A:CE:2C:F1:B1:8E:07:F0:B8:DB:92:CA:D7:D2:66:F6:1B:86:C5:CB:86:A8:D7:86:B3:FA:0A:A7:CF:7F:22 |
| Lightsail SG | 13.215.219.205 | 8443 | ✅ 可用 | E3:F9:64:F6:4B:61:47:4B:CC:32:F9:E4:0F:9A:99:9E:D7:7C:1E:93:FC:7D:24:CD:8E:68:97:88:79:89:2A:4E |
| Lightsail MY | 56.69.159.104 | 443 | ✅ TCP 443 已通（07:55 探测）；SSH 密钥暂不可复验 | BF:51:58:17:9E:72:86:3C:A3:DB:92:98:05:7F:D7:4B:69:4F:23:57:4E:BD:C6:94:FF:63:48:EC:D5:87:DD:7E |
| Lightsail HK | 43.198.203.114 | 443 | ✅ TCP 443 已通（07:55 探测）；SSH 密钥暂不可复验 | F1:0B:81:9B:97:4B:3C:E6:A3:D9:06:2B:5A:D6:77:08:22:6A:D5:7A:E1:B1:7C:DD:7E:2D:89:62:75:8E:46:47 |
| QQG | 107.149.159.229 | 8443 | ⚠️ 已装；整机出站被封 | - |
| Lightsail 东京 | 54.64.40.96 | 443 | ✅ 可用（CF 已删） | 97:C3:7D:7E:A1:9D:69:55:17:02:B2:C2:C5:1E:7D:05:B8:D8:9B:D2:14:BC:01:D7:0A:AB:E1:45:A8:8B:57:0B |

## mihomo
```yaml
proxies:
  - {name: "🇺🇸 RackNerd-AnyTLS", type: anytls, server: 192.255.151.85, port: 443, password: "<REDACTED>", sni: www.bing.com, skip-cert-verify: true, client-fingerprint: chrome, udp: true}
  - {name: "🇸🇬 Lightsail-SG-AnyTLS", type: anytls, server: 13.215.219.205, port: 8443, password: "<REDACTED>", sni: www.bing.com, skip-cert-verify: true, client-fingerprint: chrome, udp: true}
  - {name: "🇲🇾 Lightsail-MY-AnyTLS", type: anytls, server: 56.69.159.104, port: 443, password: "<REDACTED>", sni: www.bing.com, skip-cert-verify: true, client-fingerprint: chrome, udp: true}
  - {name: "🇭🇰 Lightsail-HK-AnyTLS", type: anytls, server: 43.198.203.114, port: 443, password: "<REDACTED>", sni: www.bing.com, skip-cert-verify: true, client-fingerprint: chrome, udp: true}
  - {name: "🇯🇵 Lightsail-TYO-AnyTLS", type: anytls, server: 54.64.40.96, port: 443, password: "<REDACTED>", sni: www.bing.com, skip-cert-verify: true, client-fingerprint: chrome, udp: true}
```

## Loon
已写入 Mac ~/Downloads/2026_10_17-anytls.lcf（基于 icloudfix）

## 订阅
sub.omnitools.cc：AnyTLS×4 已加，Reality 已删，CF 保留（RackNerd /opt/sub-static + SG /etc/lightsail-sub）

## IPv6
已关：RackNerd、SG、QQG、MY、HK。未关：东京。

## QQG
网关可达，外网不可达，防火墙未拦。服务商侧出站封锁/流量耗尽，服务器无法修复。

## 2026-10-17 10:40 CF 线路删除
RN/SG/MY/HK 的 CF WS 入站与 tunnel 代理 ingress 已删（备份 /root/backup-cf-removal-20261017/）；订阅只剩 4×AnyTLS + 东京/QQG CF。

Loon: 🇯🇵 Lightsail-TYO-AnyTLS = anytls,54.64.40.96,443,"hFsNJfCj1tccGWzDhBMu53ARZPqXq1W",sni=www.bing.com,skip-cert-verify=true,udp=true
东京：备份 /root/backup-anytls-20261017/，IPv6 已关；订阅已加 TYO AnyTLS，tyo CF 保留待外部验证。

## 10:55 东京外部验证通过（出口 54.64.40.96），tyo CF 已删（备份 /root/backup-cf-removal-20261017/），订阅只剩 5×AnyTLS + QQG CF。Loon: ~/Downloads/2026_10_17-anytls-v2.lcf
