#!/bin/sh
# Transparent proxy rules for mihomo (iptables/fw3). Usage: firewall.sh start|stop|check
# Also registered as a fw3 include (firewall.mihomo) so rules survive firewall reloads.
MARK=0x40000000
TABLE=233
TPORT=7894
DNSPORT=1053
LAN_IFS="br-lan"
BYPASS="0.0.0.0/8 10.0.0.0/8 100.64.0.0/10 127.0.0.0/8 169.254.0.0/16 172.16.0.0/12 192.168.0.0/16 224.0.0.0/4 240.0.0.0/4"

rules_del() {
  for i in $LAN_IFS; do
    while iptables -t mangle -D PREROUTING -i $i -j MIHOMO 2>/dev/null; do :; done
    while iptables -t nat -D PREROUTING -i $i -j MIHOMO_DNS 2>/dev/null; do :; done
    while ip6tables -t nat -D PREROUTING -i $i -j MIHOMO_DNS 2>/dev/null; do :; done
  done
  iptables -t mangle -F MIHOMO 2>/dev/null; iptables -t mangle -X MIHOMO 2>/dev/null
  iptables -t nat -F MIHOMO_DNS 2>/dev/null; iptables -t nat -X MIHOMO_DNS 2>/dev/null
  ip6tables -t nat -F MIHOMO_DNS 2>/dev/null; ip6tables -t nat -X MIHOMO_DNS 2>/dev/null
  while ip rule del fwmark $MARK/$MARK table $TABLE 2>/dev/null; do :; done
  ip route flush table $TABLE 2>/dev/null
}

rules_add() {
  rules_del
  ip rule add fwmark $MARK/$MARK table $TABLE pref 100
  ip route add local 0.0.0.0/0 dev lo table $TABLE
  iptables -t mangle -N MIHOMO
  iptables -t mangle -A MIHOMO -m addrtype --dst-type LOCAL -j RETURN
  for n in $BYPASS; do iptables -t mangle -A MIHOMO -d $n -j RETURN; done
  iptables -t mangle -A MIHOMO -p udp --dport 53 -j RETURN
  iptables -t mangle -A MIHOMO -p tcp --dport 53 -j RETURN
  iptables -t mangle -A MIHOMO -p tcp -j TPROXY --on-ip 127.0.0.1 --on-port $TPORT --tproxy-mark $MARK/$MARK
  iptables -t mangle -A MIHOMO -p udp -j TPROXY --on-ip 127.0.0.1 --on-port $TPORT --tproxy-mark $MARK/$MARK
  iptables -t nat -N MIHOMO_DNS
  iptables -t nat -A MIHOMO_DNS -p udp --dport 53 -j REDIRECT --to-ports $DNSPORT
  iptables -t nat -A MIHOMO_DNS -p tcp --dport 53 -j REDIRECT --to-ports $DNSPORT
  ip6tables -t nat -N MIHOMO_DNS
  ip6tables -t nat -A MIHOMO_DNS -p udp --dport 53 -j REDIRECT --to-ports $DNSPORT
  ip6tables -t nat -A MIHOMO_DNS -p tcp --dport 53 -j REDIRECT --to-ports $DNSPORT
  for i in $LAN_IFS; do
    iptables -t mangle -I PREROUTING 1 -i $i -j MIHOMO
    iptables -t nat -I PREROUTING 1 -i $i -j MIHOMO_DNS
    ip6tables -t nat -I PREROUTING 1 -i $i -j MIHOMO_DNS
  done
  logger -t mihomo-fw "transparent proxy rules applied"
}

running() { pidof mihomo >/dev/null 2>&1 && netstat -lnu 2>/dev/null | grep -q ":$DNSPORT "; }

case "$1" in
  start) running && rules_add ;;
  stop) rules_del; logger -t mihomo-fw "transparent proxy rules removed" ;;
  check)  # cron watchdog: never leave LAN black-holed if mihomo is dead
    if iptables -t mangle -S MIHOMO >/dev/null 2>&1; then
      running || { rules_del; logger -t mihomo-fw "mihomo not running - rules removed by watchdog"; }
    else
      [ -f /etc/mihomo/.enabled_rules ] && running && rules_add
    fi ;;
  *)  # fw3 include (firewall reload): re-apply only if mihomo is running
    running && [ -f /etc/mihomo/.enabled_rules ] && rules_add ;;
esac
exit 0
