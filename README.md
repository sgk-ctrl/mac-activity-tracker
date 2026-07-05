# mac-activity-tracker

**A 100% local macOS activity tracker — reads native Screen Time, browser, and CLI logs to give you a private biweekly productivity review. No cloud, no telemetry, no always-on process.**

![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Telemetry: none](https://img.shields.io/badge/telemetry-none-brightgreen)

It answers: *Where does my Mac time actually go? How much of it is deep focus vs. distraction? How much am I leaning on agentic tools (Claude, Codex, Hermes…), and what tools or workflow changes would amplify how I work?* — then re-assesses every two weeks.

> **Preview it now with zero setup:** open [`dashboard.sample.html`](dashboard.sample.html) — it's built from synthetic sample data, so the whole UI works before you touch your own data.

## Who this is for

- **Privacy-conscious knowledge workers** (developers, researchers, writers) who want quantified-self insight but won't send their browsing/app history to a cloud service.
- **Heavy AI / agentic-tool users** who want to see and optimize how Claude, Codex, Hermes, Cursor, etc. fit into their day.
- **Freelancers and solo operators** self-managing focus and effectiveness, with no manager and no corporate monitoring.
- **Local-first / quantified-self tinkerers** who want a small, auditable, dependency-free tool they can read and modify — not an opaque SaaS.

## Who this is *not* for

- **Managers or teams wanting to monitor other people.** This is a single-user, on-device tool with no central reporting or sync. Installing it on someone else's machine to surveil them is out of scope and against its spirit.
- **Anyone needing stopwatch-accurate or billable-hours tracking.** Durations are directional estimates (see *A note on accuracy*), not an invoicing time clock.
- **Windows or Linux users.** It reads macOS-specific data (Screen Time, macOS browser paths); it is macOS-only by design.
- **People who want a zero-terminal GUI app.** Setup is a couple of command-line steps and a Full Disk Access grant. There's no installer or menu-bar app (yet).
- **Teams wanting shared cloud dashboards.** There is intentionally no server, account, or sync — that's the point.

<!-- Add a real screenshot/GIF here before publishing: assets/demo.gif -->
<!-- ![Dashboard](assets/demo.gif) -->

## Why you can trust it

- **Auditable** — a few hundred lines of dependency-free Python. Read [`tracker.py`](tracker.py) end to end in a few minutes.
- **No network egress** — grep the source: no HTTP clients, sockets, or uploads. Chart.js is **vendored locally** (`vendor/`), not fetched from a CDN, so the dashboard is fully offline.
- **Read-only** — source databases are opened read-only (or via a private, auto-deleted temp copy). Originals are never modified.
- **No daemon** — runs on demand, or on a `launchd` timer *you* control. There is no always-on process and no screen recording.
- **Private by default** — only **domains** are stored (never full URLs or page titles); a `--redact` mode drops names entirely.

## Privacy & Data

This tool runs entirely on your machine. **No telemetry, no analytics, no network requests.**

### What is read, and where it goes

| Source | What's read | How | Where it goes |
|---|---|---|---|
| Screen Time (`knowledgeC.db`) | Per-app foreground time | Read-only | `my_activity_data.json` (local) |
| Browser history (Chrome / Arc / Safari) | Visited **domains** + visit times | Read-only | `my_activity_data.json` (local) |
| Shell history (`.zsh_history` / `.bash_history`) | **Only** invocations of agentic CLIs (e.g. `claude`, `codex`); arguments are ignored | Read-only | `my_activity_data.json` (local) |

- Output files (`my_activity_data.json`, `dashboard.html`) stay in the repo folder and are **git-ignored** so you can't accidentally publish them.
- The generated `dashboard.html` **embeds your data** — treat it like a private document; don't share it.

> **Disclaimer:** Provided "as is" without warranty (see [LICENSE](LICENSE)). It reads personal activity data on your Mac; you are responsible for how you store and share what it produces.

## Requirements

macOS 12+ and Python 3.9+ (both preinstalled on modern Macs). No pip packages required to run.

## Quickstart

```bash
git clone https://github.com/<you>/mac-activity-tracker.git
cd mac-activity-tracker

# 1) See the sample dashboard (no setup, no real data)
python3 build_dashboard.py --data sample/sample_data.json --out dashboard.sample.html
open dashboard.sample.html

# 2) Switch to YOUR data (needs Full Disk Access — see below)
python3 tracker.py                                   # -> my_activity_data.json
python3 build_dashboard.py --data my_activity_data.json
open dashboard.html
```

Or just: `make review`.

### Granting Full Disk Access

Reading the Screen Time and browser databases requires **Full Disk Access** for the terminal you run this from:

**System Settings ▸ Privacy & Security ▸ Full Disk Access** → add Terminal (or iTerm).

⚠️ This is a broad, persistent grant: it lets *anything* run in that terminal read sensitive files. Consider granting it to a dedicated terminal profile and **revoking it after your run**. Without it, app-usage and browser history are skipped (you'll get a clear warning) and the rest still works.

## Collection options

```bash
python3 tracker.py --days 14        # lookback window (default 14)
python3 tracker.py --no-browser     # app usage + CLI only
python3 tracker.py --no-shell       # skip shell history
python3 tracker.py --redact         # category + time only; drop all names
```

## Customizing categories

Edit [`categories.py`](categories.py) — plain data mapping apps/domains to categories and marking what counts as focus, distraction, or agentic. PRs adding common apps welcome.

## Automating the biweekly review

```bash
FOLDER="$(pwd)"
LABEL="com.$(whoami).activityreview"
sed -e "s|__PATH__|$FOLDER|g" -e "s|__LABEL__|$LABEL|g" \
    packaging/com.example.activityreview.plist > ~/Library/LaunchAgents/$LABEL.plist
launchctl load ~/Library/LaunchAgents/$LABEL.plist
```

It rebuilds the dashboard every ~14 days and logs to `review.log`. Cadence is approximate (a job due while the Mac is asleep runs on wake); use `StartCalendarInterval` for a fixed day/time.

**Uninstall:** `launchctl unload ~/Library/LaunchAgents/$LABEL.plist && rm ~/Library/LaunchAgents/$LABEL.plist`, then delete `my_activity_data.json`, `dashboard.html`, and `review.log`.

## How it works

`tracker.py` reads three native sources into a single JSON schema →
`build_dashboard.py` renders that JSON into a self-contained HTML dashboard
(data embedded as inert JSON, Chart.js from `vendor/`). The dashboard computes
KPIs (focus %, agentic-tool share, context-switches/day, distraction time),
several charts, and a rule-based biweekly assessment with tool/workflow suggestions.

## A note on accuracy

Durations are **estimates**. App usage comes from Screen Time (which may only
retain recent days and can be disabled). Web "time" is a visit-count × capped-dwell
proxy, not a true focus signal. Treat the numbers as **directional trends**, not stopwatch-accurate.

## Contributing / Security / License

- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Found a vulnerability? See [SECURITY.md](SECURITY.md) (please report privately).
- Full data-handling detail: [PRIVACY.md](PRIVACY.md)
- Scope & success criteria: [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md)
- Licensed under [MIT](LICENSE). Bundles Chart.js (MIT) in `vendor/`.
