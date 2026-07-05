"""Cross-platform unit tests (run on Linux CI via fixtures — no macOS needed)."""
import datetime as dt
import sqlite3
import sys

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
        ": 1719000000:0;claude write tests\n"          # real agentic (dated)
        ": 1719000100:0;git commit -m \"fix cursor bug\"\n"   # must NOT match
        ": 1719000200:0;python codextool.py\n"          # must NOT match
        ": 1719000300:0;sudo apt install ollama-bin\n"  # must NOT match (argv0=apt)
        ": 1719000400:0;cursor .\n"                     # real agentic
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
    conn.execute("CREATE TABLE ZOBJECT (ZSTREAMNAME TEXT, ZVALUESTRING TEXT, "
                 "ZSTARTDATE REAL, ZENDDATE REAL)")
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
        ("/app/usage", "com.google.Chrome", now_cf - 1800, now_cf - 1770),     # 0.5 min
        ("/other/stream", "com.apple.Finder", now_cf - 100, now_cf - 10),      # ignored
        ("/app/usage", "com.anthropic.claude", now_cf - 600, now_cf - 300),    # agentic
    ]
    _make_knowledgec(str(db), rows)
    monkeypatch.setattr(tracker, "HOME", str(tmp_path))
    out = tracker.collect_app_usage(dt.datetime.now() - dt.timedelta(days=1), [])
    names = {s["name"] for s in out}
    assert "VS Code" in names          # display-name mapping applied
    assert any(s["is_agentic"] for s in out if s["name"] == "Claude")
    assert all(s["category"] != "/other/stream" for s in out)


def test_platform_guard_non_darwin(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    rc = tracker.main(["--out", str(tmp_path / "x.json")])
    assert rc == 2
