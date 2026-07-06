#!/bin/bash
# focus_session.sh — the "app side" of focus mode (no sudo; quits YOUR apps).
#
#   focus_session.sh start "Xcode,Safari" 60 "ship the release"
#       quit every other visible app (gracefully), record the goal, and start
#       a guard that keeps quitting non-allowed apps for 60 minutes.
#   focus_session.sh stop
#       end the session now (the guard stops; apps are free to open again).
#   focus_session.sh status
#       print the active goal + allowed apps, if any.
#
# Set DRY_RUN=1 to print what WOULD be quit without quitting anything.
#
# Safety: apps are asked to quit with AppleScript `quit` (they may prompt to
# save) — never force-killed. A protect-list (scripts/focus_apps.py) always
# spares Finder, your terminal, this tracker, and system UI. The guard is
# session-scoped: it exits when the session ends. This is the toolkit's only
# background process, and it lives only for the length of a focus session.
set -euo pipefail
cd "$(dirname "$0")/.."

STATE=".focus"
SENTINEL="$STATE/active"
ALLOW="$STATE/allowed.txt"
GOAL="$STATE/goal.txt"
ENDFILE="$STATE/end_epoch"
SUB="${1:-}"

running_visible() {
  osascript -e 'tell application "System Events" to get name of (every application process whose background only is false)' 2>/dev/null \
    | tr ',' '\n' | sed 's/^ *//;s/ *$//'
}

quit_disallowed() {
  local app
  running_visible | python3 scripts/focus_apps.py "$ALLOW" | while IFS= read -r app; do
    [ -n "$app" ] || continue
    if [ -n "${DRY_RUN:-}" ]; then
      echo "would quit: $app"
    else
      osascript -e "tell application \"$app\" to quit" >/dev/null 2>&1 || true
    fi
  done
}

case "$SUB" in
  start)
    # args: 2=comma-separated allowed apps  3=minutes  4=goal text
    mins="${3:-60}"
    # In DRY_RUN, persist nothing: use a throwaway allowlist so the quit
    # decision can run, but create no sentinel/guard/log.
    if [ -n "${DRY_RUN:-}" ]; then
      ALLOW="$(mktemp)"
    else
      mkdir -p "$STATE"
    fi
    : > "$ALLOW"
    IFS=',' read -ra _apps <<< "${2:-}"
    for a in "${_apps[@]}"; do
      a="${a#"${a%%[![:space:]]*}"}"; a="${a%"${a##*[![:space:]]}"}"  # trim
      [ -n "$a" ] && printf '%s\n' "$a" >> "$ALLOW"
    done
    quit_disallowed
    if [ -n "${DRY_RUN:-}" ]; then
      rm -f "$ALLOW"
      echo "(dry run — no session started)"
      exit 0
    fi
    printf '%s\n' "${4:-}" > "$GOAL"
    printf '%s\n' "$(( $(date +%s) + mins * 60 ))" > "$ENDFILE"
    : > "$SENTINEL"
    # aggregate log (local, git-ignored): goal + count only, no app names
    mkdir -p history
    printf '{"start":"%s","minutes":%s,"allowed_count":%s,"goal":%s}\n' \
      "$(date '+%Y-%m-%dT%H:%M')" "$mins" "$(grep -c . "$ALLOW" || echo 0)" \
      "$(printf '%s' "${4:-}" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')" \
      >> history/focus_sessions.jsonl
    nohup "$0" _guard >/dev/null 2>&1 &
    echo "Focus session started: ${4:-(no goal)} — kept: $(tr '\n' ' ' < "$ALLOW")"
    ;;
  _guard)
    # internal: keep quitting non-allowed apps until the session ends
    while [ -f "$SENTINEL" ]; do
      end="$(cat "$ENDFILE" 2>/dev/null || echo 0)"
      [ "$(date +%s)" -ge "$end" ] && break
      quit_disallowed
      sleep 5
    done
    rm -f "$SENTINEL"
    ;;
  stop)
    rm -f "$SENTINEL"
    echo "Focus session ended — apps are free to open again."
    ;;
  status)
    if [ -f "$SENTINEL" ]; then
      echo "Active goal: $(cat "$GOAL" 2>/dev/null)"
      echo "Allowed apps: $(tr '\n' ' ' < "$ALLOW" 2>/dev/null)"
    else
      echo "No active focus session."
    fi
    ;;
  *)
    sed -n '2,14p' "$0"; exit 1
    ;;
esac
