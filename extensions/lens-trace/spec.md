# Spec: lens-trace

## Problem

During a speckit `implement` run, engineers have no visibility into execution. They see file changes after the fact but nothing during: which task is active, what files it intends to touch, or whether it completed cleanly. Debugging a failed implement run requires archaeology.

## Role in the suite

lens-trace is the observability layer. It runs as an `after_task` hook and emits structured output after each task completes. It has no side effects on the implement run itself.

## Inputs

- `.specify/tasks.md` — source of task ID, title, and file scope
- `.specify/plan.md` — optional; used to cross-reference intended file scope vs. actual
- Git working tree diff — source of actual file changes

## Outputs

A trace report printed to stdout after each task. No files written.

## Behavior

### Trace report format

The trace report must:
- Print a header with task ID and title
- List files the task declared intent to modify (from tasks.md scope)
- List files actually changed (from git diff), with line-level delta (`+N -N`)
- Mark any file changed but not in declared scope as `[undeclared]`
- Mark any declared file not changed as `[untouched]`
- Print a footer when complete

### Undeclared changes

If a task modifies files outside its declared scope, lens-trace must flag each undeclared file. It must not block the implement run — flagging is informational only.

### No changes detected

If git diff produces no output after a task, the report must say "No file changes detected" rather than printing an empty table.

### Missing task context

If `.specify/tasks.md` is missing or the current task cannot be identified from hook context:
- Print a warning: `lens-trace: could not identify current task`
- Print the git diff summary anyway without task metadata

### Output format

Output must be delimited with a consistent border so it is visually distinct from speckit's own output. Use `━` as the border character.

## Constraints

- Must not modify any project files
- Must not modify `.specify/` artifacts
- Must not block or alter the implement loop under any condition
- Must complete in under 2 seconds (read-only operations only)

## Integration

- Designed to run alongside `lens-drift` in the same `after_task` hook slot
- When both are active, lens-trace runs first (lower hook priority number), then lens-drift
- lens-trace output should be visually separable from lens-drift output

## Open questions

- Should lens-trace write a structured log to `.specify/trace.log` for post-run review?
- Should undeclared file changes trigger a non-zero exit to pause the implement loop?
- Hook priority relative to lens-drift: enforce via `priority` field or leave to user config?
