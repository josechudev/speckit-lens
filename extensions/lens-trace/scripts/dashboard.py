#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
lens-trace dashboard generator.

Reads .specify/trace.log and (optionally) .specify/drift.log.
Writes a self-contained static HTML report.

Usage:
    uv run scripts/dashboard.py [--output PATH] [--specify-dir DIR]
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from html import escape
from collections import defaultdict


# ── Log parsers ──────────────────────────────────────────────────────────────

RUN_HEADER = re.compile(r"^\[run:\s*(.+?)\]$")
TASK_HEADER = re.compile(r"^Task\s*:\s*(.+?)\s*—\s*(.+)$")
SCORE_LINE  = re.compile(r"^Score\s*:\s*(\d+)/(\d+)")
VIOLATION   = re.compile(r"^\s*\[(MISSING|PARTIAL|VIOLATED|OK)\]\s*(spec\.md:\d+)?\s*[—-]?\s*(.*)$")
CHANGE_LINE = re.compile(r"^\s*(?:\(created\))?\s*(\S+)\s*(?:\+(\d+)\s*-(\d+))?")
UNDECLARED  = re.compile(r"\[undeclared\]")
UNTOUCHED   = re.compile(r"\[untouched\]")


def parse_trace_log(path: Path) -> list[dict]:
    """Return list of runs. Each run: {timestamp, tasks: [{id, title, files, changes}]}"""
    runs = []
    current_run = None
    current_task = None
    in_changed = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        m = RUN_HEADER.match(line)
        if m:
            current_run = {"timestamp": m.group(1), "tasks": []}
            runs.append(current_run)
            current_task = None
            in_changed = False
            continue

        if current_run is None:
            # Lines before first run header — create implicit run
            current_run = {"timestamp": "unknown", "tasks": []}
            runs.append(current_run)

        m = TASK_HEADER.match(line)
        if m:
            current_task = {
                "id": m.group(1).strip(),
                "title": m.group(2).strip(),
                "declared_files": [],
                "changes": [],          # {file, added, removed, tag}
                "no_changes": False,
            }
            current_run["tasks"].append(current_task)
            in_changed = False
            continue

        if current_task is None:
            continue

        if line.startswith("Files :") or line.startswith("Files:"):
            files_str = line.split(":", 1)[1].strip()
            current_task["declared_files"] = [f.strip() for f in files_str.split(",") if f.strip()]
            continue

        if "Changed:" in line:
            in_changed = True
            continue

        if "No file changes detected" in line:
            current_task["no_changes"] = True
            in_changed = False
            continue

        if in_changed and line and not line.startswith("━") and not line.startswith("─"):
            tag = None
            if "[undeclared]" in line:
                tag = "undeclared"
            elif "[untouched]" in line:
                tag = "untouched"
            created = "(created)" in line
            # Extract filename and deltas
            clean = line.replace("[undeclared]", "").replace("[untouched]", "").replace("(created)", "").strip()
            parts = clean.split()
            fname = parts[0] if parts else ""
            added = removed = 0
            for p in parts[1:]:
                if p.startswith("+"):
                    try: added = int(p[1:])
                    except ValueError: pass
                elif p.startswith("-"):
                    try: removed = int(p[1:])
                    except ValueError: pass
            if fname:
                current_task["changes"].append({
                    "file": fname,
                    "added": added,
                    "removed": removed,
                    "tag": tag,
                    "created": created,
                })

    return runs


def parse_drift_log(path: Path) -> dict[tuple, dict]:
    """Return dict keyed by (run_timestamp, task_id) → {score_ok, score_total, violations}"""
    result = {}
    current_run_ts = "unknown"
    current_entry = None
    current_key = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        m = RUN_HEADER.match(line)
        if m:
            current_run_ts = m.group(1)
            current_entry = None
            current_key = None
            continue

        m = TASK_HEADER.match(line)
        if m:
            task_id = m.group(1).strip()
            current_key = (current_run_ts, task_id)
            current_entry = {"score_ok": None, "score_total": None, "violations": []}
            result[current_key] = current_entry
            continue

        if current_entry is None:
            continue

        m = SCORE_LINE.match(line)
        if m:
            current_entry["score_ok"] = int(m.group(1))
            current_entry["score_total"] = int(m.group(2))
            continue

        m = VIOLATION.match(line)
        if m and m.group(1) in ("MISSING", "PARTIAL", "VIOLATED"):
            current_entry["violations"].append({
                "status": m.group(1),
                "ref": m.group(2) or "",
                "text": m.group(3).strip(),
            })

    return result


# ── HTML rendering ────────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: ui-monospace, 'Cascadia Code', Menlo, monospace;
       background: #0d1117; color: #c9d1d9; font-size: 13px; line-height: 1.5; }
