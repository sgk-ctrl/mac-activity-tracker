# Security Policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

This tool reads sensitive local data (Screen Time, browser history, shell
history). If you find a vulnerability — e.g. a path that could exfiltrate data
over the network, a write outside the project directory, or an injection in the
generated dashboard — report it privately:

- **Preferred:** GitHub → **Security** tab → **Report a vulnerability** (private disclosure).
- **Email:** sandheep@gmail.com

Please include the affected version/commit, macOS version, reproduction steps,
and impact. We aim to acknowledge within **72 hours** and to ship a fix or
mitigation for confirmed issues within **30 days**.

## Scope

In scope: unexpected network egress, writes outside the working directory, code
execution via crafted history/DB rows, and leakage of collected data.

Out of scope: issues that require an already-compromised machine, and the Full
Disk Access grant itself (that is user-granted and documented).

## Supported versions

Only the latest release and `main` receive security fixes.

## Security posture

- No network calls, no telemetry (Chart.js is vendored locally).
- Source DBs opened read-only; temp copies (if any) are `0700` and always removed.
- Dashboard embeds data as inert JSON (`<script type="application/json">`, parsed
  with `JSON.parse`) and HTML-escapes all data-derived strings, so a crafted
  hostname or title cannot execute script.
