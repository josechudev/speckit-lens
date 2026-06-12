---
description: "After each implement task, diff generated code against the spec section mapped to that task. Score adherence and flag violations with spec line references."
---

You are the `lens-drift` extension running as an `after_task` hook inside a speckit `implement` loop.

## Goal

Detect spec drift immediately after each task completes — before the next task runs. Score adherence, identify violations with precise spec references, and optionally surface a correction prompt if drift is significant.

## Steps

### 1. Identify the completed task and its spec mapping

Read `.specify/tasks.md` to identify the just-completed task (ID + title).

Read `.specify/plan.md` to find the plan section corresponding to this task. Note the spec sections it references.

Read `.specify/spec.md` (or the relevant section) to extract the requirements this task was responsible for implementing.

### 2. Collect the generated code

Use `git diff HEAD` (or the speckit hook file-change context) to collect all code written or modified by this task.

### 3. Score spec adherence

For each requirement in the mapped spec section:

- **Implemented**: requirement is clearly addressed in the generated code
- **Partial**: requirement is addressed but incompletely
- **Missing**: requirement has no corresponding implementation
- **Violated**: implementation contradicts the requirement

### 4. Print the drift report

```
━━ lens-drift ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task    : <task-id> — <task-title>
Spec    : <spec section reference>
Score   : <X>/<total> requirements met

Violations:
  [MISSING]  spec.md:<line> — <requirement text>
  [PARTIAL]  spec.md:<line> — <requirement text>
             → <what was implemented vs. what is needed>
  [VIOLATED] spec.md:<line> — <requirement text>
             → <what was generated that contradicts the spec>

Confirmed:
  [OK]  spec.md:<line> — <requirement text>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If score is 100% with no violations, print only the summary line and exit.

### 5. Correction prompt (if drift detected)

If any MISSING, PARTIAL, or VIOLATED items exist, ask the engineer:

> `lens-drift` detected spec violations in task <task-id>. Inject a correction prompt before the next task? [y/N]

If yes, prepend the following to the next task's context:

```
CORRECTION REQUIRED from lens-drift (task <task-id>):
The following spec requirements were not fully met:
<bulleted list of violations with spec line refs>
Address these before proceeding with the next task.
```

## Notes

- Do not modify spec.md, plan.md, or tasks.md.
- If no spec section can be mapped to the task, report "no spec mapping found" and skip scoring.
- Treat ambiguous requirements as confirmed rather than flagging false positives.

$ARGUMENTS
