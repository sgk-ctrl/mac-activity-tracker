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


def test_stale_timer_cannot_strip_newer_session(tmp_path):
    # regression: session A's exit trap must remove only A's section. If the
    # user started session B meanwhile, B's block must survive A's cleanup.
    hosts = tmp_path / "hosts"
    original = "127.0.0.1 localhost\n"
    hosts.write_text(original)
    env = {**os.environ, "FOCUS_HOSTS_FILE": str(hosts)}
    sh = os.path.join(REPO, "scripts", "focus.sh")

    subprocess.run(["bash", sh, "on"], env=env, cwd=REPO, capture_output=True)
    text_a = hosts.read_text()
    session_a = [ln for ln in text_a.splitlines() if "session:" in ln][0]

    subprocess.run(["bash", sh, "on"], env=env, cwd=REPO, capture_output=True)
    text_b = hosts.read_text()
    session_b = [ln for ln in text_b.splitlines() if "session:" in ln][0]
    assert session_a != session_b  # different PIDs -> different tags

    # simulate stale session A's trap firing now: strip A's tag specifically
    strip_a = (
        f'HOSTS="{hosts}"; END="# <<< mac-activity-tracker focus mode <<<"; '
        f'awk -v b="{session_a}" -v e="$END" '
        f"'index($0,b)==1{{skip=1}} !skip{{print}} index($0,e)==1{{skip=0}}' "
        f'"$HOSTS" > "$HOSTS.tmp" && cat "$HOSTS.tmp" > "$HOSTS"'
    )
    subprocess.run(["bash", "-c", strip_a], capture_output=True)
    assert "youtube.com" in hosts.read_text()  # B's block still standing

    subprocess.run(["bash", sh, "off"], env=env, cwd=REPO, capture_output=True)
    assert hosts.read_text() == original


def test_blocked_domain_resolves_to_localhost(tmp_path):
    # effectiveness proof: hosts-format lines produced by focus.sh are exactly
    # what the libc resolver consumes. Simulate resolution against the scratch
    # file the same way getaddrinfo consults /etc/hosts (first-match wins).
    hosts = tmp_path / "hosts"
    hosts.write_text("127.0.0.1 localhost\n")
    env = {**os.environ, "FOCUS_HOSTS_FILE": str(hosts)}
    sh = os.path.join(REPO, "scripts", "focus.sh")
    subprocess.run(["bash", sh, "on"], env=env, cwd=REPO, capture_output=True)

    mapping = {}
    for ln in hosts.read_text().splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        parts = ln.split()
        for name in parts[1:]:
            mapping.setdefault(name, parts[0])
    assert mapping.get("youtube.com") == "127.0.0.1"
    assert mapping.get("www.youtube.com") == "127.0.0.1"
    assert mapping.get("localhost") == "127.0.0.1"  # pre-existing entry intact


def test_focus_sh_rejects_garbage_arg():
    sh = os.path.join(REPO, "scripts", "focus.sh")
    r = subprocess.run(["bash", sh, "9000x"], cwd=REPO, capture_output=True, text=True)
    assert r.returncode != 0
