"""Cross-platform unit tests (run on Linux CI via fixtures — no macOS needed)."""

import datetime as dt
import sqlite3
import sys

import pytest

import tracker
from tracker import CHROME_EPOCH, MAC_EPOCH, _argv0, cat_for_domain


# --------------------------------------------------------------- epoch math
def test_cfabsolute_epoch():
    # ZSTARTDATE == 0 -> 2001-01-01
    assert MAC_EPOCH + dt.timedelta(seconds=0) == dt.datetime(2001, 1, 1)
    # a known 2025 value ~ 7.8e8 seconds after 2001
    t = MAC_EPOCH + dt.timedelta(seconds=788_000_000)
    assert 2024 <= t.year <= 2026


def test_chrome_epoch():
    # Chrome time is microseconds since 1601-01-01
    micros = 13_350_000_000_000_000
    t = CHROME_EPOCH + dt.timedelta(microseconds=micros)
    assert 2023 <= t.year <= 2027


# --------------------------------------------------------------- domain cats
def test_domain_categories():
    assert cat_for_domain("github.com") == "Coding"
    assert cat_for_domain("claude.ai") == "AI / Agentic"
    assert cat_for_domain("youtube.com") == "Media"
    assert cat_for_domain("some-unknown-site.example") == "Browsing"


# --------------------------------------------------------------- CLI matcher
def test_argv0_strips_prefixes():
    assert _argv0("claude --help") == "claude"
    assert _argv0("sudo ollama run llama3") == "ollama"
    assert _argv0("env FOO=bar codex do") == "codex"


def test_agentic_cli_no_false_positives(tmp_path, monkeypatch):
    hist = (
        ": 1719000000:0;claude write tests\n"  # real agentic (dated)
        ': 1719000100:0;git commit -m "fix cursor bug"\n'  # must NOT match
        ": 1719000200:0;python codextool.py\n"  # must NOT match
        ": 1719000300:0;sudo apt install ollama-bin\n"  # must NOT match (argv0=apt)
        ": 1719000400:0;cursor .\n"  # real agentic
    )
    (tmp_path / ".zsh_history").write_text(hist)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    since = dt.datetime(2024, 1, 1)
    out = tracker.collect_cli(since, [])
    names = sorted(s["name"] for s in out)
    assert names == ["claude (CLI)", "cursor (CLI)"]


def test_undated_bash_history_not_fabricated(tmp_path, monkeypatch):
    # bash history usually has no timestamps -> entries must be skipped, not stamped NOW
    (tmp_path / ".bash_history").write_text("claude do something\ncodex go\n")
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    warnings = []
    out = tracker.collect_cli(dt.datetime(2024, 1, 1), warnings)
    assert out == []
    assert any("un-timestamped" in w for w in warnings)


