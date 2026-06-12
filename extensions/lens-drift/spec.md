# Spec: lens-drift

## Problem

speckit implement runs succeed or fail at the file level, not the spec level. Code compiles and tests pass, but the implementation silently violates what the spec required. Drift is only caught in PR review — or in production.

## Role in the suite

lens-drift is the spec adherence guard. It runs as an `after_task` hook, reads the spec section mapped to the completed task, reads the generated code, and scores adherence. It can optionally inject a correction prompt before the next task.

## Inputs

- `.specify/tasks.md` — identifies the completed task
- `.specify/plan.md` — maps the task to its spec section(s)
- `.specify/spec.md` — source of requirements for the mapped section
- Git working tree diff — the generated code to evaluate

## Outputs

- A drift report printed to stdout (always)
- An optional correction prompt injected into the next task's context (if violations detected and engineer approves)

## Behavior

### Spec section mapping

lens-drift must locate the spec section(s) corresponding to the completed task by:
1. Reading the task entry in tasks.md for any explicit spec references
2. Reading the plan section for this task and extracting its spec references
3. If no explicit reference exists, infer the relevant spec section from the task title and file scope

If no mapping can be found, lens-drift must print: `lens-drift: no spec mapping for task <id>` and exit without scoring.

### Adherence scoring

For each requirement in the mapped spec section(s), classify as:

| Status | Meaning |
|--------|---------|
| `OK` | Requirement clearly addressed in generated code |
| `PARTIAL` | Requirement addressed but incompletely |
| `MISSING` | No corresponding implementation found |
| `VIOLATED` | Implementation contradicts the requirement |

Score = (OK count) / (total requirements). Report as `X/N`.

### Violation reporting

Each non-OK item must include:
- Status tag: `[PARTIAL]`, `[MISSING]`, or `[VIOLATED]`
- Spec file + line number reference
- The requirement text (verbatim, truncated to 120 chars)
- For `PARTIAL` and `VIOLATED`: what was found vs. what was required

### Correction prompt

If any MISSING, PARTIAL, or VIOLATED items exist, lens-drift must ask the engineer whether to inject a correction prompt. The correction prompt must:
- Be prepended to the next task's context (not replace it)
- List each violation with its spec reference
- Instruct the agent to address violations before proceeding

This interaction must be skippable — defaulting to "no" on non-interactive runs.

### Clean pass

If all requirements score `OK`, print a one-line summary only. Do not print a full report.

### Ambiguous requirements

Requirements that cannot be objectively verified from code alone (e.g., subjective UX requirements) must be treated as `OK` to avoid false positives.

## Constraints

- Must not modify `.specify/` artifacts (spec.md, plan.md, tasks.md)
- Must not modify source files
- Must not block the implement loop — correction prompt is opt-in
- Spec references must include line numbers, not just section names

## Integration

- Runs in same `after_task` slot as lens-trace; lens-trace runs first
- lens-drift's correction prompt mechanism feeds into the next implement task's context — speckit must support context injection via hooks for this to work (requires speckit `>=0.9.1`)
- lens-probe validates runtime output; lens-drift validates generated code — complementary, non-overlapping

## Open questions

- Should lens-drift write violations to `.specify/drift.log` for trend analysis across an implement run?
- Scoring threshold: at what score should lens-drift default to "inject correction" without asking?
- How to handle tasks that intentionally deviate from spec (e.g., a refactor task with no spec section)?
- Should `VIOLATED` violations halt the implement loop rather than being opt-in correctable?
