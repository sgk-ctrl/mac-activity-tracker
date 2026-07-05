#!/usr/bin/env python3
"""Generate 14 days of realistic *synthetic* activity data so the dashboard can
be previewed with zero setup and no real personal data. Deterministic (seeded).
Output: sample/sample_data.json"""

import datetime as dt
import json
import os
import random

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__))

APPS = {
    "Claude (Cowork)": ("AI / Agentic", 9, True),
    "Codex CLI": ("AI / Agentic", 6, True),
    "Hermes": ("AI / Agentic", 4, True),
    "Cursor": ("Coding", 10, True),
    "VS Code": ("Coding", 8, False),
    "iTerm2": ("Coding", 7, False),
    "Google Chrome": ("Browsing", 12, False),
    "Arc": ("Browsing", 5, False),
    "Slack": ("Communication", 8, False),
    "Mail": ("Communication", 4, False),
    "Zoom": ("Meetings", 5, False),
    "Notion": ("Docs / Notes", 5, False),
    "Figma": ("Design", 3, False),
    "Spotify": ("Media", 4, False),
    "Messages": ("Communication", 3, False),
    "Preview": ("Docs / Notes", 2, False),
}
SITES = {
    "github.com": ("Coding", 11, False),
    "claude.ai": ("AI / Agentic", 8, True),
    "chatgpt.com": ("AI / Agentic", 5, True),
    "stackoverflow.com": ("Coding", 5, False),
    "docs.python.org": ("Coding", 3, False),
    "youtube.com": ("Media", 7, False),
    "news.ycombinator.com": ("News / Reading", 5, False),
    "twitter.com": ("Social", 6, False),
    "linkedin.com": ("Social", 3, False),
    "gmail.com": ("Communication", 5, False),
    "calendar.google.com": ("Meetings", 3, False),
    "notion.so": ("Docs / Notes", 4, False),
    "figma.com": ("Design", 2, False),
    "amazon.com": ("Shopping", 2, False),
    "reddit.com": ("Social", 4, False),
    "vercel.com": ("Coding", 2, False),
}


def pick(cat):
    names = list(cat)
    return random.choices(names, weights=[cat[n][1] for n in names])[0]


def main():
    sessions = []
    start_day = dt.date.today() - dt.timedelta(days=13)
    for d in range(14):
        day = start_day + dt.timedelta(days=d)
        weekend = day.weekday() >= 5
        n = random.randint(5, 10) if weekend else random.randint(14, 22)
        clock = dt.datetime.combine(day, dt.time(random.randint(8, 9), random.randint(0, 40)))
        for _ in range(n):
            if random.random() < 0.62:
                name = pick(APPS)
                cat, _, ag = APPS[name]
                kind = "app"
            else:
                name = pick(SITES)
                cat, _, ag = SITES[name]
                kind = "web"
            mins = random.choices([3, 7, 12, 18, 25, 40, 55], weights=[6, 10, 9, 7, 5, 3, 2])[0]
            sessions.append(
                {
                    "start": clock.isoformat(timespec="minutes"),
                    "name": name,
                    "kind": kind,
                    "category": cat,
                    "is_agentic": ag,
                    "minutes": mins,
                }
            )
            clock += dt.timedelta(minutes=mins + random.randint(0, 6))
            if clock.hour >= 23:
                break
    data = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "window_start": start_day.isoformat(),
        "window_end": (start_day + dt.timedelta(days=13)).isoformat(),
        "source": "sample",
        "estimates": True,
        "redacted": False,
        "sessions": sessions,
    }
    out = os.path.join(HERE, "sample_data.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=1)
    print(f"{out}: {len(sessions)} sessions, {sum(s['minutes'] for s in sessions) / 60:.1f}h")


if __name__ == "__main__":
    main()
