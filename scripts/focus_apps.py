#!/usr/bin/env python3
"""Decide which running apps focus mode should ask to quit.

Reads the list of currently-visible app names on stdin (one per line, as
produced by System Events), plus an allowlist file path as argv[1]. Prints the
apps to quit, one per line.

Pure decision logic, kept out of the shell so it can be unit-tested on any OS.
The actual quitting is done by focus_session.sh via `osascript ... to quit`
(graceful — apps may prompt to save; nothing is force-killed).
"""

import sys

# Never asked to quit, even if not on the allowlist. These keep the desktop,
# the terminal you may have launched from, the tracker app, and the automation
# bridge alive so a session can't lock you out or lose the guard process.
PROTECTED = {
    "activity review",
    "control center",
    "controlcenter",
    "dock",
    "finder",
    "iterm",
    "iterm2",
    "loginwindow",
    "notification center",
    "notificationcenter",
    "spotlight",
    "system events",
    "systemuiserver",
    "terminal",
    "warp",
    "windowserver",
}


def to_quit(running, allowed):
    """running, allowed: iterables of app display names. Returns the ordered,
    de-duplicated list of running apps that are neither allowed nor protected."""
    allow = {a.strip().lower() for a in allowed if a.strip()} | PROTECTED
    seen, out = set(), []
    for name in running:
        name = name.strip()
        key = name.lower()
        if name and key not in allow and key not in seen:
            seen.add(key)
            out.append(name)
    return out


if __name__ == "__main__":
    allowed = []
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as f:
                allowed = f.read().splitlines()
        except OSError:
            pass
    running = sys.stdin.read().splitlines()
    print("\n".join(to_quit(running, allowed)))
