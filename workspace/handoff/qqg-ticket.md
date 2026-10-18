# QQG 工单（中文）
标题：VPS 107.149.159.229 出站流量全部不通，仅网关可达

您好，我的 VPS（IP 107.149.159.229）从 10 月 17 日凌晨起无法访问任何外网地址：
- 能 ping 通网关 107.149.159.1（0% 丢包），但 ping 1.1.1.1 / 8.8.8.8 均 100% 丢包；
- traceroute/mtr 到 1.1.1.1 在第 3 跳 10.255.68.26（你们的内网设备）之后无响应；
- DNS（8.8.8.8:53）、HTTP/HTTPS 全部超时；
- 服务器本机 iptables/nft 无出站拦截规则，网卡无错误，入站 SSH 正常。
请帮忙检查上游路由/出站是否被限制或流量是否已耗尽，并尽快恢复。附件为诊断输出。谢谢！

# QQG Ticket (English)
Subject: VPS 107.149.159.229 – all outbound traffic dropped beyond gateway

Hello, since early Oct 17 (UTC+8) my VPS 107.149.159.229 cannot reach the internet:
- Gateway 107.149.159.1 replies to ping (0% loss), but 1.1.1.1 and 8.8.8.8 show 100% loss;
- traceroute/mtr to 1.1.1.1 stops after hop 3 (10.255.68.26, your internal network);
- DNS (8.8.8.8:53) and HTTP/HTTPS all time out;
- No outbound filtering on the server (iptables/nft clean), no NIC errors, inbound SSH works.
Please check whether outbound is blocked/rate-limited or the traffic quota is exhausted, and restore it. Diagnostic output attached. Thanks.
