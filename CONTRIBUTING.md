# Contributing

Thanks for helping improve mac-activity-tracker! It's a small, dependency-free
project — contributions of new app/domain mappings, accuracy fixes, and docs are
especially welcome.

## Dev setup

```bash
git clone https://github.com/<you>/mac-activity-tracker.git
cd mac-activity-tracker
python3 -m pip install -r requirements-dev.txt   # pytest, ruff
make test        # run the test suite (works on Linux/macOS via fixtures)
make lint        # ruff + format check
```

## Ground rules

- **Never commit real data.** `my_activity_data.json`, `dashboard.html`, and
  `*.log` are git-ignored; keep it that way. Only `sample/sample_data.json`
  (synthetic) and `dashboard.sample.html` are tracked.
- **No new runtime dependencies.** The collector must stay stdlib-only and make
  **no network calls**. Bundled front-end libs live in `vendor/` (pinned, MIT).
- **Preserve privacy defaults.** Don't capture full URLs, page titles, or shell
  command arguments by default. New sensitive capture must be opt-in.
- **Add a test.** Bug fixes and new collectors should come with a fixture-based
  test that runs in CI without macOS.

## Good first contributions

- Add apps/domains to [`categories.py`](categories.py).
- Improve the web dwell-time estimate (it's a coarse proxy today).
- Real CLI session durations from zsh `EXTENDED_HISTORY` duration fields.
- A `StartCalendarInterval` variant of the launchd template.

## PR checklist

- [ ] `make test` and `make lint` pass
- [ ] No real personal data or secrets in the diff
- [ ] Privacy defaults unchanged (or the change is opt-in and documented)
- [ ] README/PRIVACY updated if behavior changed
