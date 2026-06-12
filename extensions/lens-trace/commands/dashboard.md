---
description: "Generate a self-contained static HTML dashboard from .specify/trace.log and .specify/drift.log. Writes .specify/dashboard.html."
---

You are the `lens-dashboard` command, part of the `lens-trace` extension.

## Goal

Run the dashboard generator script to produce a static HTML report from the current run logs. No analysis — just invoke the script and report the output path.

## Steps

### 1. Resolve paths

The script lives at `<lens-trace extension dir>/scripts/dashboard.py`.

The default output path is `.specify/dashboard.html`. If `$ARGUMENTS` contains `--output <path>`, pass it through to the script.

### 2. Run the script

```bash
uv run <path-to-extension>/scripts/dashboard.py $ARGUMENTS
```

### 3. Report

Print the path to the generated HTML file. If the script exits non-zero, print the error output and exit.

## Notes

- Requires `.specify/trace.log` to exist (written by the `lens-trace` after_task hook).
- `.specify/drift.log` is optional — dashboard renders trace-only if drift log is absent.
- The generated HTML is fully self-contained (no CDN, no external deps).
- Open in any browser: `open .specify/dashboard.html`

$ARGUMENTS
