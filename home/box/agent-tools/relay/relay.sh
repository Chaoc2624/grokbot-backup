#!/system/bin/sh
# relay.sh — F50 Pro WiFi 中继后端（仅 STA 上游 + captive 认证；不改 NAT/iptables/路由）
# 用法: relay.sh status|scan|connect <ssid> [pskfile]|savepsk <ssid> <psk>|disconnect|
#        portal_check|portal_send [phone]|portal_readcode [wait]|portal_auth <code> [phone]|
#        auto on|off|watchdog|clear_fail
# 参数可用 b64:<base64> 形式传入（插件用，防注入）。输出均为单行 JSON。
R=/data/local/tmp/relay
BB=/data/local/tmp/busybox
IW=/data/local/tmp/iw
F=/data/data/com.minikano.f50_sms/files
JQ=$F/jq
UFIREQ=$F/ufi_req
WPA=/vendor/bin/hw/wpa_supplicant
IF=wlan1
G204=http://connectivitycheck.gstatic.com/generate_204
FAIL=/sdcard/halo_portal_fail
LOG=$R/relay.log
KNOWN=$R/known.list
mkdir -p $R/psk; chmod 700 $R $R/psk 2>/dev/null
[ -f $KNOWN ] || echo "alibaba-guest" > $KNOWN

log(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" >> $LOG; n=$($BB wc -l < $LOG); [ "$n" -gt 500 ] && $BB tail -n 300 $LOG > $LOG.t && mv $LOG.t $LOG; }
arg(){ case "$1" in b64:*) echo "${1#b64:}" | $BB base64 -d ;; *) printf '%s' "$1" ;; esac; }
jerr(){ $JQ -n -c --arg e "$1" --arg d "${2:-}" '{ok:false,error:$e,detail:$d}'; }
setfail(){ echo "$(date '+%m-%d %H:%M') $1" > $FAIL; log "FAIL $1"; }
lock(){ i=0; while ! mkdir $R/.lock 2>/dev/null; do i=$((i+1)); [ $i -gt 60 ] && { rm -rf $R/.lock; }; sleep 1; done; }
unlock(){ rmdir $R/.lock 2>/dev/null; }

ensure_if(){
  ip link show $IF >/dev/null 2>&1 || { $IW phy phy0 interface add $IF type managed 2>/dev/null || return 1; }
  ip link set $IF up 2>/dev/null; return 0
}
cur_ssid(){ $IW dev $IF link 2>/dev/null | $BB sed -n 's/^[[:space:]]*SSID: //p' | head -1; }
cur_ip(){ ip -4 addr show $IF 2>/dev