header { padding: 20px 28px 12px; border-bottom: 1px solid #21262d; }
header h1 { font-size: 18px; color: #f0f6fc; }
header .sub { color: #8b949e; font-size: 11px; margin-top: 2px; }
.runs { padding: 16px 28px; }
.run { margin-bottom: 24px; }
.run-header { font-size: 12px; color: #8b949e; margin-bottom: 8px;
              padding: 6px 10px; background: #161b22;
              border: 1px solid #21262d; border-radius: 6px; }
.run-header strong { color: #c9d1d9; }
table { width: 100%; border-collapse: collapse; border: 1px solid #21262d;
        border-radius: 6px; overflow: hidden; }
th { background: #161b22; color: #8b949e; font-size: 11px; font-weight: 600;
     padding: 8px 12px; text-align: left; border-bottom: 1px solid #21262d; }
td { padding: 8px 12px; border-bottom: 1px solid #21262d; vertical-align: top; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #161b22; }
.task-id { color: #58a6ff; white-space: nowrap; }
.task-title { color: #e6edf3; }
.score { white-space: nowrap; }
.score-bar { display: inline-block; width: 60px; height: 8px;
             background: #21262d; border-radius: 4px; vertical-align: middle;
             margin-right: 6px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 4px; }
.green  { background: #238636; }
.yellow { background: #9e6a03; }
.red    { background: #da3633; }
.score-label { font-size: 11px; }
.changes { font-size: 11px; color: #8b949e; }
.change { margin-bottom: 2px; }
.added { color: #3fb950; }
.removed { color: #f85149; }
.tag-undeclared { color: #f78166; font-size: 10px; }
.tag-untouched  { color: #8b949e; font-size: 10px; }
.tag-created    { color: #58a6ff; font-size: 10px; }
.no-changes     { color: #484f58; font-style: italic; }
.violations { font-size: 11px; margin-top: 4px; }
.v-missing  { color: #f85149; }
.v-partial  { color: #d29922; }
.v-violated { color: #f78166; }
.summary-bar { display: flex; gap: 20px; padding: 12px 28px;
               border-bottom: 1px solid #21262d; flex-wrap: wrap; }
.stat { background: #161b22; border: 1px solid #21262d; border-radius: 6px;
        padding: 8px 14px; }
.stat-val { font-size: 20px; font-weight: 700; color: #f0f6fc; }
.stat-lbl { font-size: 10px; color: #8b949e; margin-top: 1px; }
.no-log { color: #484f58; font-style: italic; padding: 20px 28px; }
"""

def score_color(ok, total):
    if total == 0: return "green"
    pct = ok / total
    if pct >= 0.85: return "green"
    if pct >= 0.5:  return "yellow"
    return "red"


def render_changes(changes: list, no_changes: bool) -> str:
    if no_changes:
        return '<span class="no-changes">no file changes detected</span>'
    if not changes:
        return '<span class="no-changes">—</span>'
    parts = []
    for c in changes:
        tag_html = ""
        if c["tag"] == "undeclared":
            tag_html = ' <span class="tag-undeclared">[undeclared]</span>'
        elif c["tag"] == "untouched":
            tag_html = ' <span class="tag-untouched">[untouched]</span>'
        if c["created"]:
            tag_html += ' <span class="tag-created">[created]</span>'
        delta = ""
        if c["added"] or c["removed"]:
            delta = f' <span class="added">+{c["added"]}</span> <span class="removed">-{c["removed"]}</span>'
        parts.append(f'<div class="change">{escape(c["file"])}{delta}{tag_html}</div>')
    return "\n".join(parts)


def render_score(entry: dict | None) -> str:
    if entry is None:
        return '<span class="no-changes">—</span>'
    ok = entry["score_ok"]
    total = entry["score_total"]
    if ok is None:
        return '<span class="no-changes">—</span>'
    pct = (ok / total) if total else 1.0
    color = score_color(ok, total)
    bar = f'<span class="score-bar"><span class="score-fill {color}" style="width:{int(pct*100)}%"></span></span>'
    label = f'<span class="score-label">{ok}/{total}</span>'
    viols = entry.get("violations", [])
    viol_html = ""
    if viols:
        items = []
        for v in viols[:5]:
            cls = f"v-{v['status'].lower()}"
            ref = f' <span style="color:#484f58">{escape(v["ref"])}</span>' if v["ref"] else ""
            items.append(f'<div class="{cls}">[{v["status"]}]{ref} {escape(v["text"][:80])}</div>')
        if len(viols) > 5:
            items.append(f'<div style="color:#484f58">…+{len(viols)-5} more</div>')
        viol_html = f'<div class="violations">{"".join(items)}</div>'
    return f'<span class="score">{bar}{label}</span>{viol_html}'


def render_run(run: dict, drift: dict, run_ts: str) -> str:
    rows = []
    for task in run["tasks"]:
        key = (run_ts, task["id"])
        drift_entry = drift.get(key)
        score_html = render_score(drift_entry)
        changes_html = render_changes(task["changes"], task["no_changes"])
        rows.append(f"""
        <tr>
          <td class="task-id">{escape(task['id'])}</td>
          <td class="task-title">{escape(task['title'])}</td>
          <td class="changes">{changes_html}</td>
          <td>{score_html}</td>
        </tr>""")

    if not rows:
        rows.append('<tr><td colspan="4" class="no-changes" style="padding:12px">No tasks recorded.</td></tr>')

    task_count = len(run["tasks"])
    ts_display = escape(run_ts)
    return f"""
    <div class="run">
      <div class="run-header">
        <strong>Run:</strong> {ts_display} &nbsp;·&nbsp; {task_count} task{'s' if task_count != 1 else ''}
      </div>
      <table>
        <thead>
          <tr>
            <th style="width:80px">Task</th>
            <th>Title</th>
            <th>File changes</th>
            <th style="width:180px">Drift score</th>
          </tr>
        </thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>"""


def render_summary(runs: list, drift: dict) -> str:
    total_tasks = sum(len(r["tasks"]) for r in runs)
    total_runs = len(runs)
    all_scores = [(v["score_ok"], v["score_total"]) for v in drift.values()
                  if v["score_ok"] is not None and v["score_total"]]
    avg_pct = (sum(ok/tot for ok, tot in all_scores) / len(all_scores) * 100) if all_scores else None
    total_violations = sum(len(v["violations"]) for v in drift.values())

    avg_html = f"{avg_pct:.0f}%" if avg_pct is not None else "—"
    avg_color = ""
    if avg_pct is not None:
        avg_color = f" color:{'#3fb950' if avg_pct >= 85 else '#d29922' if avg_pct >= 50 else '#f85149'}"

    return f"""
    <div class="summary-bar">
      <div class="stat">
        <div class="stat-val">{total_runs}</div>
        <div class="stat-lbl">implement runs</div>
      </div>
      <div class="stat">
        <div class="stat-val">{total_tasks}</div>
        <div class="stat-lbl">tasks traced</div>
      </div>
      <div class="stat">
        <div class="stat-val" style="{avg_color}">{avg_html}</div>
        <div class="stat-lbl">avg drift score</div>
      </div>
      <div class="stat">
        <div class="stat-val" style="{'color:#f85149' if total_violations else ''}">{total_violations}</div>
        <div class="stat-lbl">total violations</div>
      </div>
    </div>"""


def render_html(trace_runs: list, drift: dict, generated_at: str) -> str:
    if not trace_runs:
        body = '<p class="no-log">No trace.log found or log is empty. Run an implement session with lens-trace active.</p>'
    else:
        summary = render_summary(trace_runs, drift)
        run_sections = []
        for run in reversed(trace_runs):  # newest first
            run_sections.append(render_run(run, drift, run["timestamp"]))
        body = summary + '<div class="runs">' + "".join(run_sections) + "</div>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>lens-trace dashboard</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <h1>lens-trace dashboard</h1>
    <div class="sub">speckit-lens · generated {escape(generated_at)}</div>
  </header>
  {body}
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate lens-trace static HTML dashboard.")
    parser.add_argument("--output", default=".specify/dashboard.html",
                        help="Output HTML path (default: .specify/dashboard.html)")
    parser.add_argument("--specify-dir", default=".specify",
                        help="Path to .specify directory (default: .specify)")
    args = parser.parse_args()

    specify = Path(args.specify_dir)
    trace_log = specify / "trace.log"
    drift_log = specify / "drift.log"
    out_path = Path(args.output)

    # Parse logs
    trace_runs: list[dict] = []
    if trace_log.exists():
        try:
            trace_runs = parse_trace_log(trace_log)
        except Exception as e:
            print(f"lens-dashboard: failed to parse trace.log: {e}", file=sys.stderr)

    drift: dict = {}
    if drift_log.exists():
        try:
            drift = parse_drift_log(drift_log)
        except Exception as e:
            print(f"lens-dashboard: failed to parse drift.log: {e}", file=sys.stderr)

    if not trace_runs and not drift:
        print("lens-dashboard: no log data found. Run an implement session with lens-trace (and optionally lens-drift) active.", file=sys.stderr)

    # Generate HTML
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = render_html(trace_runs, drift, generated_at)

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"lens-trace dashboard → {out_path}")


if __name__ == "__main__":
    main()
