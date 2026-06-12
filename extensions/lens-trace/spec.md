# Spec: lens-trace

## EARS Reference

EARS (Easy Approach to Requirements Syntax) — Alistair Mavin, Rolls-Royce. Standard adopted by [spec-kit#1356](https://github.com/github/spec-kit/issues/1356) and Kiro IDE.

| Pattern | Template |
|---------|----------|
| Ubiquitous | The `<system>` SHALL `<response>`. |
| Event-driven | WHEN `<trigger>`, the `<system>` SHALL `<response>`. |
| State-driven | WHILE `<state>`, the `<system>` SHALL `<response>`. |
| Unwanted behavior | IF `<condition>`, THEN the `<system>` SHALL `<response>`. |
| Optional feature | WHERE `<feature enabled>`, the `<system>` SHALL `<response>`. |
| Compound | WHEN `<trigger>`, WHILE `<state>`, the `<system>` SHALL `<response>`. |

---

## Problem

During a speckit `implement` run, engineers have no visibility into execution. They see file changes after the fact but nothing during: which task is active, what files it intends to touch, or whether it completed cleanly. Debugging a failed implement run requires archaeology.

## Role in the suite

lens-trace is the observability layer. Runs as `after_task` hook. Emits structured output after each task completes. No side effects on the implement run.

## Inputs

- `.specify/tasks.md` — task ID, title, declared file scope
- `.specify/plan.md` — optional; cross-reference intended vs. actual file scope
- Git working tree diff — actual file changes

## Outputs

- Stdout trace block after each task (always)
- `.specify/trace.log` — persistent append log across all tasks in an implement run
- `.specify/dashboard.html` — static HTML report generated on demand via `/speckit.lens.dashboard`

---

## Requirements

### Stdout trace block

**R-LT-01:** WHEN an `after_task` hook fires, `lens-trace` SHALL print a trace block delimited with `━` border characters, visually distinct from speckit's own output.

**R-LT-02:** WHEN an `after_task` hook fires, `lens-trace` SHALL include the task ID and task title in the trace block header.

**R-LT-03:** WHEN an `after_task` hook fires, `lens-trace` SHALL list all files declared in the task's scope (sourced from `tasks.md`).

**R-LT-04:** WHEN an `after_task` hook fires, `lens-trace` SHALL list all files changed in the git working tree diff, each with line delta in the form `+N -N`.

**R-LT-05:** WHEN a changed file is absent from the task's declared scope, `lens-trace` SHALL label it `[undeclared]`.

**R-LT-06:** WHEN a declared file is absent from the git diff output, `lens-trace` SHALL label it `[untouched]`.

**R-LT-07:** IF git diff produces no output after a task completes, THEN `lens-trace` SHALL print "No file changes detected" and SHALL NOT print an empty table.

**R-LT-08:** IF `.specify/tasks.md` is missing or the current task cannot be identified from hook context, THEN `lens-trace` SHALL print `lens-trace: could not identify current task`, and SHALL still print the git diff summary without task metadata.

### Persistent trace log

**R-LT-09:** WHEN an `after_task` hook fires, `lens-trace` SHALL append the full trace block for that task to `.specify/trace.log`.

**R-LT-10:** IF `.specify/trace.log` does not exist when the first `after_task` hook fires in an implement run, THEN `lens-trace` SHALL create it.

**R-LT-11:** WHEN the first task of a new implement run is traced, `lens-trace` SHALL prepend a run separator in the format `[run: <ISO-8601 timestamp>]` to the new log entries.

**R-LT-12:** WHILE appending to `.specify/trace.log`, `lens-trace` SHALL NOT truncate or modify any prior log entries.

### Behavioral constraints

**R-LT-13:** `lens-trace` SHALL NOT modify any project source files.

**R-LT-14:** `lens-trace` SHALL NOT modify `.specify/spec.md`, `.specify/plan.md`, or `.specify/tasks.md`.

**R-LT-15:** `lens-trace` SHALL NOT block, pause, or alter the implement loop under any condition.

**R-LT-16:** `lens-trace` SHALL complete each trace operation in under 2 seconds.

**R-LT-17:** WHILE both `lens-trace` and `lens-drift` are active as `after_task` hooks, `lens-trace` SHALL execute before `lens-drift` (lower `priority` value in `extension.yml`).

---

## Integration

- `lens-drift` runs in same `after_task` slot; lens-trace runs first
- `.specify/trace.log` is a human artifact; no other extension reads it
- Undeclared file flags are informational only — lens-drift independently scores spec adherence

## Dashboard (`/speckit.lens.dashboard`)

Standalone command — not a hook. Reads `.specify/trace.log` and `.specify/drift.log` (if present) and writes `.specify/dashboard.html`.

Script: `scripts/dashboard.py` (uv inline, stdlib-only, no deps).

**Dashboard sections:**
- Summary bar: run count, task count, average drift score, total violations
- Per-run task table: task ID, title, file changes (with `[undeclared]`/`[untouched]` tags), drift score bar + violations
- Newest run shown first
- Fully self-contained HTML — no CDN, no server

**Usage:**
```bash
# Via speckit command
/speckit.lens.dashboard

# Directly
uv run extensions/lens-trace/scripts/dashboard.py
uv run extensions/lens-trace/scripts/dashboard.py --output reports/run-01.html
```

### Dashboard requirements

**R-LT-D01:** WHEN `/speckit.lens.dashboard` runs, `lens-trace` SHALL invoke `scripts/dashboard.py` and SHALL print the output path on success.

**R-LT-D02:** WHEN generating the dashboard, the script SHALL read `.specify/trace.log` as the primary data source.

**R-LT-D03:** IF `.specify/drift.log` exists, THEN the script SHALL merge drift scores and violations into the task rows.

**R-LT-D04:** IF `.specify/trace.log` does not exist, THEN the script SHALL emit a warning to stderr and write an empty-state HTML page (not exit with error).

**R-LT-D05:** The script SHALL write a self-contained HTML file with no external dependencies (no CDN, no runtime server).

**R-LT-D06:** WHERE `--output <path>` is provided, the script SHALL write to that path instead of `.specify/dashboard.html`.

**R-LT-D07:** The script SHALL NOT modify `trace.log`, `drift.log`, or any `.specify/` artifact.

## Open questions

- Should undeclared file changes trigger a non-zero exit code to optionally pause the implement loop?
- Should hook priority relative to lens-drift be enforced via a fixed `priority` field or left to user config?
- Should `.specify/trace.log` be rotated or capped to avoid unbounded growth across many runs?

---

## Acceptance

Evaluatable test cases derived directly from requirements above.

- [ ] **R-LT-01/02:** Trace block for task T-01 contains `━` border, task ID, and task title
- [ ] **R-LT-03:** Trace block lists `src/api.py` when task scope declares `[src/api.py]`
- [ ] **R-LT-04:** Trace block shows `src/api.py +12 -3` when git diff reports those deltas
- [ ] **R-LT-05:** When task scope is `[src/api.py]` but `src/util.py` also changes, `src/util.py` is labeled `[undeclared]`
- [ ] **R-LT-06:** When task scope is `[src/api.py]` but `src/api.py` has no diff, it is labeled `[untouched]`
- [ ] **R-LT-07:** When git diff is empty, output contains "No file changes detected" and no table
- [ ] **R-LT-08:** When `tasks.md` is absent, output contains `lens-trace: could not identify current task`
- [ ] **R-LT-09/10:** After first task, `.specify/trace.log` exists and contains the task's trace block
- [ ] **R-LT-11:** Second implement run appends `[run: <timestamp>]` separator before new entries
- [ ] **R-LT-12:** Prior log entries are unchanged after second task appends to trace.log
- [ ] **R-LT-13/14:** `spec.md`, `plan.md`, `tasks.md` unmodified after trace runs
- [ ] **R-LT-16:** Trace completes in under 2 seconds on a 50-task project
