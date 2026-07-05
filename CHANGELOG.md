# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

## [0.2.0] - 2026-07-06

Accuracy & trust release — the three P1 items from the v0.1.0 expert reviews.

### Fixed
- **Chrome/Arc history collection was broken** — the visits/urls join selected
  an ambiguous `url` column and errored on the real schema. Now qualified;
  covered by a fixture test using the real two-`url`-column shape.
- `read_only_db` mistook caller query errors for connection failures and
  yielded twice, crashing the context manager. Query errors now propagate.

### Changed
- **App usage is de-overlapped**: overlapping Screen Time rows are swept into
  non-overlapping segments (overlap goes to the most recently started app) and
  split at midnight, so per-day totals can never exceed 24h. Tested against a
  pathological 120h/day fixture.
- **Web dwell is per browsing-session across all browsers**: visits from every
  browser/profile merge into one timeline before dwell is estimated, so
  interleaved visits can't double-count the same wall-clock gap. Sessions end
  at a 15-minute idle cutoff.
- **CLI durations are real** where the shell recorded them (zsh
  `EXTENDED_HISTORY` elapsed field), capped like app rows; entries without a
  recorded duration keep a small nominal credit.
- Dev tooling: ruff pinned to `>=0.15,<0.16` so formatting can't drift between
  local and CI.

## [0.1.0] - 2026-07-05

Initial public release.

### Added
- `tracker.py` — local collector for Screen Time app usage, browser history
  (Chrome/Arc/Safari), and agentic-CLI usage, with `--days`, `--redact`,
  `--no-browser`, `--no-shell` options and a non-macOS guard.
- `build_dashboard.py` + `templates/dashboard.html.tmpl` — self-contained
  dashboard with KPIs, charts, and a rule-based biweekly assessment.
- Synthetic sample data and a zero-setup preview (`dashboard.sample.html`).
- `launchd` template for an automatic biweekly review.
- Test suite (fixture-based, runs without macOS) and GitHub Actions CI.
- Community/legal docs: LICENSE (MIT), PRIVACY, SECURITY, CONTRIBUTING, Code of Conduct.

### Security / privacy
- Data embedded as inert JSON with HTML-escaping (no script injection from
  hostnames/titles).
- Chart.js vendored locally — dashboard is fully offline, no CDN.
- Read-only DB access with guaranteed temp-file cleanup.
- Domain-only capture by default; secrets in shell arguments are never read.
