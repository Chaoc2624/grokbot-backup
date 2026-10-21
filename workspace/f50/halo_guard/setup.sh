#!/system/bin/sh
set -u; D=/data/halo_guard; S=/data/local/tmp/hg_stage; TS=$(date +%Y%m%d%H%M%S); BK=/data/local/tmp/halo_bak/$TS; mkdir -p $BK
echo "== id"; id
cp -p /data/clash/Proxy/config.yaml $BK/; cp -p /sdcard/ufi_tools_boot.sh $BK/; cp -p $D/UNDO.txt $BK/; echo "backup $BK"
cp $S/wan_fallback.sh $D/; cp $S/tg.conf $D/tg.conf; chmod 700 $D/wan_fallback.sh; chmod 600 $D/tg.conf
grep -q wan_fallback /sdcard/ufi_tools_boot.sh || echo '(while true; do sh /data/halo_guard/wan_fallback.sh; sleep 30; done) </dev/null >/dev/null 2>&1 &' >> /sdcard/ufi_tools_boot.sh
cat >> $D/UNDO.txt <<U

== wan_fallback ($TS) wlan1 -> sipa_eth8 mihomo fallback + TG
Disable: touch /data/halo_guard/wan_fallback.disabled
Undo: remove the wan_fallback line from /sdcard/ufi_tools_boot.sh (backup $BK/ufi_tools_boot.sh), pkill -f wan_fallback, rm /data/halo_guard/wan_fallback.* /data/halo_guard/tg.conf,
      then curl -X PATCH -H 'Authorization: Bearer 123456' http://127.0.0.1:7788/configs -d '{"interface-name":"wlan1"}'
U
. $D/tg.conf
echo "== tg test"; for o in "--interface sipa_eth8" "-x http://127.0.0.1:7890"; do c=$(curl -s -m15 $o "https://api.telegram.org/bot$TG_TOKEN/sendMessage" --data-urlencode "chat_id=$TG_CHAT" --data-urlencode "text=F50 中继断线提醒已启用（测试）" -o /dev/null -w '%{http_code}'); echo "via $o: $c"; [ "$c" = 200 ] && break; done
echo "== simulate"; rm -f $D/wan_fallback.tglast $D/wan_fallback.state
restore(){ iptables -D OUTPUT -o wlan1 -j DROP 2>/dev/null; }; trap restore EXIT
iptables -I OUTPUT -o wlan1 -j DROP
sh $D/wan_fallback.sh; sleep 5; sh $D/wan_fallback.sh; cat $D/wan_fallback.state
curl -s -m5 -H 'Authorization: Bearer 123456' http://127.0.0.1:7788/configs | grep -o '"interface-name":"[^"]*"'
sleep 50; restore; sleep 3; rm -f $D/wan_fallback.tglast
sh $D/wan_fallback.sh; cat $D/wan_fallback.state
curl -s -m5 -H 'Authorization: Bearer 123456' http://127.0.0.1:7788/configs | grep -o '"interface-name":"[^"]*"'
tail -5 $D/wan_fallback.log
setsid nohup sh -c 'while true; do sh /data/halo_guard/wan_fallback.sh; sleep 30; done' </dev/null >/dev/null 2>&1 &
echo "== delay"; curl -s -m10 -H 'Authorization: Bearer 123456' 'http://127.0.0.1:7788/proxies/TwitterX/delay?url=http://www.gstatic.com/generate_204&timeout=5000'; echo
echo "== NAT"; iptables -t nat -S POSTROUTING | head -20; iptables -S FORWARD | head -15; cat /proc/sys/net/ipv4/ip_forward
echo "== plugin"; for d in /data/local/tmp/relay /data/data /data/adb /data/local/tmp/root.new; do grep -rl "收起认证\|热点共享上游" $d 2>/dev/null | head -5; done > $S/plugin_hits; cat $S/plugin_hits
for f in $(cat $S/plugin_hits); do mkdir -p $BK/plugin; cp -p "$f" $BK/plugin/; grep -n -o ".\{120\}热点共享上游.\{200\}" "$f" | head -4; done
