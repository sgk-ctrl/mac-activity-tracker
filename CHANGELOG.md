# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

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
