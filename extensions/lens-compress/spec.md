# Spec: lens-compress

## Problem

speckit re-reads `spec.md`, `plan.md`, and `tasks.md` on every implement turn. As these files grow, token consumption compounds. A 400-line spec with a 200-line plan read 20 times across an implement run represents significant waste — without contributing new information after the first read.

## Role in the suite

lens-compress runs as a `before_implement` hook. It compresses speckit artifacts in place before the implement loop begins. It backs up originals so the engineer can restore if needed.

## Inputs

- `.specify/spec.md`
- `.specify/plan.md`
- `.specify/tasks.md`

Any of these may be absent; absent files are skipped without error.

## Outputs

- Modified versions of input files (compressed in place)
- Backup files: `*.original.md` for each compressed file
- Stdout compression report

## Behavior

### Compression rules

Compression must preserve all semantic content. Specifically:

**Must preserve verbatim:**
- All requirement statements containing `must`, `should`, `shall`, `will`, `must not`
- All task IDs (e.g., `T-01`, `TASK-001`) and task status markers (`[x]`, `[ ]`)
- All file paths, function names, type names, identifiers, and symbols
- All code blocks (fenced with ` ``` `)
- All numbered list ordering
- All section headings and their hierarchy levels
- All spec line references (e.g., `spec.md:42`)

**Must remove:**
- Filler words: "basically", "simply", "just", "really", "actually", "in order to"
- Redundant preamble phrases: "This section describes...", "The following...", "Please note that..."
- Section headers that only restate the content immediately below them
- Consecutive blank lines (collapse to one)
- Closing summary paragraphs that restate what was already said

**May shorten:**
- Long sentences to fragments when the subject is unambiguous from context
- "implementation of the feature" → "feature implementation"
- Passive constructions → active where meaning is preserved

### Backup behavior

Before modifying any file, write `<file>.original.md`:
- `spec.md` → `spec.md.original.md`
- `plan.md` → `plan.md.original.md`
- `tasks.md` → `tasks.md.original.md`

If `<file>.original.md` already exists, skip backup and compress in place — do not overwrite an existing backup.

### Already-compressed detection

If `.original.md` backup already exists for a file, treat that file as already compressed. Report it as "already compressed (skipped)" in the output.

### Validation

After compressing each file, validate:
1. All task IDs present in the original appear in the compressed version
2. All `must`/`should`/`shall` sentences are present (exact match not required, but substance must be preserved)
3. No code blocks are missing or modified

If validation fails for any file: restore from `.original.md`, report the failure, and do not compress that file.

### Token estimation

Use character count divided by 4 as a token proxy. Report original and compressed counts for each file, with percentage reduction.

### Target reduction

Target 20–40% token reduction. If a file compresses by less than 5%, report it as "minimal compression opportunity — skipped" and restore the original.

## Constraints

- Must not compress code blocks (reproduce verbatim)
- Must not modify files outside `.specify/`
- Must complete in under 60 seconds for artifacts up to 500 lines each
- Backup must exist before any in-place modification occurs

## Integration

- Runs as `before_implement` — executes once per implement session, not per task
- Does not interact with lens-trace or lens-drift (those run during implement)
- Works alongside lens-contract (both run `before_implement`; order is user-configured)
- Compressed artifacts are what lens-drift reads during the implement loop — compression must preserve all spec references that lens-drift needs

## Open questions

- Should lens-compress support a `--dry-run` flag to preview compression without writing?
- Should it support compressing individual files via `$ARGUMENTS` rather than all three always?
- Should it track compression ratio history across runs to detect diminishing returns?
- Is 5% the right minimum threshold, or should it be configurable?
