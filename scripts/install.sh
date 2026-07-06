#!/bin/bash
# One-line installer for mac-activity-tracker.
#   curl -fsSL https://raw.githubusercontent.com/sgk-ctrl/mac-activity-tracker/main/scripts/install.sh | bash
#
# What it does (and nothing more):
#   1. Checks you're on macOS with python3 + git (both ship with Xcode CLT).
#   2. Clones the repo to ~/mac-activity-tracker (or updates an existing clone).
#   3. Builds and opens the SAMPLE dashboard so you see the tool before it
#      touches any of your data.
#   4. Prints the Full Disk Access walkthrough for your first real run.
# No sudo. No PATH changes. Nothing leaves your machine.
set -euo pipefail

REPO="https://github.com/sgk-ctrl/mac-activity-tracker.git"
DEST="$HOME/mac-activity-tracker"

if [ "$(uname)" != "Darwin" ]; then
  echo "This tool reads macOS-native logs and only runs on macOS." >&2
  exit 1
fi
for cmd in python3 git; do
  if ! command -v "$cmd" >/dev/null; then
    echo "'$cmd' not found. Install Apple's command-line tools first:" >&2
    echo "    xcode-select --install" >&2
    exit 1
  fi
done

if [ -d "$DEST/.git" ]; then
  echo "Updating existing install at $DEST ..."
  git -C "$DEST" pull --ff-only
else
  echo "Cloning to $DEST ..."
  git clone --depth 1 "$REPO" "$DEST"
fi

cd "$DEST"
echo
echo "Building the sample dashboard (synthetic data — none of yours) ..."
python3 sample/build_sample_data.py >/dev/null
python3 build_dashboard.py --data sample/sample_data.json \
  --history-dir sample/history --out dashboard.sample.html >/dev/null
open dashboard.sample.html || true

cat <<'EOF'

✅ Installed. The dashboard that just opened is SAMPLE data.

To see YOUR data (one-time setup, ~2 minutes):

  1. Grant Full Disk Access to your terminal — this lets it read the
     Screen Time and browser history databases:
        System Settings ▸ Privacy & Security ▸ Full Disk Access
        → toggle ON for Terminal (or iTerm, whichever you use)
        → quit and reopen the terminal afterwards
     (You can revoke this after each run if you prefer.)

  2. Run your first review:
        cd ~/mac-activity-tracker && make review

Everything stays on your Mac: no accounts, no cloud, no telemetry.
Docs: https://github.com/sgk-ctrl/mac-activity-tracker#readme
EOF
