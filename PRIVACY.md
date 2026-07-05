# Privacy

mac-activity-tracker is designed to keep some of the most sensitive data on your
Mac exactly where it is: on your Mac.

## Principles

- **Local only.** No network requests, no telemetry, no analytics, no accounts.
  Chart.js is vendored in `vendor/`, so even the dashboard makes no external calls.
- **Read-only.** Source databases are opened read-only, either via SQLite's
  immutable/nolock URI (no copy) or, if that fails, via a private `0700` temp
  copy that is deleted on every exit path (including errors). Originals are
  never modified.
- **Minimal by default.** Only **domains** are stored — never full URLs, query
  strings, or page titles. From shell history, only the command name (argv[0])
  of known agentic tools is recorded; arguments (which may contain secrets) are
  never read into the output.
- **You own the output.** `my_activity_data.json` and `dashboard.html` are
  written to the repo folder and are git-ignored so they can't be committed by
  accident. The dashboard embeds your data inline — treat it as private.

## What is collected

| Source | Field(s) | Notes |
|---|---|---|
| `~/Library/Application Support/Knowledge/knowledgeC.db` | app bundle id → display name, focus start/end | Screen Time; requires Full Disk Access |
| Chrome / Arc / Safari history DBs | domain, visit time | full URLs are discarded; only the host is kept |
| `~/.zsh_history` / `~/.bash_history` | argv[0] of agentic CLIs, timestamp | arguments ignored; undated entries skipped, not fabricated |

## Redaction

Run `python3 tracker.py --redact` to store **only** category + time buckets and
drop every app/site name. `--no-browser` and `--no-shell` further narrow what is
read.

## Full Disk Access

Reading Screen Time and browser DBs requires granting Full Disk Access to your
terminal. This is a broad macOS permission — it lets any process in that
terminal read protected files. We recommend granting it to a dedicated terminal
and revoking it when you're done. See the README for details.

## Third parties

None. There are no third-party services, SDKs, or trackers. The only bundled
third-party code is Chart.js (MIT), served locally.
