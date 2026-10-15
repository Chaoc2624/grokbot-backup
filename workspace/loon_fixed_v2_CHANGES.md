# loon_fixed_v2.lcf — change summary (vs original attachment)
FIX-1 [General] L30-32: dns-server 1.1.1.1,1.0.0.1 -> 223.5.5.5,119.29.29.29 ; doh-server https://1.1.1.1|1.0.0.1 -> https://223.5.5.5/dns-query,https://1.12.12.12/dns-query ; comment now says keep 查询回落 ON.
FIX-2 [Host] (after L134): node/sub domains -> server:system  (*.tube-cat.com, *.catcat321.com, *.gcp300.com, *.omnitools.cc, 0b96e976-...com)
FIX-3 [Rule] 140 IP-CIDR lines (first at orig L627, Telegram etc.) +",no-resolve"
FIX-4 [Mitm] orig L54239-54240 duplicate empty ca-p12= / ca-passphrase= commented out
FIX-5 [Plugin] duplicate TestFlightRegionUnlock (orig L54221) and BlockAdvertisers (orig L54230) commented out
Unchanged: everything else (groups, filters, 53k rules, plugins, MITM hostnames).
Full diff: loon_fixed_v2.diff ; scanner: scan.py
