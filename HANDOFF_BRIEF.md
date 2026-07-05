# Handoff brief — continue in Claude Code

This is everything you need to pick up `mac-activity-tracker` in Claude Code.

## 0. Get the code onto your machine

The full project is the artifact **`mac-activity-tracker.zip`** produced in this
session (shared as a file card in the chat). To start in Claude Code:

```bash
unzip mac-activity-tracker.zip        # from your Downloads/output folder
cd mac-activity-tracker
git init && git add -A && git commit -m "Initial commit: v0.1.0"
claude          # launch Claude Code in the repo root
```

Claude Code will auto-load `CLAUDE.md` (guardrails + orientation). Read
`README.md`, `PRIVACY.md`, and `DEFINITION_OF_DONE.md` for full context.

## 1. Current state (v0.1.0)

Working and verified: collectors for Screen Time app usage, browser history, and
agentic-CLI usage; a self-contained dashboard with KPIs, charts, and a rule-based
biweekly assessment; synthetic sample + zero-setup preview; launchd template;
11 passing tests; ruff clean; GitHub Actions CI (Ubuntu + macOS). Three expert
reviews (security, correctness, OSS packaging) were applied — see the git history
message and `CHANGELOG.md`.

Repo layout:
```
tracker.py  build_dashboard.py  categories.py
templates/dashboard.html.tmpl   vendor/chart.umd.min.js
sample/  scripts/  packaging/  tests/  .github/workflows/ci.yml
README PRIVACY SECURITY CONTRIBUTING CODE_OF_CONDUCT CHANGELOG
DEFINITION_OF_DONE  CLAUDE.md  Makefile  pyproject.toml  .gitignore
```

## 2. First thing to do in Claude Code

Sanity-check the environment, then make the smallest real change end-to-end:

```
Read CLAUDE.md and DEFINITION_OF_DONE.md. Run `make test` and `make lint` and
confirm both pass. Then add a README screenshot: build the sample dashboard,
capture assets/dashboard.png, and embed it near the top of README.md. Keep all
CLAUDE.md invariants.
```

(The README screenshot is the one remaining v0.1.0 DoD item.)

## 3. Prioritized backlog (from the reviews + DoD)

**P1 — accuracy & trust**
- Improve web dwell-time: compute per browsing-session with an idle cutoff instead
  of the current global gap heuristic; label clearly. Add tests.
- De-overlap app-usage intervals so daily totals can't exceed wall-clock; clamp
  per-day. Add a test asserting ≤24h/day.
- Real CLI durations from zsh `EXTENDED_HISTORY` duration field (replace nominal 5 min).

**P2 — robustness & packaging**
- Schema-probe `knowledgeC.db` (columns/stream may vary by macOS version); degrade
  gracefully. Test against fixtures for macOS 12–15 shapes.
- Optionally package as `pipx`-installable with `activity-tracker` / `activity-review`
  entry points (keep stdlib-only runtime).
- Add `StartCalendarInterval` launchd variant for a fixed day/time.

**P3 — product value**
- Optional local `notes` field per review ("what I'll try next") to make the tool
  its own before/after log (no telemetry).
- Trend view across multiple runs (store dated snapshots in a local history dir).
- Optional AI-summary mode that sends only the *aggregated summary* (never raw
  activity) to a model — must be opt-in and off by default.

## 4. Guardrails (do not break — full list in CLAUDE.md)
No network egress · read-only DB access with guaranteed temp cleanup · domains-only
by default, new sensitive capture is opt-in · never commit real data · inert-JSON +
HTML-escaping in the dashboard · stdlib-only runtime · durations stay labeled as
estimates.

## 5. Definition of done for each PR
`make test` + `make lint` pass · no real data/secrets in the diff · privacy
defaults unchanged or opt-in + documented · test added for any fix/new collector ·
docs updated if behavior changed. Success criteria (product outcomes) are in
`DEFINITION_OF_DONE.md`.

## 6. Artifacts from the Cowork session
All are inside the zip; the ones shared as file cards in chat were:
- `mac-activity-tracker.zip` — the full repo (portable bundle to move to Claude Code)
- `README.md` — includes "Who this is for / not for"
- `DEFINITION_OF_DONE.md` — release DoD + success criteria
- `dashboard.sample.html` — zero-setup preview
- `tracker.py` — the collector
- `CLAUDE.md` (this addition) — guardrails Claude Code auto-loads
