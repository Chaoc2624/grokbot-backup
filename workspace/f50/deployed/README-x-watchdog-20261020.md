# F50 X/Twitter self-heal (2026-10-20 Asia/Shanghai)

## Device (live)
- Config: `/data/clash/Proxy/config.yaml`
- Backup: `/data/clash/Proxy/config.yaml.bak-prune-20261020110248`
- Changes: `exclude-filter: "…|随机刷新|0倍率"` on TwitterX, 星际穿越自动, 星际穿越
- Watchdog script: `/data/halo_guard/x_watchdog.sh` (every ~60s via background loop)
- Fail counter: `/data/halo_guard/x_watchdog.fail`
- Log: `/data/halo_guard/x_watchdog.log` (rotates at ~200KB)
- Boot persist: appended to `/sdcard/ufi_tools_boot.sh`
- Disable: `touch /data/halo_guard/x_watchdog.disabled`
- Kill loop: `pkill -f x_watchdog.sh`
- Undo notes: `/data/halo_guard/UNDO.txt`

## Mac backup watchdog
- `~/.clash-watchdog/watchdog.py` (bak: `watchdog.py.bak-20261020`)
- Auto-detects gateway 192.168.0.1 (F50) vs 192.168.8.1 (GL)
- launchd: `com.halo.clash-watchdog` every 60s

## Cron note
- Tried kano_cron; crontab file must be owned by root. adb shell cannot chown.
- On-device loop + boot hook used instead. Cron file currently has both lines but may be ignored by ownership.
