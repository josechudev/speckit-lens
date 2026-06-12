---
description: "After each implement task, diff generated code against the spec section mapped to that task. Score adherence and flag violations with spec line references."
---

You are the `lens-drift` extension running as an `after_task` hook inside a speckit `implement` loop.

## Goal

Detect spec drift immediately after each task completes — before the next task runs. Score adherence, identify violations with precise spec line references, and optionally surface a correction prompt.

## Steps

### 1. Identify the completed task

Read `.specify/tasks.md` to identify the just-completed task (ID + title).

### 2. Find the spec mapping

Locate the spec section(s) this task is responsible for, using this priority order:

1. Explicit spec reference in the task's entry in `tasks.md`
2. Spec section referenced in the corresponding section of `.specify/plan.md`
3. Infer from task title and the set of files modified

If no mapping can be found after all three methods, print exactly:

```
lens-drift: no spec mapping for task <id>
```

Then exit without scoring.

### 3. Extract requirements

Read `.specify/spec.md`. Locate the mapped section(s). For each requirement statement, record:
- Its line number in `spec.md`
- Its full text

### 4. Collect generated code

Use `git diff HEAD` (or the speckit hook file-change context) to collect all code written or modified by this task.

### 5. Score spec adherence

For each requirement, classify as:

| Status | Meaning |
|--------|---------|
| `OK` | Requirement clearly addressed in generated code |
| `PARTIAL` | Requirement addressed but incompletely |
| `MISSING` | No corresponding implementation found |
| `VIOLATED` | Implementation contradicts the requirement |

**EARS-pattern scoring** — detect the requirement's EARS keyword before deciding what code constructs constitute evidence:

| EARS keyword | What to look for in generated code |
|---|---|
| `WHEN <trigger>` | Event handler, callback, or listener for the trigger; body implements the response |
| `WHILE <state>` | Guard condition, state check, or precondition enforcing the state before response executes |
| `IF <condition> THEN` | Conditional branch, error handler, or guard clause that fires on the condition |
| `WHERE <feature enabled>` | Feature flag check, compile-time conditional, or configuration gate |
| Ubiquitous (no keyword, plain `SHALL`) | Unconditional — response must be present regardless of path |
| Compound (`WHEN … WHILE …`) | Both the event handler (WHEN) and the state guard (WHILE) must be present |

Apply this before scoring: if the EARS trigger/condition construct is absent, that is `MISSING` even if the response action appears elsewhere without the guard. If the guard is present but the response is incomplete, that is `PARTIAL`.

If a requirement cannot be objectively verified from code alone (e.g., subjective UX requirement, deployment concern), classify it as `OK` to avoid false positives.

Compute the score as: `<OK-count> / <total-requirements>`.

### 6. Print stdout drift report

**If score < 100%**, print the full report:

```
━━ lens-drift ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task    : <task-id> — <task-title>
Spec    : <spec section reference>
Score   : <ok>/<total> requirements met

Violations:
  [MISSING]  spec.md:<line> — <requirement text, ≤120 chars>
  [PARTIAL]  spec.md:<line> — <requirement text, ≤120 chars>
             → Found: <what was implemented>
             → Expected: <what spec requires>
  [VIOLATED] spec.md:<line> — <requirement text, ≤120 chars>
             → Found: <what was generated that contradicts spec>
             → Expected: <what spec requires>

Confirmed:
  [OK]  spec.md:<line> — <requirement text>
━━ done ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**If score is 100%**, print only:

```
━━ lens-drift: task <task-id> — all <N> requirements met ━━
```

### 7. Write to .specify/drift.log

Append to `.specify/drift.log`. Create the file if it does not exist.

**Run separator** — write `[run: <ISO-8601 timestamp>]` only once per implement session, before the first task's log block. For subsequent tasks in the same session, skip the run separator and append the task block directly.

To detect "first task of this session": check whether the last line of `drift.log` (if the file already exists) belongs to a prior run. A new run separator is needed when either the file is new/empty or the current implement session has not yet written a run header.

**Exact log format** (must match dashboard.py parser):

```
[run: 2026-06-12T14:32:10+00:00]
━━ lens-drift ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task    : <task-id> — <task-title>
Score   : <ok>/<total>
[MISSING]  spec.md:<line> — <requirement text, ≤120 chars>
[PARTIAL]  spec.md:<line> — <requirement text, ≤120 chars>
[VIOLATED] spec.md:<line> — <requirement text, ≤120 chars>
━━ done ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Rules:
- `OK` items are **not** written to `drift.log` — only MISSING, PARTIAL, VIOLATED appear, plus Task and Score lines
- Prior log entries must never be modified — append only
- `Task    :` (4 spaces before colon) aligns with `Score   :` (3 spaces) — keeps columns readable
- Each violation line starts with `[STATUS]` at column 0 (no indentation in the log)

### 8. Correction prompt

If any MISSING, PARTIAL, or VIOLATED items exist:

**Non-interactive check** — if stdin is not a TTY (CI environment, piped input), skip the prompt entirely and do not inject any correction.

If interactive, ask:

```
lens-drift detected violations in task <task-id>. Inject correction prompt before next task? [y/N]
```

Default is `N`. If the engineer answers `y`, prepend the following block to the next task's context (do not replace the existing context — prepend to it):

```
CORRECTION REQUIRED from lens-drift (task <task-id>):
The following spec requirements were not fully met:
• spec.md:<line> [<STATUS>] — <requirement text>
• spec.md:<line> [<STATUS>] — <requirement text>
Address these before proceeding with the next task.
```

## Constraints

- Do NOT modify `.specify/spec.md`, `.specify/plan.md`, `.specify/tasks.md`, or any project source files
- Do NOT block the implement loop — correction prompt is always opt-in
- Every violation entry must reference `spec.md:<line-number>` (not section name alone)
- VIOLATED severity does not halt the loop — it is opt-in correctable only

$ARGUMENTS
