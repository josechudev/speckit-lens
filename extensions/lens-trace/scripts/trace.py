#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
lens-trace: Emits a structured trace report after each speckit implement task.

Invoked as an after_task hook. Reads .specify/tasks.md and git diff to produce
a per-task change summary. Never writes files. Never blocks the implement loop.

Exit codes:
  0 — success (including undeclared-file warnings)
  1 — internal error (missing dependency, unreadable git state)
"""

import os
import re
import subprocess
import sys
from pathlib import Path

BORDER = "━" * 60
THIN = "─" * 60
DONE = "━━ done " + "━" * 52


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_tasks_md(path: Path) -> dict[str, dict]:
    """Return {task_id: {title, files}} from .specify/tasks.md."""
    if not path.exists():
        return {}

    content = path.read_text()
    tasks: dict[str, dict] = {}

    # Match blocks that start with ## T-XX or ## T-XX:
    task_pattern = re.compile(
        r"##\s+(T-\d+)[:\s]+(.+?)(?=\n##\s+T-|\Z)", re.DOTALL
    )
    for m in task_pattern.finditer(content):
        task_id = m.group(1).strip()
        block = m.group(2)
        title = block.split("\n")[0].strip()

        files: list[str] = []
        for line in block.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- ") and ("/" in stripped or "." in stripped):
                files.append(stripped.lstrip("- ").strip("`").strip())

        tasks[task_id] = {"title": title, "files": files}

    return tasks


def get_git_changes() -> list[dict]:
    """Return list of {file, added, removed, binary} from git diff --numstat HEAD."""
    result = subprocess.run(
        ["git", "diff", "--numstat", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    changes: list[dict] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            added, removed, filepath = parts
            changes.append({
                "file": filepath,
                "added": int(added) if added != "-" else 0,
                "removed": int(removed) if removed != "-" else 0,
                "binary": added == "-",
            })
    return changes


def get_current_task_id() -> str | None:
    """Read task ID from speckit hook env vars."""
    return (
        os.environ.get("SPECKIT_TASK_ID")
        or os.environ.get("SPECKIT_CURRENT_TASK")
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_trace(
    task_id: str | None,
    task: dict | None,
    changes: list[dict],
) -> None:
    declared_files: list[str] = task["files"] if task else []
    declared_set = set(declared_files)

    print(BORDER)

    if task_id and task:
        print(f"Task  : {task_id} — {task['title']}")
        if declared_files:
            print(f"Scope : {', '.join(declared_files)}")
    elif task_id:
        print(f"Task  : {task_id}  (no metadata found)")
    else:
        print("lens-trace: could not identify current task")

    print(THIN)

    if not changes:
        print("No file changes detected.")
    else:
        print("Changed:")
        changed_set: set[str] = set()
        for c in changes:
            changed_set.add(c["file"])
            tag = "  [undeclared]" if declared_set and c["file"] not in declared_set else ""
            if c["binary"]:
                print(f"  {c['file']}  (binary){tag}")
            else:
                print(f"  {c['file']}  +{c['added']} -{c['removed']}{tag}")

        for f in declared_files:
            if f not in changed_set:
                print(f"  {f}  [untouched]")

    print(DONE)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main() -> None:
    tasks_path = Path(".specify/tasks.md")
    tasks = parse_tasks_md(tasks_path)

    if not tasks_path.exists():
        print("lens-trace: warning — .specify/tasks.md not found", file=sys.stderr)

    task_id = get_current_task_id()
    task = tasks.get(task_id) if task_id else None
    changes = get_git_changes()

    print_trace(task_id, task, changes)


if __name__ == "__main__":
    main()
