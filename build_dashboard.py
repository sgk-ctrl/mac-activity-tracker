#!/usr/bin/env python3
"""Render a self-contained dashboard HTML from an activity JSON file.

The data is embedded as INERT JSON inside a <script type="application/json">
block and parsed with JSON.parse in the page, so hostnames/app names can never
execute as script. Chart.js is referenced from a locally vendored copy (no CDN),
keeping the dashboard fully offline.
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "templates", "dashboard.html.tmpl")


def escape_for_script(data_json: str) -> str:
    """Neutralize any sequence that could close the <script> tag or start
    markup, so embedded data stays inert regardless of its contents. Also
    escape the JS line/paragraph separators U+2028/U+2029 for safety."""
    return (data_json
            .replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace(" ", "\\u2028")
            .replace(" ", "\\u2029"))


def build(data_path: str, out_path: str, chart_src: str) -> str:
    with open(data_path) as f:
        data = json.load(f)
    with open(TEMPLATE) as f:
        html = f.read()

    data_json = escape_for_script(json.dumps(data, separators=(",", ":")))
    html = html.replace("__CHART_SRC__", chart_src, 1)
    html = html.replace("__DATA__", data_json, 1)

    with open(out_path, "w") as f:
        f.write(html)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the dashboard HTML from activity JSON.")
    ap.add_argument("--data", default="my_activity_data.json", help="input JSON path")
    ap.add_argument("--out", default="dashboard.html", help="output HTML path")
    ap.add_argument("--chart-src", default="vendor/chart.umd.min.js",
                    help="path/URL to Chart.js as seen from the output file "
                         "(default: local vendored copy)")
    args = ap.parse_args(argv)

    if not os.path.exists(args.data):
        raise SystemExit(f"Data file not found: {args.data}\n"
                         "Run 'python3 tracker.py' first, or pass "
                         "--data sample/sample_data.json")

    out = build(args.data, args.out, args.chart_src)
    print(f"Wrote {out} (data: {args.data}, chart: {args.chart_src})")


if __name__ == "__main__":
    main()
