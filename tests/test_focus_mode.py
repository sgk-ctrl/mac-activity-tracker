"""Focus-mode tests: blocklist generation + the hosts add/remove round trip."""

import json
import os
import subprocess
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
)
import focus_blocklist

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _data(tmp_path, sessions):
    p = tmp_path / "data.json"
    p.write_text(json.dumps({"sessions": sessions}))
    return str(p)


def test_blocklist_includes_personal_distraction_domains(tmp_path):
    path = _data(
        tmp_path,
        [
            {"name": "9gag.com", "kind": "web", "category": "Social"},
            {"name": "github.com", "kind": "web", "category": "Coding"},  # not distraction
            {"name": "Spotify", "kind": "app", "category": "Media"},  # app, not web
        ],
    )
    got = focus_blocklist.blocklist(path)
    assert "9gag.com" in got  # personal distraction picked up
    assert "github.com" not in got  # focus site never blocked
    assert "Spotify" not in got  # apps aren't hosts entries
    assert "youtube.com" in got  # fallback usual suspects always present


def test_blocklist_redacted_data_falls_back(tmp_path):
    # --redact stores category names instead of domains; no dot -> filtered out
    path = _data(tmp_path, [{"name": "Social", "kind": "web", "category": "Social"}])
    got = focus_blocklist.blocklist(path)
    assert "Social" not in got
    assert got == focus_blocklist.blocklist(str(tmp_path / "missing.json"))  # pure fallback


def test_focus_sh_round_trip_preserves_hosts(tmp_path):
    hosts = tmp_path / "hosts"
    original = "127.0.0.1 localhost\n255.255.255.255 broadcasthost\n"
    hosts.write_text(original)
    env = {**os.environ, "FOCUS_HOSTS_FILE": str(hosts)}
    sh = os.path.join(REPO, "scripts", "focus.sh")

    on = subprocess.run(["bash", sh, "on"], env=env, cwd=REPO, capture_output=True, text=True)
    assert on.returncode == 0, on.stderr
    blocked = hosts.read_text()
    assert "youtube.com" in blocked and "focus mode >>>" in blocked
    assert blocked.startswith(original)  # existing entries untouched

    # 'on' twice must not stack two sections
    subprocess.run(["bash", sh, "on"], env=env, cwd=REPO, capture_output=True, text=True)
    assert hosts.read_text().count("focus mode >>>") == 1

    off = subprocess.run(["bash", sh, "off"], env=env, cwd=REPO, capture_output=True, text=True)
    assert off.returncode == 0, off.stderr
    assert hosts.read_text() == original  # byte-identical restore


def test_focus_sh_rejects_garbage_arg():
    sh = os.path.join(REPO, "scripts", "focus.sh")
    r = subprocess.run(["bash", sh, "9000x"], cwd=REPO, capture_output=True, text=True)
    assert r.returncode != 0
