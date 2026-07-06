#!/bin/bash
# Build "Activity Review.app" from packaging/applet.applescript.tmpl using
# osacompile (ships with macOS — no Xcode, no downloads).
#
#   make app                      # builds into ~/Applications
#   bash packaging/build_app.sh dist   # or build into ./dist (CI uses this)
#
# The app is a plain AppleScript applet: read the template to audit everything
# it can do. Rebuild after moving the repo — the repo path is baked in.
set -euo pipefail
cd "$(dirname "$0")/.."

DEST="${1:-$HOME/Applications}"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"   # absolute, so the FDA instructions are pasteable
APP="$DEST/Activity Review.app"

TMP="$(mktemp -t applet).applescript"
sed "s|__PATH__|$(pwd)|g" packaging/applet.applescript.tmpl > "$TMP"
osacompile -o "$APP" "$TMP"
rm -f "$TMP"

cat <<EOF
✅ Built: $APP

One-time setup so the app can read Screen Time + Safari history:
  System Settings ▸ Privacy & Security ▸ Full Disk Access
  → click +, add "$APP"
This grants FDA to ONLY this app — narrower than granting it to your
whole terminal. (Chrome history + CLI usage work even without it.)

Double-click the app to run a review or toggle focus mode.
EOF
