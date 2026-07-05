# Definition of Done & Success Criteria

This project has two kinds of "done": the **release DoD** (is the software fit to
ship and use) and the **success criteria** (is it actually solving the problem
for the people it's for). They're deliberately separate — you can ship a clean
release that still fails to help anyone, and vice versa.

---

## 1. Release Definition of Done (per version)

A version is "done" only when **all** of these hold. ✅ = met in v0.1.0.

### Functional
- ✅ `tracker.py` collects app usage, browser history, and agentic-CLI usage on macOS into a single documented JSON schema.
- ✅ `build_dashboard.py` renders that JSON into a self-contained dashboard (KPIs, charts, assessment).
- ✅ Zero-setup preview works from synthetic sample data (`dashboard.sample.html`).
- ✅ Graceful degradation: missing sources, empty data, and non-macOS all produce clear messages, not stack traces.
- ✅ One-command biweekly path (`make review` / `run_review.sh`) and a `launchd` template.

### Privacy & security (non-negotiable)
- ✅ No network calls, no telemetry; Chart.js vendored locally.
- ✅ Source DBs opened read-only; any temp copy is `0700` and always deleted.
- ✅ Dashboard embeds data as inert JSON + HTML-escapes all data-derived strings (no injection).
- ✅ Private by default: domains only, secrets in shell args never read; `--redact` available.
- ✅ `.gitignore` prevents committing real data/output, **verified with `git check-ignore`**.

### Quality
- ✅ Test suite passes on Linux and macOS CI via fixtures (no Full Disk Access needed).
- ✅ Lint/format clean (ruff).
- ✅ Injection, empty-data, epoch-math, and CLI-matcher cases covered by tests.

### Docs & OSS hygiene
- ✅ README with a "what's read / where it goes" table and who-it's-for/-not-for.
- ✅ LICENSE, PRIVACY, SECURITY, CONTRIBUTING, Code of Conduct, CHANGELOG.
- ✅ A real screenshot in the README (`assets/dashboard.png`, built from the synthetic sample data).

**Definition of Done for a single PR:** `make test` + `make lint` pass · no real
data/secrets in the diff · privacy defaults unchanged or the change is opt-in and
documented · docs updated if behavior changed · a test added for any bug fix or
new collector.

---

## 2. Success criteria (is it working for people?)

Ship-quality ≠ useful. These define whether the tool earns its place.

### Primary outcome — the one that matters
- **A user changes one work habit because of an insight and it sticks.** Concretely: across two consecutive biweekly reviews, at least one tracked metric moves in the intended direction (e.g. context-switches/day ↓, deep-focus % ↑, or a targeted distraction ↓) **and** the user says the change was prompted by the dashboard.

### Leading indicators (per user)
- **Time-to-first-insight < 10 minutes** from `git clone` to seeing their own dashboard.
- **Setup completes without reading code** — the FDA prompt and warnings are enough.
- **Trust check passes** — a privacy-minded user can confirm "no network egress" by skimming the source and is comfortable running it.
- **Repeat use:** the user runs it again in the next cycle without being reminded (the biweekly habit forms).
- **Assessment is actionable, not just descriptive** — every review yields at least one recommendation the user considers worth trying.

### Project-health indicators (public repo)
- **Reproducible for strangers:** issues are about features/edge cases, *not* "it leaked my data," "it phoned home," or "it crashed on a clean Mac."
- **Contributable:** outside contributors can add an app/domain mapping via PR without touching core logic, and CI catches regressions.
- **Honest expectations:** users aren't surprised by accuracy — nobody treats the estimates as a billing clock because the docs set that expectation up front.

### Explicit non-goals (so we don't drift)
- Not aiming for minute-perfect time accounting.
- Not becoming a team/manager surveillance product.
- Not adding a cloud, account, or sync.
- Not expanding capture surface (full URLs, keystrokes, screenshots) — new sensitive capture must stay opt-in and justified.

### How you'd measure it (privately, locally)
Because there's no telemetry, success is measured by **you**, not by the tool:
your own two-cycle metric deltas, plus (for the public repo) qualitative signals —
stars/forks, the *nature* of issues, and whether people report a behavior change in
discussions. A tiny optional local `notes` field per review ("what I'll try next")
turns the tool into its own before/after log without sending anything anywhere.
