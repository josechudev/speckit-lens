---
description: "Apply semantic compression to speckit artifacts (spec.md, plan.md, tasks.md) before implement runs. Preserves all semantic content. Backs up originals."
---

You are the `lens-compress` extension running as a `before_implement` hook.

## Goal

Reduce token consumption during the `implement` loop by compressing `.specify/` artifacts in place. Semantic content must be fully preserved — compression removes only filler, redundancy, and formatting overhead. Back up originals before touching anything.

## Target files

- `.specify/spec.md`
- `.specify/plan.md`
- `.specify/tasks.md`

Skip any file that doesn't exist.

## Steps

### 1. Back up originals

For each target file that exists, copy it to `<file>.original.md` before modifying:
- `.specify/spec.md` → `.specify/spec.md.original.md`
- `.specify/plan.md` → `.specify/plan.md.original.md`
- `.specify/tasks.md` → `.specify/tasks.md.original.md`

Do not overwrite existing backups — if `.original.md` already exists, skip the backup and compress in place.

### 2. Compress each artifact

Apply these compression rules to each file:

**Drop without semantic loss:**
- Filler words and phrases: "basically", "simply", "just", "in order to", "it is important to note that", "please note"
- Redundant section headers that restate the content below them
- Repetitive preambles ("This section describes...", "The following...")
- Blank lines beyond one between sections
- Verbose bullet constructions ("The system should be able to..." → "System must...")

**Preserve exactly:**
- All requirement statements (must/should/shall/will)
- All task IDs, task titles, task status markers
- All file paths, function names, type names, identifiers
- All numbered lists and their ordering
- All code blocks verbatim
- All spec line references and cross-references
- Section hierarchy (heading levels)

**Shorten where meaning is retained:**
- Long sentences → fragments when subject is clear from context
- "implementation of the feature" → "feature implementation"
- Multi-sentence equivalents → single sentence

### 3. Validate compression

After compressing each file, verify:
- All task IDs from the original are present in the compressed version
- All `must`/`should`/`shall` requirement statements are present
- No code blocks were modified

If validation fails, restore from `.original.md` and report the failure.

### 4. Print a compression report

```
━━ lens-compress ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
spec.md    : <original tokens> → <compressed tokens> (<reduction>%)
plan.md    : <original tokens> → <compressed tokens> (<reduction>%)
tasks.md   : <original tokens> → <compressed tokens> (<reduction>%)
─────────────────────────────────────────────────────────────
Total saved: ~<N> tokens
Originals  : backed up as *.original.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Use character counts as a token proxy (÷4 for approximate tokens).

## Notes

- If a file is already compressed (`.original.md` exists), report it as "already compressed" and skip.
- Never compress code blocks — reproduce them verbatim.
- The goal is 20–40% token reduction while keeping full semantic fidelity.

$ARGUMENTS
