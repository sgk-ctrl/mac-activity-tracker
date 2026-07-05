#!/bin/bash
# Biweekly review: collect native macOS activity -> rebuild dashboard -> open it.
# 100% local. Safe to run manually anytime. Run from the repo root.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "[$(date '+%Y-%m-%d %H:%M')] Running biweekly activity review..."

# Don't hard-fail the whole review if collection is partial; still rebuild.
python3 tracker.py --out my_activity_data.json || echo "tracker.py exited non-zero (partial data)."

if [ -f my_activity_data.json ]; then
  python3 build_dashboard.py --data my_activity_data.json --out dashboard.html
  # open only when run interactively (skip under launchd)
  if [ -t 1 ]; then open dashboard.html 2>/dev/null || true; fi
  echo "Done. Dashboard: $(pwd)/dashboard.html"
else
  echo "No data file produced; nothing to render."
  exit 1
fi
