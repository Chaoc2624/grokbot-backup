#!/system/bin/sh
# wlan1 relay -> cellular fallback for mihomo (kano_cron every minute). Cooperates with relay.sh/clash_if.sh:
#  - switches to sipa_eth8 only if mihomo is currently on wlan1 and wlan1 failed twice;
#  - switches back only if it made the switch itself; missing wlan1 = down; one alert per outage.
# Single scheduler: kano_cron every minute; mkdir lock; drop after 3 consecutive fails (~3 min); 10-min cooldown both msgs.
# Disable: touch /data/halo_guard/wan_fallback.disabled
D=/data/halo_guard; LOG=$D/wan_fallback.log; ST=$D/wan_fallback.state
[ -f $D/wan_fallback.disabled ] && exit 0
L=$D/wan_fallback.lock
if ! mkdir $L 2>/dev/null; then
  [ $(( $(date +%s) - $(stat -c %Y $L 2>/dev/null || echo 0) )) -gt 120 ] && rmdir $L 2>/dev/null; exit 0; fi
trap 'rmdir $L 2>/dev/null' EXIT
API=http://127.0.0.1:7788; AUTH="Authorization: Bearer 123456"
[ -f $D/tg.conf ] && . $D/tg.conf
CD=600
log(){ echo "$(date '+%m-%d %H:%M:%S') $*" >> $LOG; [ "$(wc -c < $LOG)" -gt 200000 ] && mv -f $LOG $LOG.1; }
tg(){ [ -n "${TG_TOKEN:-}" ] || return; now=$(date +%s); last=$(cat $D/wan_fallback.tglast 2>/dev/null || echo 0)
  [ $((now-last)) -lt $CD ] && { log "tg suppressed (cooldown)"; return; }
  for o in "-x http://127.0.0.1:7890" "--interface sipa_eth8" ""; do
    c=$(curl -s -m 15 $o "https://api.telegram.org/bot$TG_TOKEN/sendMessage" --data-urlencode "chat_id=$TG_CHAT" --data-urlencode "text=$1" -o /dev/null -w '%{http_code}')
    [ "$c" = 200 ] && { echo $now > $D/wan_fallback.tglast; log "tg sent"; return; }
  done; log "tg send failed"; }
cur(){ curl -s -m4 -H "$AUTH" $API/configs | sed -n 's/.*"interface-name":"\([^"]*\)".*/\1/p'; }
ok(){ ip link show wlan1 >/dev/null 2>&1 || return 1
  c=$(curl -4 -s -o /dev/null -m 8 --interface wlan1 -w '%{http_code}' http://connect.rom.miui.com/generate_204); [ "$c" = 204 ]; }
set_if(){ curl -s -m5 -X PATCH -H "$AUTH" $API/configs -d "{\"interface-name\":\"$1\"}" -o /dev/null; curl -s -m5 -X DELETE -H "$AUTH" $API/connections -o /dev/null; }
switched=0; alerted=0; fails=0; [ -f $ST ] && . $ST
T=$(date '+%Y-%m-%d %H:%M:%S'); C=$(cur)
if ok; then
  fails=0
  if [ "$switched" = 1 ]; then [ "$C" = sipa_eth8 ] && set_if wlan1; switched=0; log "wlan1 recovered -> mihomo back to wlan1 (was '$C')"; fi
  if [ "$alerted" = 1 ]; then alerted=0; tg "✅ F50 中继恢复 $T
原因: alibaba-guest(wlan1) 探测恢复
当前上游: WiFi 中继 wlan1（mihomo: $(cur)）" ; fi
else
  fails=$((fails+1)); ip link show wlan1 >/dev/null 2>&1 && why="wlan1 连续 $fails 次探测失败" || why="wlan1 接口不存在（中继断开）"
  if [ $fails -ge 3 ]; then
    if [ "$switched" = 0 ] && [ "$C" = wlan1 ]; then set_if sipa_eth8; switched=1; log "$why -> mihomo wlan1 -> sipa_eth8"; fi
    if [ "$alerted" = 0 ]; then alerted=1; log "alert: $why (mihomo='$(cur)')"; tg "⚠️ F50 中继断开 $T
原因: $why
当前上游: 5G 蜂窝 sipa_eth8（mihomo: $(cur)）"; fi
  fi
fi
printf 'switched=%s\nalerted=%s\nfails=%s\n' $switched $alerted $fails > $ST.tmp && mv -f $ST.tmp $ST
