"""Dashboard build + injection-safety tests."""

import json
import re

import build_dashboard


def _write(tmp_path, data):
    p = tmp_path / "data.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_build_produces_html(tmp_path):
    data = {
        "source": "sample",
        "window_start": "2026-01-01",
        "window_end": "2026-01-14",
        "generated_at": "2026-01-14T10:00:00",
        "sessions": [
            {
                "start": "2026-01-01T09:00",
                "name": "VS Code",
                "kind": "app",
                "category": "Coding",
                "is_agentic": False,
                "minutes": 30,
            }
        ],
    }
    out = tmp_path / "dash.html"
    build_dashboard.build(_write(tmp_path, data), str(out), "vendor/chart.umd.min.js")
    html = out.read_text()
    assert '<canvas id="catChart">' in html
    assert "vendor/chart.umd.min.js" in html


def test_script_injection_is_neutralized(tmp_path):
    # A hostile page title / hostname containing a closing script tag must NOT
    # break out of the embedded JSON block.
    payload = "</script><img src=x onerror=alert(1)>"
    data = {
        "source": "live",
        "window_start": "2026-01-01",
        "window_end": "2026-01-14",
        "generated_at": "2026-01-14T10:00:00",
        "sessions": [
            {
                "start": "2026-01-01T09:00",
                "name": payload,
                "kind": "web",
                "category": "Social",
                "is_agentic": False,
                "minutes": 3,
            }
        ],
    }
    out = tmp_path / "dash.html"
    build_dashboard.build(_write(tmp_path, data), str(out), "vendor/chart.umd.min.js")
    html = out.read_text()
    # the literal closing tag from data must not appear un-escaped
    assert "</script><img" not in html
    assert "\\u003c/script" in html or "\\u003c\\/script" in html
    # the inert JSON block still parses back to the original payload
    m = re.search(r'<script id="activity-data" type="application/json">(.*?)</script>', html, re.S)
    assert m, "data script block not found"
    raw = m.group(1).replace("\\u0026", "&").replace("\\u003c", "<").replace("\\u003e", ">")
    parsed = json.loads(raw)
    assert parsed["sessions"][0]["name"] == payload


def test_data_token_collision(tmp_path):
    # user data literally containing __DATA__ must not corrupt the template
    data = {
        "source": "live",
        "window_start": "2026-01-01",
        "window_end": "2026-01-14",
        "generated_at": "2026-01-14T10:00:00",
        "sessions": [
            {
                "start": "2026-01-01T09:00",
                "name": "__DATA__",
                "kind": "app",
                "category": "Other",
                "is_agentic": False,
                "minutes": 1,
            }
        ],
    }
    out = tmp_path / "dash.html"
    build_dashboard.build(_write(tmp_path, data), str(out), "vendor/chart.umd.min.js")
    html = out.read_text()
    assert "__CHART_SRC__" not in html
    # the only "__DATA__" left is the user's value inside the JSON block; it must
    # round-trip cleanly rather than corrupt the template.
    m = re.search(r'<script id="activity-data" type="application/json">(.*?)</script>', html, re.S)
    raw = m.group(1).replace("\\u0026", "&").replace("\\u003c", "<").replace("\\u003e", ">")
    assert json.loads(raw)["sessions"][0]["name"] == "__DATA__"
