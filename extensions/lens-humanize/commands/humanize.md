---
description: "Translate the agent-oriented plan.md into PR-sized work chunks with human-readable ownership signals, visible dependencies, and entry/exit criteria."
---

You are the `lens-humanize` extension running after `/speckit.plan` and before `/speckit.tasks`.

## Goal

Produce a human-reviewable version of `plan.md` — one that a team of engineers can divide, own, and reason about without reading the agent-optimized original. Write the output to `.specify/plan-human.md`.

## Steps

### 1. Read the plan

Read `.specify/plan.md` in full. Identify all top-level work units, their dependencies, and any phasing or ordering assumptions the agent encoded.

### 2. Group into PR-sized chunks

Divide the work into chunks where each chunk:
- Represents a shippable unit (can be reviewed and merged independently)
- Touches a coherent set of files or concerns
- Is estimable by a single engineer in ≤3 days

Aim for 3–8 chunks. If the plan is small, fewer is fine.

### 3. For each chunk, produce a work block

```markdown
## Chunk <N>: <title>

**Owner signal:** <which team / role this belongs to, inferred from the files/concerns>
**Estimated scope:** <S / M / L>

**Entry criteria:**
- <what must be true before this chunk can start>

**Exit criteria:**
- <what must be true for this chunk to be considered done>

**Files in scope:**
- <file or directory>

**Depends on:** Chunk <N>, Chunk <N> (or "none")
**Blocks:** Chunk <N>, Chunk <N> (or "none")

**Key decisions visible here:**
- <any architectural or product decision baked into this chunk that reviewers should scrutinize>
```

### 4. Prepend a dependency graph summary

Before the chunks, write a brief dependency ordering:

```
Chunk 1 → Chunk 3 → Chunk 5
Chunk 2 → Chunk 4
Chunk 6 (independent)
```

### 5. Write the output

Write the full human plan to `.specify/plan-human.md`. Do not modify `plan.md`.

Print a summary:
```
━━ lens-humanize ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Translated plan.md → .specify/plan-human.md
Chunks : <N>
Sizes  : <S count>S / <M count>M / <L count>L
Review the human plan before running /speckit.tasks.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Notes

- Do not modify `plan.md`. The agent needs it unchanged.
- If `plan.md` is missing, print an error and exit.
- Owner signals are inferred — label them as estimates, not assignments.

$ARGUMENTS