# --------------------------------------------------------------- knowledgeC
def _make_knowledgec(path, rows):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE ZOBJECT (ZSTREAMNAME TEXT, ZVALUESTRING TEXT, ZSTARTDATE REAL, ZENDDATE REAL)"
    )
    conn.executemany("INSERT INTO ZOBJECT VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()


def test_collect_app_usage_fixture(tmp_path, monkeypatch):
    dbdir = tmp_path / "Library/Application Support/Knowledge"
    dbdir.mkdir(parents=True)
    db = dbdir / "knowledgeC.db"
    now_cf = (dt.datetime.now() - MAC_EPOCH).total_seconds()
    rows = [
        ("/app/usage", "com.microsoft.VSCode", now_cf - 3600, now_cf - 1800),  # 30 min
        ("/app/usage", "com.google.Chrome", now_cf - 1800, now_cf - 1770),  # 0.5 min
        ("/other/stream", "com.apple.Finder", now_cf - 100, now_cf - 10),  # ignored
        ("/app/usage", "com.anthropic.claude", now_cf - 600, now_cf - 300),  # agentic
    ]
    _make_knowledgec(str(db), rows)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    out = tracker.collect_app_usage(dt.datetime.now() - dt.timedelta(days=1), [])
    names = {s["name"] for s in out}
    assert "VS Code" in names  # display-name mapping applied
    assert any(s["is_agentic"] for s in out if s["name"] == "Claude")
    assert all(s["category"] != "/other/stream" for s in out)


def test_platform_guard_non_darwin(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    rc = tracker.main(["--out", str(tmp_path / "x.json")])
    assert rc == 2


# --------------------------------------------------------- overlap / day caps
def _cf(t):
    return (t - MAC_EPOCH).total_seconds()


def test_overlapping_rows_do_not_exceed_wall_clock(tmp_path, monkeypatch):
    # two apps "focused" over the SAME 4h window must yield 4h total, not 8h
    dbdir = tmp_path / "Library/Application Support/Knowledge"
    dbdir.mkdir(parents=True)
    day = dt.datetime(2026, 6, 1, 10, 0)
    rows = [
        ("/app/usage", "com.microsoft.VSCode", _cf(day), _cf(day + dt.timedelta(hours=4))),
        ("/app/usage", "com.google.Chrome", _cf(day), _cf(day + dt.timedelta(hours=4))),
    ]
    _make_knowledgec(str(dbdir / "knowledgeC.db"), rows)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    out = tracker.collect_app_usage(dt.datetime(2026, 5, 31), [])
    total_min = sum(s["minutes"] for s in out)
    assert total_min <= 4 * 60 + 1  # wall-clock, not the 8h naive sum


def test_contained_interval_attribution():
    # A runs 10:00-11:00; B interrupts 10:10-10:20. A must get 50 min, B 10.
    a = (dt.datetime(2026, 6, 1, 10, 0), dt.datetime(2026, 6, 1, 11, 0), "A")
    b = (dt.datetime(2026, 6, 1, 10, 10), dt.datetime(2026, 6, 1, 10, 20), "B")
    segs = tracker._deoverlap([a, b])
    per_key = {}
    for s, e, k in segs:
        per_key[k] = per_key.get(k, 0) + (e - s).total_seconds() / 60
    assert per_key == {"A": 50, "B": 10}


def test_daily_totals_capped_at_24h(tmp_path, monkeypatch):
    # pathological DB: 30 overlapping 4h rows in one day (120h naive) plus a
    # row crossing midnight. Per-day totals must stay <= 24h.
    dbdir = tmp_path / "Library/Application Support/Knowledge"
    dbdir.mkdir(parents=True)
    day = dt.datetime(2026, 6, 1, 0, 0)
    rows = [
        (
            "/app/usage",
            f"com.example.app{i}",
            _cf(day + dt.timedelta(minutes=7 * i)),
            _cf(day + dt.timedelta(minutes=7 * i) + dt.timedelta(hours=4)),
        )
        for i in range(30)
    ]
    rows.append(  # crosses midnight into 06-02
        (
            "/app/usage",
            "com.example.night",
            _cf(day + dt.timedelta(hours=23)),
            _cf(day + dt.timedelta(hours=26)),
        )
    )
    _make_knowledgec(str(dbdir / "knowledgeC.db"), rows)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    out = tracker.collect_app_usage(dt.datetime(2026, 5, 31), [])
    per_day = {}
    for s in out:
        d = s["start"][:10]
        per_day[d] = per_day.get(d, 0) + s["minutes"]
    assert per_day  # something was collected
    for d, mins in per_day.items():
        assert mins <= 24 * 60, f"{d} exceeds wall-clock: {mins} min"


# ------------------------------------------------------- merged web timeline
def _make_chrome_history(path, visit_times_hosts):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT)")
    conn.execute("CREATE TABLE visits (url INTEGER, visit_time INTEGER)")
    for i, (host, t) in enumerate(visit_times_hosts, start=1):
        micros = int((t - CHROME_EPOCH).total_seconds() * 1_000_000)
        conn.execute("INSERT INTO urls VALUES (?, ?)", (i, f"https://{host}/page"))
        conn.execute("INSERT INTO visits VALUES (?, ?)", (i, micros))
    conn.commit()
    conn.close()


def test_interleaved_browsers_share_one_timeline(tmp_path, monkeypatch):
    # visits alternate between two Chrome profiles every 2 min. Sessionized
    # per-profile the gaps look like 4 min each (double-counting); merged they
    # are 2 min. Total dwell must reflect the MERGED timeline.
    base = dt.datetime(2026, 6, 1, 10, 0)
    profile_a = [("a.com", base + dt.timedelta(minutes=m)) for m in (0, 4, 8)]
    profile_b = [("b.com", base + dt.timedelta(minutes=m)) for m in (2, 6, 10)]
    for prof, visits in (("Default", profile_a), ("Profile 1", profile_b)):
        d = tmp_path / f"Library/Application Support/Google/Chrome/{prof}"
        d.mkdir(parents=True)
        _make_chrome_history(str(d / "History"), visits)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    out = tracker.collect_browsers(dt.datetime(2026, 5, 31), [])
    assert len(out) == 6
    # 5 gaps of 2 min + 1 session-final floor credit = 11 min total
    assert sum(s["minutes"] for s in out) == 5 * 2 + tracker.WEB_FLOOR_MIN


# ------------------------------------------------------------- read_only_db
def test_read_only_db_propagates_caller_errors(tmp_path):
    # a query error inside the with-block must propagate as-is — the context
    # manager must NOT treat it as a connection failure and yield again
    # (regression: RuntimeError "generator didn't stop after throw()")
    db = tmp_path / "x.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE t (a INTEGER)")
    conn.commit()
    conn.close()
    with pytest.raises(sqlite3.Error):
        with tracker.read_only_db(str(db)) as ro:
            ro.execute("SELECT missing_col FROM no_such_table")


# ----------------------------------------------------------- CLI durations
def test_cli_uses_real_elapsed_duration(tmp_path, monkeypatch):
    hist = (
        ": 1719000000:600;claude implement feature\n"  # 10 min real duration
        ": 1719010000:0;codex quick\n"  # no elapsed recorded -> fallback
        ": 1719020000:999999;claude marathon\n"  # absurd -> capped
    )
    (tmp_path / ".zsh_history").write_text(hist)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    out = tracker.collect_cli(dt.datetime(2024, 1, 1), [])
    by_start = {s["start"]: s["minutes"] for s in out}
    mins = sorted(by_start.values())
    assert 10 in mins  # real 600s -> 10 min
    assert tracker.CLI_FALLBACK_MIN in mins  # elapsed 0 -> nominal
    assert max(mins) == tracker.APP_ROW_CAP_MIN  # capped, not 16666 min
