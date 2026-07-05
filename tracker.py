#!/usr/bin/env python3
"""
tracker.py - 100% local macOS activity collector.

Reads NATIVE macOS logs (no always-on process, no screen recording):
  1. App usage        -> ~/Library/Application Support/Knowledge/knowledgeC.db (Screen Time)
  2. Browser history  -> Chrome / Arc / Safari history SQLite DBs
  3. Agentic CLI use  -> ~/.zsh_history / ~/.bash_history (claude, codex, hermes, ...)

Writes my_activity_data.json (git-ignored) in the schema the dashboard consumes.
Nothing leaves your machine. Source DBs are opened read-only and never modified.

Privacy defaults (see --help):
  * Only DOMAINS are stored, never full URLs or page titles.
  * --redact drops all names and keeps category + time only.
  * --no-browser / --no-shell let you narrow what is collected.

Requires macOS and, for the Screen Time / browser DBs, Full Disk Access for your
terminal (System Settings > Privacy & Security > Full Disk Access).
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

from categories import (
    AGENTIC_APP_FRAGMENTS,
    AGENTIC_CLI,
    AGENTIC_DOMAINS,
    APP_CATEGORY,
    DOMAIN_CATEGORY,
)

HOME = os.path.expanduser("~")
MAC_EPOCH = dt.datetime(2001, 1, 1)  # CFAbsoluteTime reference (local, naive)
CHROME_EPOCH = dt.datetime(1601, 1, 1)  # WebKit/Chrome reference

# per-row / per-visit sanity caps (minutes). Durations are ESTIMATES.
APP_ROW_CAP_MIN = 240  # clamp absurdly long single app-usage rows
WEB_DWELL_CAP_MIN = 5  # a single web visit is credited at most this
WEB_IDLE_GAP_MIN = 15  # a gap larger than this ends a browsing session
WEB_FLOOR_MIN = 1
CLI_FLOOR_MIN = 1  # a CLI invocation is credited at least this
CLI_FALLBACK_MIN = 5  # when the shell recorded no elapsed time


# --------------------------------------------------------------------------- io
@contextlib.contextmanager
def read_only_db(path):
    """Open a SQLite DB read-only without mutating or leaking it.

    Strategy: try SQLite's immutable/nolock URI (no copy at all). If the DB is
    being written and that fails, fall back to a copy inside a private 0700
    temp dir that is ALWAYS removed (including -wal/-shm), even on error.
    """
    # 1) no-copy read. NOTE: only the connection attempt is inside the retry
    # loop — the yield happens exactly once, after a working connection is
    # found, so exceptions raised by the caller's queries propagate instead of
    # being mistaken for a connection failure (which would make this generator
    # yield a second time and crash the context manager).
    conn = None
    for uri in (f"file:{path}?immutable=1", f"file:{path}?mode=ro&nolock=1"):
        try:
            candidate = sqlite3.connect(uri, uri=True, timeout=2)
            candidate.execute("SELECT 1")
            conn = candidate
            break
        except sqlite3.Error:
            with contextlib.suppress(Exception):
                candidate.close()
    if conn is not None:
        try:
            yield conn
        finally:
            conn.close()
        return
    # 2) safe private copy
    tmpdir = tempfile.mkdtemp(prefix="mat_")
    try:
        os.chmod(tmpdir, 0o700)
        dst = os.path.join(tmpdir, "copy.db")
        shutil.copy2(path, dst)
        for ext in ("-wal", "-shm"):
            if os.path.exists(path + ext):
                shutil.copy2(path + ext, dst + ext)
        conn = sqlite3.connect(f"file:{dst}?mode=ro", uri=True)
        try:
            yield conn
        finally:
            conn.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def cat_for_domain(host):
    for pat, cat in DOMAIN_CATEGORY:
        if re.search(pat, host):
            return cat
    return "Browsing"


# ------------------------------------------------------------------ collectors
def _deoverlap(intervals):
    """intervals: list of (start_dt, end_dt, key). Screen Time rows can overlap
    (e.g. duplicate streams or re-focus events), which inflates totals past
    wall-clock. Sweep the timeline and attribute every moment to exactly ONE
    interval — the most recently started active one (foreground-follows-latest).
    Returns non-overlapping (start, end, key) segments whose total duration can
    never exceed the wall-clock span they cover."""
    events = []
    for idx, (s, e, _key) in enumerate(intervals):
        if e > s:
            events.append((s, 1, idx))  # start
            events.append((e, 0, idx))  # end (process ends first at same t)
    events.sort(key=lambda ev: (ev[0], ev[1]))
    active = {}  # idx -> start time
    segs = []
    prev_t = None
    for t, kind, idx in events:
        if prev_t is not None and active and t > prev_t:
            owner = max(active, key=lambda i: (active[i], i))
            segs.append([prev_t, t, intervals[owner][2]])
        if kind == 1:
            active[idx] = intervals[idx][0]
        else:
            active.pop(idx, None)
        prev_t = t
    # merge back-to-back segments of the same key
    merged = []
    for s, e, key in segs:
        if merged and merged[-1][2] == key and merged[-1][1] == s:
            merged[-1][1] = e
        else:
            merged.append([s, e, key])
    return [(s, e, key) for s, e, key in merged]


def _split_at_midnight(start, end):
    """Yield (start, end) pieces that never cross a day boundary, so per-day
    totals stay exact (and provably ≤ 24h once intervals don't overlap)."""
    cur = start
    while cur.date() < end.date():
        nxt = dt.datetime.combine(cur.date() + dt.timedelta(days=1), dt.time())
        if nxt > cur:
            yield cur, nxt
        cur = nxt
    if end > cur:
        yield cur, end


def collect_app_usage(since, warnings):
    """Screen Time app-focus intervals from knowledgeC.db, de-overlapped so
    daily totals can never exceed wall-clock time."""
    db = os.path.join(HOME, "Library/Application Support/Knowledge/knowledgeC.db")
    out = []
    if not os.path.exists(db):
        warnings.append("knowledgeC.db not found - Screen Time app usage unavailable.")
        return out
    since_cf = (since - MAC_EPOCH).total_seconds()
    q = """
        SELECT ZVALUESTRING AS bundle, ZSTARTDATE AS s, ZENDDATE AS e
        FROM ZOBJECT
        WHERE ZSTREAMNAME = '/app/usage'
          AND ZSTARTDATE IS NOT NULL AND ZENDDATE IS NOT NULL
          AND ZSTARTDATE > ?
        ORDER BY ZSTARTDATE
    """
    try:
        with read_only_db(db) as conn:
            rows = list(conn.execute(q, (since_cf,)))
    except (sqlite3.Error, OSError) as e:
        warnings.append(f"Could not read knowledgeC.db (grant Full Disk Access): {e}")
        return out
    intervals = []
    for bundle, s, e in rows:
        start = MAC_EPOCH + dt.timedelta(seconds=s)
        end = MAC_EPOCH + dt.timedelta(seconds=e)
        if end > start:
            intervals.append((start, end, bundle))
    for seg_start, seg_end, bundle in _deoverlap(intervals):
        for start, end in _split_at_midnight(seg_start, seg_end):
            minutes = round((end - start).total_seconds() / 60, 1)
            if minutes < 0.5:
                continue
            minutes = min(minutes, APP_ROW_CAP_MIN)  # clamp outliers (estimate)
            name, cat = APP_CATEGORY.get(bundle, (None, "Other"))
            agentic = any(a in (bundle or "").lower() for a in AGENTIC_APP_FRAGMENTS)
            if name is None:
                name = (bundle or "unknown").split(".")[-1]
            if agentic and cat == "Other":
                cat = "AI / Agentic"
            out.append(
                {
                    "start": start.isoformat(timespec="minutes"),
                    "name": name,
                    "kind": "app",
                    "category": cat,
                    "is_agentic": agentic,
                    "minutes": minutes,
                }
            )
    print(f"  app usage rows: {len(out)}")
    if not out:
        warnings.append(
            "Screen Time returned no app usage (may be disabled, or only recent days are retained)."
        )
    return out


def _visits_from_rows(rows):
    """rows: iterable of (host, datetime) for ALL browsers combined, sorted by
    time. Visits are grouped into browsing sessions: a gap larger than
    WEB_IDLE_GAP_MIN ends a session. Within a session each visit's dwell is
    the gap to the next visit (capped at WEB_DWELL_CAP_MIN); the last visit of
    a session gets a floor credit. Coarse proxy, not a real focus signal —
    rows must be pre-merged across browsers/profiles or interleaved visits
    would each claim the same wall-clock gap twice."""
    out = []
    rows = sorted(rows, key=lambda r: r[1])
    times = [t for _, t in rows]
    for i, (host, t) in enumerate(rows):
        gap = None
        if i + 1 < len(times):
            gap = (times[i + 1] - t).total_seconds() / 60
        if gap is None or gap > WEB_IDLE_GAP_MIN or gap < 0:
            mins = WEB_FLOOR_MIN  # session end (or clock skew): floor credit
        else:
            mins = round(min(gap, WEB_DWELL_CAP_MIN), 1)
        out.append(
            {
                "start": t.isoformat(timespec="minutes"),
                "name": host,
                "kind": "web",
                "category": cat_for_domain(host),
                "is_agentic": bool(re.search(AGENTIC_DOMAINS, host)),
                "minutes": mins,
            }
        )
    return out


def _host(url, fallback=""):
    m = re.findall(r"https?://([^/]+)", url or "")
    host = m[0] if m else fallback
    return re.sub(r"^www\.", "", host)


def collect_chrome_like(path, since, label, warnings):
    """Return raw (host, time) visit rows from one Chrome-family history DB."""
    if not os.path.exists(path):
        return []
    try:
        with read_only_db(path) as conn:
            raw = conn.execute(
                "SELECT urls.url, visits.visit_time FROM visits "
                "JOIN urls ON urls.id = visits.url ORDER BY visits.visit_time"
            ).fetchall()
    except (sqlite3.Error, OSError) as e:
        warnings.append(f"{label}: {e}")
        return []
    rows = []
    for url, vt in raw:
        t = CHROME_EPOCH + dt.timedelta(microseconds=vt)
        host = _host(url)
        if t >= since and host:
            rows.append((host, t))
    return rows


def collect_safari(since, warnings):
    """Return raw (host, time) visit rows from Safari's history DB."""
    path = os.path.join(HOME, "Library/Safari/History.db")
    if not os.path.exists(path):
        return []
    try:
        with read_only_db(path) as conn:
            raw = conn.execute(
                "SELECT hi.domain_expansion, hi.url, hv.visit_time "
                "FROM history_visits hv JOIN history_items hi ON hi.id = hv.history_item "
                "ORDER BY hv.visit_time"
            ).fetchall()
    except (sqlite3.Error, OSError) as e:
        warnings.append(f"Safari: {e}")
        return []
    rows = []
    for domain, url, vt in raw:
        t = MAC_EPOCH + dt.timedelta(seconds=vt)
        host = _host(url, fallback=domain or "")
        if t >= since and host:
            rows.append((host, t))
    return rows


def collect_browsers(since, warnings):
    """Merge visits from every browser/profile into ONE timeline before
    estimating dwell, so interleaved visits from two browsers can't both
    claim the same wall-clock gap."""
    rows = []
    for hist in glob.glob(HOME + "/Library/Application Support/Google/Chrome/*/History"):
        rows += collect_chrome_like(hist, since, "Chrome", warnings)
    for hist in glob.glob(HOME + "/Library/Application Support/Arc/User Data/*/History"):
        rows += collect_chrome_like(hist, since, "Arc", warnings)
    rows += collect_safari(since, warnings)
    out = _visits_from_rows(rows)
    print(f"  browser visits: {len(out)}")
    if not out:
        warnings.append(
            "No browser history read (grant Full Disk Access, or no supported browser installed)."
        )
    return out


def _argv0(cmd):
    """First real command token, stripping common prefixes."""
    parts = cmd.split()
    i = 0
    while i < len(parts) and parts[i] in ("sudo", "env", "time", "nohup"):
        i += 1
        # skip VAR=val assignments after env
        while i < len(parts) and "=" in parts[i] and not parts[i].startswith("-"):
            i += 1
    return os.path.basename(parts[i]) if i < len(parts) else ""


def collect_cli(since, warnings):
    """Agentic CLI invocations from shell history. Only argv[0] is inspected;
    command arguments (which may contain secrets) are never stored."""
    out = []
    undated_skipped = 0
    for hf in (".zsh_history", ".bash_history"):
        p = os.path.join(HOME, hf)
        if not os.path.exists(p):
            continue
        try:
            lines = open(p, errors="ignore").read().splitlines()
        except OSError:
            continue
        for ln in lines:
            # zsh EXTENDED_HISTORY: ": <start_epoch>:<elapsed_seconds>;<command>"
            m = re.match(r"^:\s*(\d+):(\d+);(.*)$", ln)
            if m:
                ts, elapsed, cmd = int(m.group(1)), int(m.group(2)), m.group(3)
                t = dt.datetime.fromtimestamp(ts)
            else:
                ts, elapsed, cmd, t = None, None, ln.strip(), None
            if not cmd:
                continue
            tool = _argv0(cmd)
            if tool not in AGENTIC_CLI:
                continue
            if t is None:
                undated_skipped += 1  # do NOT fabricate a timestamp
                continue
            if t < since:
                continue
            if elapsed:  # real run time recorded by the shell
                minutes = min(round(elapsed / 60, 1), APP_ROW_CAP_MIN)
                minutes = max(minutes, CLI_FLOOR_MIN)
            else:  # elapsed 0/absent: shell didn't time it; nominal estimate
                minutes = CLI_FALLBACK_MIN
            out.append(
                {
                    "start": t.isoformat(timespec="minutes"),
                    "name": f"{tool} (CLI)",
                    "kind": "app",
                    "category": "AI / Agentic",
                    "is_agentic": True,
                    "minutes": minutes,
                }
            )
    print(f"  agentic CLI invocations: {len(out)}")
    if undated_skipped:
        warnings.append(
            f"Skipped {undated_skipped} un-timestamped shell entries "
            "(enable zsh EXTENDED_HISTORY / bash HISTTIMEFORMAT to include them)."
        )
    return out


# ------------------------------------------------------------------------ main
def redact(sessions):
    for s in sessions:
        s["name"] = s["category"]  # drop identifying names
    return sessions


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect local macOS activity into JSON.")
    ap.add_argument("--days", type=int, default=14, help="lookback window (default 14)")
    ap.add_argument("--out", default="my_activity_data.json", help="output JSON path")
    ap.add_argument("--no-browser", action="store_true", help="skip browser history")
    ap.add_argument("--no-shell", action="store_true", help="skip shell/CLI history")
    ap.add_argument(
        "--redact", action="store_true", help="store category + time only, drop all app/site names"
    )
    args = ap.parse_args(argv)

    if sys.platform != "darwin":
        print(
            "mac-activity-tracker only collects data on macOS. On this platform you "
            "can still render the sample dashboard:\n"
            "  python3 sample/build_sample_data.py && python3 build_dashboard.py "
            "--data sample/sample_data.json",
            file=sys.stderr,
        )
        return 2

    now = dt.datetime.now()
    since = now - dt.timedelta(days=args.days)
    warnings: list[str] = []
    print(f"Collecting native macOS activity (last {args.days} days)...")

    sessions = collect_app_usage(since, warnings)
    if not args.no_browser:
        sessions += collect_browsers(since, warnings)
    if not args.no_shell:
        sessions += collect_cli(since, warnings)

    sessions.sort(key=lambda s: s["start"])
    if args.redact:
        sessions = redact(sessions)

    out = {
        "generated_at": now.isoformat(timespec="seconds"),
        "window_start": since.date().isoformat(),
        "window_end": now.date().isoformat(),
        "source": "live",
        "estimates": True,  # durations are heuristic, not exact
        "redacted": args.redact,
        "sessions": sessions,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)

    total_h = sum(s["minutes"] for s in sessions) / 60
    print(f"\nWrote {args.out} - {len(sessions)} sessions, ~{total_h:.1f}h (estimated).")
    if warnings:
        print("\nNotes:")
        for w in warnings:
            print("  -", w)
    if not sessions:
        print(
            "\nNo data collected. Most likely fix: give your terminal Full Disk Access, "
            "then re-run.\n  System Settings > Privacy & Security > Full Disk Access."
        )
        return 1
    print(f"\nNext: python3 build_dashboard.py --data {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
