#!/usr/bin/env python3
"""Print the domains focus mode should block, one per line.

Data-driven: the distraction-category domains actually seen in YOUR activity
data (my_activity_data.json), merged with a small built-in list of usual
suspects. Works with no data file too (fallback list only). Redacted data
stores category names instead of domains — those are filtered out.

Used by scripts/focus.sh; safe to run standalone to preview the list.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from categories import DISTRACTION_CATEGORIES  # noqa: E402

FALLBACK = [
    "facebook.com",
    "instagram.com",
    "netflix.com",
    "reddit.com",
    "tiktok.com",
    "twitch.tv",
    "twitter.com",
    "x.com",
    "youtube.com",
]


def blocklist(data_path):
    domains = set(FALLBACK)
    try:
        with open(data_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return sorted(domains)
    for s in data.get("sessions", []):
        name = s.get("name", "")
        # domains only: redacted data stores category names (no dot) — skip
        if s.get("kind") == "web" and s.get("category") in DISTRACTION_CATEGORIES and "." in name:
            domains.add(name)
    return sorted(domains)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "my_activity_data.json"
    print("\n".join(blocklist(path)))
