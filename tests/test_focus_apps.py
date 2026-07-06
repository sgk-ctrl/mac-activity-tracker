"""Focus-session app-control tests (pure decision logic; runs on any OS)."""

import os
import subprocess
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
)
import focus_apps

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_quits_only_non_allowed_non_protected():
    running = ["Xcode", "Safari", "Slack", "Spotify", "Finder", "Terminal"]
    allowed = ["Xcode", "Safari"]
    got = focus_apps.to_quit(running, allowed)
    assert got == ["Slack", "Spotify"]  # allowed + protected all spared


def test_protected_never_quit_even_if_not_allowed():
    running = ["Finder", "Terminal", "iTerm2", "Activity Review", "Dock", "Control Center"]
    assert focus_apps.to_quit(running, []) == []  # nothing critical gets quit


def test_allowlist_is_case_insensitive_and_trimmed():
    running = ["Google Chrome", "Notes"]
    allowed = ["  google chrome  "]
    assert focus_apps.to_quit(running, allowed) == ["Notes"]


def test_empty_allowlist_quits_all_non_protected():
    running = ["Photos", "Music", "Finder"]
    assert focus_apps.to_quit(running, []) == ["Photos", "Music"]


def test_deduplicates_running_names():
    assert focus_apps.to_quit(["Slack", "Slack"], []) == ["Slack"]


def test_cli_reads_allowlist_file_and_stdin(tmp_path):
    allow = tmp_path / "allow.txt"
    allow.write_text("Xcode\nSafari\n")
    script = os.path.join(REPO, "scripts", "focus_apps.py")
    r = subprocess.run(
        [sys.executable, script, str(allow)],
        input="Xcode\nSafari\nSlack\nFinder\n",
        capture_output=True,
        text=True,
    )
    assert r.stdout.split() == ["Slack"]


def test_focus_session_dry_run_reports_without_quitting(tmp_path, monkeypatch):
    # start in DRY_RUN with a fake System Events feed: must report intended
    # quits and NOT create the sentinel / guard (nothing actually happens)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    # stub osascript to emit a fixed visible-app list
    osa = fake_bin / "osascript"
    osa.write_text('#!/bin/bash\necho "Xcode, Slack, Finder, Notes"\n')
    osa.chmod(0o755)
    env = {
        **os.environ,
        "DRY_RUN": "1",
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }
    sh = os.path.join(REPO, "scripts", "focus_session.sh")
    r = subprocess.run(
        ["bash", sh, "start", "Xcode", "60", "ship it"],
        env=env,
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "would quit: Slack" in r.stdout
    assert "would quit: Notes" in r.stdout
    assert "would quit: Finder" not in r.stdout  # protected
    assert "would quit: Xcode" not in r.stdout  # allowed
    assert not os.path.exists(os.path.join(REPO, ".focus", "active"))  # dry run: no session
