#!/bin/bash
# focus.sh — OPT-IN focus mode: temporarily blocks your distracting sites
# system-wide by adding a clearly-marked section to /etc/hosts.
#
#   sudo scripts/focus.sh 60      # block for 60 minutes, then auto-restore
#   sudo scripts/focus.sh on      # block until you turn it off
#   sudo scripts/focus.sh off     # restore immediately
#   scripts/focus.sh list         # preview the blocklist (no sudo needed)
#
# The blocklist is data-driven: distraction domains from YOUR activity data
# (scripts/focus_blocklist.py), so it blocks what actually distracts you.
#
# Honesty notes:
#   * This is the ONLY part of the toolkit that writes outside the repo
#     folder. It touches exactly one thing — /etc/hosts — between marker
#     comments, and 'off' removes only that section.
#   * It's a speed bump, not a parental control. You can always turn it off.
#   * Browsers cache DNS: already-open tabs may work until reloaded.
#   * A browser with Secure DNS / DoH enabled resolves over HTTPS and can
#     bypass /etc/hosts (Safari honors it; Chrome only with secure DNS off).
set -euo pipefail
cd "$(dirname "$0")/.."

# FOCUS_HOSTS_FILE exists so the test suite can exercise this script against
# a scratch file; humans should never set it.
HOSTS="${FOCUS_HOSTS_FILE:-/etc/hosts}"
BEGIN="# >>> mac-activity-tracker focus mode >>>"
END="# <<< mac-activity-tracker focus mode <<<"
MODE="${1:-}"

usage() { sed -n '2,9p' "$0"; exit 1; }

blocklist() { python3 scripts/focus_blocklist.py 2>/dev/null || true; }

require_root() {
  if [ "$HOSTS" = "/etc/hosts" ] && [ "$(id -u)" -ne 0 ]; then
    echo "Editing $HOSTS needs sudo:  sudo scripts/focus.sh ${MODE:-60}" >&2
    exit 1
  fi
}

# Each session tags its BEGIN marker with its PID. 'off' and a fresh 'on'
# remove ANY focus section (prefix match); a timed session's exit trap removes
# only its OWN section — so a stale timer can't strip a newer session's block.
SESSION="$$"

_strip() {  # _strip <begin-matcher>: rewrite $HOSTS without the matched section
  local b="$1" tmp
  tmp="$(mktemp)"
  awk -v b="$b" -v e="$END" 'index($0,b)==1{skip=1} !skip{print} index($0,e)==1{skip=0}' \
    "$HOSTS" > "$tmp"
  cat "$tmp" > "$HOSTS"   # cat, not mv: keeps /etc/hosts ownership + perms
  rm -f "$tmp"
}

remove_block() {  # remove any focus-mode section, whichever session made it
  grep -qF "$BEGIN" "$HOSTS" && _strip "$BEGIN" || true
}

remove_own_block() {  # timed-session cleanup: only THIS session's section
  grep -qF "$BEGIN session:$SESSION" "$HOSTS" && _strip "$BEGIN session:$SESSION" || true
}

add_block() {
  remove_block  # idempotent: never stack two sections
  {
    echo "$BEGIN session:$SESSION"
    echo "# added $(date '+%Y-%m-%d %H:%M') — remove with: sudo scripts/focus.sh off"
    blocklist | while read -r d; do
      [ -n "$d" ] || continue
      echo "127.0.0.1 $d www.$d"
      echo "::1 $d www.$d"
    done
    echo "$END"
  } >> "$HOSTS"
}

flush_dns() {
  dscacheutil -flushcache 2>/dev/null || true
  killall -HUP mDNSResponder 2>/dev/null || true
}

case "$MODE" in
  list)
    blocklist
    ;;
  off)
    require_root
    remove_block
    flush_dns
    echo "Focus mode OFF — /etc/hosts restored."
    ;;
  on)
    require_root
    add_block
    flush_dns
    echo "Focus mode ON until you run: sudo scripts/focus.sh off"
    ;;
  ''|*[!0-9]*)
    usage
    ;;
  *)
    require_root
    add_block
    flush_dns
    trap 'remove_own_block; flush_dns; echo; echo "Focus mode ended — sites unblocked."' EXIT INT TERM
    echo "Focus mode ON for $MODE minutes (Ctrl-C ends it early and still unblocks)."
    echo "Blocked: $(blocklist | tr '\n' ' ')"
    sleep $(( MODE * 60 ))
    ;;
esac
