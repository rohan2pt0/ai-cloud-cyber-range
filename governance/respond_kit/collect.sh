#!/bin/sh
# SecuRAX first-response collector for Linux, macOS and other Unix-like systems (doc 78).
# Run it FROM the responder USB, as root, on the affected machine:   sudo sh /media/<usb>/SECURAX/collect.sh
#
# What it does, in the order of volatility (RFC 3227: what disappears first is taken first):
#   1. memory, if tools/avml is on the USB (Linux only)
#   2. running state: time, users, processes, network connections, listening ports, routes, ARP, DNS
#   3. persistence: cron, systemd units, shell start-up files, authorized_keys, recently changed files in temp folders
#   4. logs: the system journal and /var/log (last 3 days), shell histories
#   5. a full triage with UAC, if tools/uac is on the USB
# Then every file gets a SHA-256 in MANIFEST.sha256, and collector.json records who, when, where and with what.
# It writes ONLY to the USB, never to the machine's own disk, and it changes nothing on the machine.
#   --quick   running state and persistence only (skips memory, logs and UAC): for when minutes matter, or many machines
set -u
QUICK=0; [ "${1:-}" = "--quick" ] && QUICK=1
HERE="$(cd "$(dirname "$0")" && pwd)"
CASE="$(cat "$HERE/CASE_ID" 2>/dev/null || echo NO-CASE)"
HOST="$(hostname 2>/dev/null || uname -n)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HERE/evidence/${HOST}-${STAMP}"
mkdir -p "$OUT" || { echo "Cannot write to the USB ($OUT). Is it mounted read-write?"; exit 1; }
[ "$(id -u)" = 0 ] || echo "!! Not running as root: some items will be incomplete. Re-run with sudo if you can."
LOG="$OUT/collector.log"
say(){ echo "$*"; echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
run(){ # run NAME COMMAND... : output to NAME.txt, never fatal
  name="$1"; shift
  if command -v "$1" >/dev/null 2>&1; then "$@" > "$OUT/$name.txt" 2>&1 || true; say "  ok  $name"; else say "  --  $name ($1 not on this system)"; fi
}
say "SecuRAX collector · case $CASE · host $HOST · $(uname -s) · started $(date -u +%FT%TZ)"
say "Writing to $OUT"

# 1. memory first (it is lost the moment the machine is switched off)
if [ "$QUICK" = 1 ]; then
  say "  --  memory (quick mode)"
elif [ "$(uname -s)" = Linux ] && [ -x "$HERE/tools/avml" ]; then
  say "Capturing memory with AVML (this can take a while; do not remove the USB)..."
  "$HERE/tools/avml" "$OUT/memory.lime" >> "$LOG" 2>&1 && say "  ok  memory.lime" || say "  !!  memory capture failed (see collector.log)"
else
  say "  --  memory (put the AVML binary at tools/avml on the USB to capture it)"
fi

# 2. running state
run time-utc date -u
run uptime uptime
run uname uname -a
run users-now w
run logins-last last -a -n 200
run processes ps auxww
run process-tree ps -ejH
if command -v ss >/dev/null 2>&1; then run connections ss -tunapo; else run connections netstat -anp; fi
run open-network-files lsof -nP -i
run interfaces ip addr
run routes ip route
run arp ip neigh
[ -r /etc/hosts ] && cp /etc/hosts "$OUT/etc-hosts.txt" 2>/dev/null
[ -r /etc/resolv.conf ] && cp /etc/resolv.conf "$OUT/etc-resolv.txt" 2>/dev/null
if [ -d /proc ]; then   # programs still running after their file was deleted: a classic sign of an implant
  ls -l /proc/[0-9]*/exe 2>/dev/null | grep -i deleted > "$OUT/deleted-but-running.txt" 2>/dev/null; say "  ok  deleted-but-running"
fi

# 3. persistence
run crontab-root crontab -l
( ls -la /etc/cron* /var/spool/cron* 2>/dev/null; cat /etc/crontab 2>/dev/null ) > "$OUT/cron-all.txt" 2>&1; say "  ok  cron-all"
run systemd-units systemctl list-unit-files --state=enabled
run systemd-timers systemctl list-timers --all
for f in /root/.ssh/authorized_keys /home/*/.ssh/authorized_keys /Users/*/.ssh/authorized_keys; do
  [ -f "$f" ] && { echo "== $f"; ls -la "$f"; cat "$f"; }
done > "$OUT/authorized-keys.txt" 2>/dev/null; say "  ok  authorized-keys"
for d in /tmp /var/tmp /dev/shm; do [ -d "$d" ] && find "$d" -xdev -type f -mtime -14 -ls 2>/dev/null; done > "$OUT/temp-recent-files.txt"; say "  ok  temp-recent-files"
for f in /etc/profile /etc/bash.bashrc /root/.bashrc /root/.profile /etc/rc.local; do [ -f "$f" ] && { echo "== $f"; cat "$f"; }; done > "$OUT/startup-files.txt" 2>/dev/null
[ "$(uname -s)" = Darwin ] && ls -la /Library/LaunchAgents /Library/LaunchDaemons /Users/*/Library/LaunchAgents > "$OUT/launchd.txt" 2>&1

# 4. logs and histories (copied, never cleared)
if [ "$QUICK" = 0 ]; then
run journal-3-days journalctl --since "3 days ago" --no-pager
find /var/log -xdev -type f -mtime -3 -size -200M 2>/dev/null | tar -czf "$OUT/var-log-3-days.tgz" -T - 2>/dev/null; say "  ok  var-log-3-days.tgz (paths kept)"
fi
for h in /root/.*history /home/*/.*history /Users/*/.*history; do [ -f "$h" ] && { echo "== $h"; cat "$h"; }; done > "$OUT/shell-histories.txt" 2>/dev/null; say "  ok  shell-histories"

# 5. full triage with UAC, when it is on the USB
UAC="$(ls -d "$HERE"/tools/uac* 2>/dev/null | head -1)"
if [ "$QUICK" = 1 ]; then
  say "  --  UAC (quick mode)"
elif [ -n "$UAC" ] && [ -x "$UAC/uac" ]; then
  say "Running UAC (full profile; can take 10-30 minutes)..."
  ( cd "$UAC" && ./uac -p full "$OUT/uac" >> "$LOG" 2>&1 ) && say "  ok  uac" || say "  !!  UAC reported a problem (see collector.log)"
else
  say "  --  UAC (unpack it into tools/uac-<version>/ on the USB for a full triage)"
fi

# seal: a hash for every file, and who/when/where. Nothing is written to the folder after this except collector.json
say "Sealing: hashing every file"
( cd "$OUT" && find . -type f ! -name MANIFEST.sha256 ! -name collector.json -exec sha256sum {} \; 2>/dev/null > MANIFEST.sha256 \
  || find . -type f ! -name MANIFEST.sha256 ! -name collector.json -exec shasum -a 256 {} \; > MANIFEST.sha256 )
cat > "$OUT/collector.json" <<EOF
{"case": "$CASE", "host": "$HOST", "os": "$(uname -s) $(uname -r)", "collected_by": "${SUDO_USER:-$(id -un)}",
 "started_utc": "$STAMP", "finished_utc": "$(date -u +%Y%m%dT%H%M%SZ)", "collector": "securax collect.sh",
 "manifest_sha256": "$(sha256sum "$OUT/MANIFEST.sha256" 2>/dev/null | cut -d' ' -f1)"}
EOF
sync
echo "Done. Files: $(wc -l < "$OUT/MANIFEST.sha256") · folder: $OUT"   # the log is sealed: nothing more is written to it
echo "Next: write the time and your name on the custody form, safely eject the USB, and do NOT switch this machine off."
