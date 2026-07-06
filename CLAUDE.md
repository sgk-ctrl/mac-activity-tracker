# CLAUDE.md — project memory for Claude Code

Claude Code loads this file automatically. It defines what this project is and the
rules you must not break while working on it.

## What this is
`mac-activity-tracker` — a 100% local macOS activity tracker that reads native
logs (Screen Time `knowledgeC.db`, Chrome/Arc/Safari history, agentic-CLI shell
history) and renders a self-contained HTML dashboard plus a biweekly productivity
assessment. Intended for public release on GitHub. See `README.md`,
`PRIVACY.md`, and `DEFINITION_OF_DONE.md` for full context.

## Hard invariants (do NOT violate)
1. **No network egress, ever.** The collector and dashboard make zero network
   calls. Chart.js is vendored in `vendor/`. Never add a CDN, telemetry, analytics,
   HTTP client, or "phone home" — not even opt-in analytics.
2. **Read-only + no data leaks.** Source DBs are opened read-only via
   `read_only_db()`. Any temp copy must be `0700` and always removed. Never write
   to a user's real DBs. The ONE sanctioned exception to "never write outside
   the repo" is focus mode (`scripts/focus.sh`): it edits `/etc/hosts` between
   exact marker lines, requires sudo, is opt-in per invocation, and `off` must
   restore the file byte-identically (tested). Nothing else may write outside
   the repo folder.
   Focus SESSIONS (`scripts/focus_session.sh`) may quit the user's other apps,
   but only via graceful AppleScript `quit` (never force-kill), only after an
   explicit confirmation in the app, and never an app on the protect-list in
   `scripts/focus_apps.py` (Finder, terminals, this tracker, system UI). Its
   guard loop is the toolkit's only background process and must be
   session-scoped — it exits when the session ends. `DRY_RUN=1` must make it
   report intended quits and change nothing.
3. **Private by default.** Store domains only — never full URLs, page titles, or
   shell-command arguments. Any new sensitive capture must be OFF by default and
   opt-in via an explicit flag.
4. **Never commit real data.** `my_activity_data.json`, `dashboard.html`, and
   `*.log` are git-ignored. Only `sample/sample_data.json` and
   `dashboard.sample.html` (synthetic) are tracked. Verify with `git check-ignore`.
5. **No injection.** Dashboard data is embedded as inert JSON
   (`<script type="application/json">` + `JSON.parse`) and all data-derived strings
   are HTML-escaped. Keep it that way.
6. **stdlib-only runtime.** No new runtime dependencies. Dev tools (pytest, ruff)
   only. macOS-only behavior must degrade gracefully elsewhere.

## Commands
- `make test` — pytest (fixture-based, runs without macOS/Full Disk Access)
- `make lint` — `ruff check` + `ruff format --check`
- `make dashboard` — rebuild `dashboard.sample.html` from sample data
- `make review` — collect real data + build + open (macOS only)

## Definition of done for any change
`make test` + `make lint` pass · no real data/secrets in the diff · privacy
defaults unchanged or the change is opt-in and documented · a test added for any
bug fix or new collector · README/PRIVACY updated if behavior changed.

## Where things live
- `tracker.py` — collectors (`collect_app_usage`, `collect_chrome_like`,
  `collect_safari`, `collect_cli`) + `read_only_db` + `main`.
- `categories.py` — app/domain → category maps and agentic-tool lists (data only).
- `build_dashboard.py` + `templates/dashboard.html.tmpl` — rendering + inert-JSON
  embedding + HTML escaping.
- `sample/` — synthetic data generator. `tests/` — fixture-based tests.
- `vendor/` — Chart.js (MIT), local. `packaging/` — launchd template.

## Known limitations to respect when changing behavior
- Web "minutes" is a coarse visit-count × capped-dwell proxy, not real focus time.
- Screen Time may retain only recent days and can be disabled.
- Durations are estimates — keep them labeled as such in UI and docs.
