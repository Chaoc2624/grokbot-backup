#!/system/bin/sh
# F50 X/Twitter watchdog (run every minute by kano_cron). No notifications.
# Disable: touch /data/halo_guard/x_watchdog.disabled
D=/data/halo_guard; LOG=$D/x_watchdog.log; ST=$D/x_watchdog.fail
[ -f $D/x_watchdog.disabled ] && exit 0
API=http://127.0.0.1:7788; AUTH="Authorization: Bearer 123456"; PX=http://127.0.0.1:7890
PREF="🇯🇵 Lightsail-TYO-AnyTLS|🇸🇬 Lightsail-SG-AnyTLS|🇭🇰 Lightsail-HK-AnyTLS|🇺🇸 RackNerd-AnyTLS|日本-星际隧道 02（稳定版）|新加坡-星际隧道 02（稳定版）"
log(){ echo "$(date '+%m-%d %H:%M:%S') $*" >> $LOG; s=$(wc -c < $LOG); [ "$s" -gt 200000 ] && mv -f $LOG $LOG.1; }
pidof Clash.Core >/dev/null 2>&1 || pgrep -f mihomo >/dev/null 2>&1 || pgrep -f Clash.Core >/dev/null 2>&1 || exit 0
code(){ curl -s -o /dev/null -m 10 -x $PX -w '%{http_code}' "$1"; }
X=$(code https://x.com/robots.txt); G=$(code https://www.gstatic.com/generate_204)
case "$X" in 2*|3*) echo 0 > $ST; exit 0;; esac
case "$G" in 2*) ;; *) log "x=$X g=$G: upstream/总出口 also down, not switching"; echo 0 > $ST; exit 0;; esac
n=$(( $(cat $ST 2>/dev/null || echo 0) + 1 )); echo $n > $ST
log "x=$X g=$G fail#$n"
[ $n -lt 2 ] && exit 0
cur=$(curl -s -m5 -H "$AUTH" $API/proxies/TwitterX | sed -n 's/.*"now":"\([^"]*\)".*/\1/p')
next=""; found=0; first=""
IFS='|'; for p in $PREF; do [ -z "$first" ] && first=$p; if [ $found = 1 ]; then next=$p; break; fi; [ "$p" = "$cur" ] && found=1; done; unset IFS
[ -z "$next" ] && next=$first
curl -s -m5 -X PUT -H "$AUTH" $API/proxies/TwitterX -d "{\"name\":\"$next\"}" >/dev/null
curl -s -m5 -X DELETE -H "$AUTH" $API/connections >/dev/null
log "TwitterX: '$cur' -> '$next', connections cleared"
echo 0 > $ST
