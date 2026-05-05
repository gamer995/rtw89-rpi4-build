#!/bin/sh

# Monitor OpenClash AP stability for the RTL8922AU USB adapter.
# Defaults are tuned for this iStoreOS box: radio2 -> phy1-ap0.

set -u

IFACE="${1:-phy1-ap0}"
INTERVAL="${2:-10}"
DURATION="${3:-0}"
OUTFILE="${4:-/tmp/rtw89-stability-${IFACE}-$(date +%Y%m%d-%H%M%S).log}"

LOG_PATTERN='rtw89|flush queues|usb write32|AP-DISABLED|AP-STA-DISCONNECTED|AP-STA-CONNECTED|Phy not found|retry_setup_failed|EAPOL-4WAY-HS-COMPLETED|timed out to flush queues'
START_TS="$(date '+%Y-%m-%d %H:%M:%S')"
START_EPOCH="$(date +%s)"
END_EPOCH=0
LAST_MATCH_COUNT=0
ITER=0

if [ "$DURATION" -gt 0 ] 2>/dev/null; then
  END_EPOCH=$((START_EPOCH + DURATION))
fi

mkdir -p "$(dirname "$OUTFILE")"

echo "# rtw89 stability monitor" > "$OUTFILE"
echo "start_time=$START_TS" >> "$OUTFILE"
echo "iface=$IFACE interval=$INTERVAL duration=$DURATION" >> "$OUTFILE"
echo "hostname=$(uname -n)" >> "$OUTFILE"
echo "kernel=$(uname -r)" >> "$OUTFILE"
echo >> "$OUTFILE"

log_count() {
  logread 2>/dev/null | grep -Ei "$LOG_PATTERN" | wc -l | awk '{print $1}'
}

LAST_MATCH_COUNT="$(log_count)"

read_temp() {
  if [ -r /sys/class/thermal/thermal_zone0/temp ]; then
    awk '{printf "%.1fC", $1 / 1000}' /sys/class/thermal/thermal_zone0/temp
    return
  fi
  if command -v vcgencmd >/dev/null 2>&1; then
    vcgencmd measure_temp 2>/dev/null | sed "s/temp=//; s/'C/C/"
    return
  fi
  echo "n/a"
}

read_usb_speed() {
  lsusb -t 2>/dev/null | awk '/rtw89_8922au_git/ {print $0}' | sed 's/^ *//' | head -n 1
}

read_param() {
  local path="$1"
  if [ -r "$path" ]; then
    cat "$path"
  else
    echo "n/a"
  fi
}

station_block() {
  if iw dev "$IFACE" station dump >/dev/null 2>&1; then
    iw dev "$IFACE" station dump | awk '
      /^Station / { if (seen) print ""; seen=1; printf("STA %s\n", $2); next }
      /inactive time:/ { sub(/^[ \t]+/, ""); print }
      /signal avg:/ { sub(/^[ \t]+/, ""); print }
      /^\tsignal:/ { sub(/^[ \t]+/, ""); print }
      /tx bitrate:/ { sub(/^[ \t]+/, ""); print }
      /rx bitrate:/ { sub(/^[ \t]+/, ""); print }
      /tx retries:/ { sub(/^[ \t]+/, ""); print }
      /tx failed:/ { sub(/^[ \t]+/, ""); print }
      /connected time:/ { sub(/^[ \t]+/, ""); print }
    '
  else
    echo "STA none_or_iface_down"
  fi
}

wireless_line() {
  local up retry channel htmode
  up="$(ubus call network.wireless status 2>/dev/null | jsonfilter -e '@.radio2.up' 2>/dev/null)"
  retry="$(ubus call network.wireless status 2>/dev/null | jsonfilter -e '@.radio2.retry_setup_failed' 2>/dev/null)"
  channel="$(ubus call network.wireless status 2>/dev/null | jsonfilter -e '@.radio2.config.channel' 2>/dev/null)"
  htmode="$(ubus call network.wireless status 2>/dev/null | jsonfilter -e '@.radio2.config.htmode' 2>/dev/null)"
  echo "up=${up:-n/a} retry_setup_failed=${retry:-n/a} channel=${channel:-n/a} htmode=${htmode:-n/a}"
}

while :; do
  NOW_EPOCH="$(date +%s)"
  NOW_HUMAN="$(date '+%Y-%m-%d %H:%M:%S')"
  ITER=$((ITER + 1))

  {
    echo "===== sample $ITER $NOW_HUMAN ====="
    echo "uptime: $(uptime 2>/dev/null | sed 's/^ *//')"
    echo "temp: $(read_temp)"
    echo "usb: $(read_usb_speed)"
    echo "params: disable_ps_mode=$(read_param /sys/module/rtw89_core_git/parameters/disable_ps_mode) switch_usb_mode=$(read_param /sys/module/rtw89_usb_git/parameters/switch_usb_mode)"
    echo "wireless: $(wireless_line)"
    iw dev "$IFACE" info 2>/dev/null | sed 's/^/iface: /' || echo "iface: down_or_missing"
    echo "stations:"
    station_block | sed 's/^/  /'

    CUR_MATCH_COUNT="$(log_count)"
    if [ "$CUR_MATCH_COUNT" -gt "$LAST_MATCH_COUNT" ] 2>/dev/null; then
      DELTA=$((CUR_MATCH_COUNT - LAST_MATCH_COUNT))
      echo "events($DELTA new):"
      logread 2>/dev/null | grep -Ei "$LOG_PATTERN" | tail -n "$DELTA" | sed 's/^/  /'
    else
      echo "events: none"
    fi
    LAST_MATCH_COUNT="$CUR_MATCH_COUNT"
    echo
  } >> "$OUTFILE"

  if [ "$END_EPOCH" -gt 0 ] && [ "$NOW_EPOCH" -ge "$END_EPOCH" ]; then
    break
  fi

  sleep "$INTERVAL"
done

echo "done_time=$(date '+%Y-%m-%d %H:%M:%S')" >> "$OUTFILE"
echo "$OUTFILE"
