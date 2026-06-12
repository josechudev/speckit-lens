# Spec: lens-drift

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

speckit implement runs succeed or fail at the file level, not the spec level. Code compiles and tests pass, but the implementation silently violates what the spec required. Drift is only caught in PR review — or in production.

## Role in the suite

lens-drift is the spec adherence guard. Runs as `after_task` hook. Reads the spec section mapped to the completed task, scores the generated code against it, and optionally injects a correction prompt before the next task.

## Inputs

- `.specify/tasks.md` — identifies the completed task
- `.specify/plan.md` — maps the task to its spec section(s)
- `.specify/spec.md` — source of requirements for the mapped section
- Git working tree diff — generated code to evaluate

## Outputs

- Stdout drift report after each task (always)
- Optional correction prompt injected into next task's context (if violations detected and engineer approves)
- `.specify/drift.log` — persistent append log of per-task scores and violations

---

## Requirements

### Spec section mapping

**R-LD-01:** WHEN an `after_task` hook fires, `lens-drift` SHALL locate the spec section(s) for the completed task by first checking for explicit spec references in the task's `tasks.md` entry, then in the corresponding `plan.md` section, then by inferring from task title and file scope.

**R-LD-02:** IF no spec section mapping can be found for a task, THEN `lens-drift` SHALL print `lens-drift: no spec mapping for task <id>` and SHALL exit without scoring.

### Adherence scoring

**R-LD-03:** WHEN scoring a task, `lens-drift` SHALL classify each requirement in the mapped spec section as one of: `OK`, `PARTIAL`, `MISSING`, or `VIOLATED`.

| Status | Meaning |
|--------|---------|
| `OK` | Requirement clearly addressed in generated code |
| `PARTIAL` | Requirement addressed but incompletely |
| `MISSING` | No corresponding implementation found |
| `VIOLATED` | Implementation contradicts the requirement |

**R-LD-04:** WHEN scoring is complete, `lens-drift` SHALL compute and report the score as `OK-count / total-requirements` (e.g., `7/9`).

**R-LD-05:** IF a requirement cannot be objectively verified from code alone (e.g., subjective UX requirement), THEN `lens-drift` SHALL classify it as `OK` to avoid false positives.

### Violation reporting — stdout

**R-LD-06:** WHEN a task scores less than 100%, `lens-drift` SHALL print a full drift report delimited with `━` border characters.

**R-LD-07:** WHEN reporting a non-OK requirement, `lens-drift` SHALL include: the status tag (`[PARTIAL]`, `[MISSING]`, or `[VIOLATED]`), the spec file and line number in the form `spec.md:<N>`, and the requirement text (verbatim, truncated to 120 characters).

**R-LD-08:** WHEN reporting a `PARTIAL` or `VIOLATED` requirement, `lens-drift` SHALL also include what was found in the generated code vs. what the spec requires.

**R-LD-09:** IF all requirements score `OK`, THEN `lens-drift` SHALL print only a single summary line and SHALL NOT print a full violation table.

### Correction prompt

**R-LD-10:** WHEN any MISSING, PARTIAL, or VIOLATED items exist, `lens-drift` SHALL ask the engineer: `lens-drift detected violations in task <id>. Inject correction prompt before next task? [y/N]`.

**R-LD-11:** WHILE running in a non-interactive environment, `lens-drift` SHALL default to `N` (no injection) without prompting.

**R-LD-12:** WHEN the engineer confirms injection, `lens-drift` SHALL prepend a correction block to the next task's context that lists each violation with its spec line reference and instructs the agent to address them before proceeding.

**R-LD-13:** WHEN injecting a correction block, `lens-drift` SHALL NOT replace the next task's context — it SHALL prepend to it.

### Persistent drift log

**R-LD-14:** WHEN an `after_task` hook fires and scoring completes, `lens-drift` SHALL append the task's score and any violations to `.specify/drift.log`.

**R-LD-15:** IF `.specify/drift.log` does not exist when the first `after_task` hook fires in an implement run, THEN `lens-drift` SHALL create it.

**R-LD-16:** WHEN the first task of a new implement run is scored, `lens-drift` SHALL prepend a run separator in the format `[run: <ISO-8601 timestamp>]` to the new log entries.

**R-LD-17:** WHILE appending to `.specify/drift.log`, `lens-drift` SHALL NOT truncate or modify any prior log entries.

### Behavioral constraints

**R-LD-18:** `lens-drift` SHALL NOT modify `.specify/spec.md`, `.specify/plan.md`, or `.specify/tasks.md`.

**R-LD-19:** `lens-drift` SHALL NOT modify any project source files.

**R-LD-20:** `lens-drift` SHALL NOT block the implement loop — the correction prompt is always opt-in.

**R-LD-21:** WHEN reporting a violation, `lens-drift` SHALL reference spec line numbers, not section names alone.

---

## Integration

- Runs in same `after_task` slot as lens-trace; lens-trace runs first
- Correction prompt injection requires speckit `>=0.9.1` context injection via hooks
- lens-probe validates runtime output; lens-drift validates generated code — non-overlapping
- Compressed artifacts from lens-compress must preserve all spec line references that lens-drift requires

## Open questions

- At what score threshold should lens-drift default to injecting correction without asking (e.g., score < 50%)?
- How to handle tasks that intentionally deviate from spec (refactor tasks with no spec section mapping)?
- Should `VIOLATED` severity halt the implement loop rather than being opt-in correctable?
- Should `.specify/drift.log` emit a summary score trend (per-run average) at the end of each run?

---

## Acceptance

Evaluatable test cases derived directly from requirements above.

- [ ] **R-LD-01:** When task T-03 has explicit spec ref `spec.md#auth`, drift reads `spec.md` section `auth`
- [ ] **R-LD-02:** When no spec mapping exists for task, output contains `lens-drift: no spec mapping for task <id>`; no score emitted
- [ ] **R-LD-03/04:** Drift report for a 9-requirement section shows score `7/9` when 2 are MISSING
- [ ] **R-LD-06/07:** MISSING requirement entry contains `[MISSING]`, `spec.md:<N>`, and requirement text ≤120 chars
- [ ] **R-LD-08:** VIOLATED entry shows "Found: ..." and "Expected: ..." sub-lines
- [ ] **R-LD-09:** When all requirements are OK, only one summary line is printed; no table
- [ ] **R-LD-10:** After violations detected, prompt `lens-drift detected violations ... [y/N]` appears
- [ ] **R-LD-11:** In CI (non-interactive), no prompt is shown and no correction is injected
- [ ] **R-LD-13:** Correction block is prepended; original next-task context is intact after it
- [ ] **R-LD-14/15:** After first scored task, `.specify/drift.log` exists with score entry
- [ ] **R-LD-16:** Second implement run prepends `[run: <timestamp>]` before new entries
- [ ] **R-LD-17:** Prior drift.log entries are unchanged after second task appends
- [ ] **R-LD-18/19:** `spec.md`, `plan.md`, `tasks.md`, and source files unmodified after drift runs
- [ ] **R-LD-21:** Every violation entry contains `spec.md:<line-number>` (not section name only)
