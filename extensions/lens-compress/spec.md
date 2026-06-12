# Spec: lens-compress

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

speckit re-reads `spec.md`, `plan.md`, and `tasks.md` on every implement turn. As these files grow, token consumption compounds. A 400-line spec with a 200-line plan read 20 times across an implement run represents significant waste — without contributing new information after the first read.

## Role in the suite

Runs as `before_implement` hook. Compresses speckit artifacts in place before the implement loop begins. Backs up originals for restoration.

## Inputs

- `.specify/spec.md` (if present)
- `.specify/plan.md` (if present)
- `.specify/tasks.md` (if present)

## Outputs

- Compressed versions of each input file (in place)
- Backup files: `<file>.original.md` for each compressed file
- Stdout compression report

---

## Requirements

### Backup

**R-LC-01:** WHEN `lens-compress` is about to modify a file, it SHALL first write the original content to `<file>.original.md`.

**R-LC-02:** IF `<file>.original.md` already exists, THEN `lens-compress` SHALL NOT overwrite the backup and SHALL compress the current file in place.

**R-LC-03:** IF a target file (`spec.md`, `plan.md`, `tasks.md`) does not exist, THEN `lens-compress` SHALL skip it without error.

### Already-compressed detection

**R-LC-04:** IF `<file>.original.md` already exists for a target file, THEN `lens-compress` SHALL treat that file as already compressed, report it as "already compressed (skipped)", and SHALL NOT re-compress it.

### Compression rules — preserve

**R-LC-05:** WHILE compressing any artifact, `lens-compress` SHALL preserve verbatim all requirement statements containing `must`, `should`, `shall`, `will`, or `must not`.

**R-LC-06:** WHILE compressing any artifact, `lens-compress` SHALL preserve verbatim all task IDs (e.g., `T-01`, `TASK-001`) and task status markers (`[x]`, `[ ]`).

**R-LC-07:** WHILE compressing any artifact, `lens-compress` SHALL preserve verbatim all file paths, function names, type names, identifiers, and symbols.

**R-LC-08:** WHILE compressing any artifact, `lens-compress` SHALL preserve verbatim all fenced code blocks (` ``` ` delimited).

**R-LC-09:** WHILE compressing any artifact, `lens-compress` SHALL preserve all numbered list ordering and all section heading hierarchy levels.

**R-LC-10:** WHILE compressing any artifact, `lens-compress` SHALL preserve all spec line references (e.g., `spec.md:42`).

### Compression rules — remove

**R-LC-11:** WHILE compressing any artifact, `lens-compress` SHALL remove filler words: "basically", "simply", "just", "really", "actually", "in order to".

**R-LC-12:** WHILE compressing any artifact, `lens-compress` SHALL remove redundant preamble phrases: "This section describes...", "The following...", "Please note that...".

**R-LC-13:** WHILE compressing any artifact, `lens-compress` SHALL remove section headers that only restate the content immediately below them.

**R-LC-14:** WHILE compressing any artifact, `lens-compress` SHALL collapse consecutive blank lines to a single blank line.

**R-LC-15:** WHILE compressing any artifact, `lens-compress` SHALL remove closing summary paragraphs that restate content already present in the section.

### Validation

**R-LC-16:** WHEN compression of a file is complete, `lens-compress` SHALL verify that all task IDs from the original are present in the compressed version.

**R-LC-17:** WHEN compression of a file is complete, `lens-compress` SHALL verify that all `must`/`should`/`shall` requirement statements are present (exact match not required; substance must be preserved).

**R-LC-18:** WHEN compression of a file is complete, `lens-compress` SHALL verify that no fenced code blocks are missing or modified.

**R-LC-19:** IF validation fails for a file, THEN `lens-compress` SHALL restore the file from its `.original.md` backup, report the validation failure with details, and SHALL NOT leave the file in a partially compressed state.

### Minimum compression threshold

**R-LC-20:** IF a file compresses by less than 5% (by character count), THEN `lens-compress` SHALL restore the original content, report "minimal compression opportunity — skipped", and SHALL NOT write the compressed version.

### Reporting

**R-LC-21:** WHEN `lens-compress` completes, it SHALL print a stdout report showing for each file: original character count, compressed character count, and percentage reduction (using char-count ÷ 4 as token proxy).

**R-LC-22:** `lens-compress` SHALL target 20–40% token reduction. Where a file falls outside this range, `lens-compress` SHALL note it in the report but SHALL NOT fail.

### Behavioral constraints

**R-LC-23:** `lens-compress` SHALL NOT modify files outside `.specify/`.

**R-LC-24:** `lens-compress` SHALL NOT modify fenced code blocks in any artifact.

**R-LC-25:** `lens-compress` SHALL complete compression of all three artifacts in under 60 seconds for files up to 500 lines each.

**R-LC-26:** `lens-compress` SHALL execute once per implement session (as a `before_implement` hook), not once per task.

---

## Integration

- Runs `before_implement` alongside lens-contract; execution order is user-configured
- Does not interact with lens-trace or lens-drift at run time (those run during implement)
- Compressed artifacts must preserve all spec line references that lens-drift reads during the implement loop

## Open questions

- Should `--dry-run` flag preview compression stats without writing any files?
- Should individual files be selectable via `$ARGUMENTS` rather than always compressing all three?
- Should lens-compress track compression ratio history across runs to detect diminishing returns?
- Is 5% the right minimum threshold, or should it be configurable?

---

## Acceptance

Evaluatable test cases derived directly from requirements above.

- [ ] **R-LC-01:** Before modifying `spec.md`, `spec.md.original.md` is created with identical content
- [ ] **R-LC-02:** If `spec.md.original.md` already exists, it is not overwritten; compression still runs on current `spec.md`
- [ ] **R-LC-03:** Absent `tasks.md` causes no error; run completes for the other two files
- [ ] **R-LC-04:** If `spec.md.original.md` exists, report says "already compressed (skipped)" for spec.md
- [ ] **R-LC-05:** After compression, all original `must`/`should`/`shall` sentences remain (spot-check 5)
- [ ] **R-LC-08:** All fenced code blocks in original appear verbatim in compressed output
- [ ] **R-LC-06:** All task IDs (`T-01`, `T-02`, etc.) present in compressed `tasks.md`
- [ ] **R-LC-16/17/18:** Validation passes for a well-formed spec.md; compressed file retained
- [ ] **R-LC-19:** When validation is manually broken (inject missing task ID), original is restored and failure reported
- [ ] **R-LC-20:** A file with <5% compression opportunity is reported as "skipped" and restored
- [ ] **R-LC-21:** Stdout report shows char counts and % reduction for each processed file
- [ ] **R-LC-23:** No files outside `.specify/` are modified
- [ ] **R-LC-24:** Fenced code block content byte-for-byte identical before and after compression
