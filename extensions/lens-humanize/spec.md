# Spec: lens-humanize

## Problem

`plan.md` is structured for agent consumption: dense, reference-heavy, optimized for task decomposition. Engineers can't use it to review scope, assign ownership, identify risks, or reason about what to ship first. Team review happens blind or gets skipped.

## Role in the suite

lens-humanize runs as an `after_plan` hook, between `/speckit.plan` and `/speckit.tasks`. It translates `plan.md` into a human-reviewable document without modifying the agent-facing artifact.

## Inputs

- `.specify/plan.md` — the agent-optimized plan to translate
- `.specify/spec.md` — optional; used to enrich ownership signals and entry/exit criteria

## Outputs

- `.specify/plan-human.md` — the translated plan (created or overwritten)
- Stdout summary (chunk count, size breakdown)

## Behavior

### Chunking

lens-humanize must divide plan.md into PR-sized chunks where each chunk:
- Represents a coherent, independently shippable unit of work
- Maps to a contiguous set of files or concerns (no cross-cutting chunks unless necessary)
- Is estimable by a single engineer in ≤3 days (size `S`, `M`, or `L`)

Target: 3–8 chunks. Fewer for small plans, more only when the plan genuinely requires it.

### Per-chunk output

Each chunk must include:
- Chunk number and title
- Owner signal: inferred from file paths and concern area (label as estimated, not assigned)
- Size estimate: `S` (≤1 day), `M` (1–3 days), `L` (>3 days)
- Entry criteria: what must be true before this chunk can start
- Exit criteria: what must be true for this chunk to be considered done
- Files in scope
- Dependencies: which other chunks must complete first
- Blocks: which other chunks this one gates
- Key decisions: architectural or product decisions embedded in this chunk that reviewers should scrutinize

### Dependency graph

Before the chunks, output a text dependency graph showing the execution ordering. Format:

```
Chunk 1 → Chunk 3 → Chunk 5
Chunk 2 → Chunk 4
Chunk 6 (independent)
```

### Output file

Write to `.specify/plan-human.md`. If the file already exists, overwrite it.

### plan.md must not be modified

lens-humanize must never write to `plan.md`. The agent-facing plan must remain intact for `/speckit.tasks` to consume.

### Owner signal accuracy

Owner signals are inferences from file paths (e.g., `src/api/` → backend, `src/ui/` → frontend). They must be labeled as inferred, not authoritative. If no inference is possible, emit `unknown`.

## Constraints

- Must not modify `plan.md`, `spec.md`, or `tasks.md`
- Must produce valid Markdown parseable by standard renderers
- Owner signals must be clearly labeled as estimated, not assigned
- Must run in under 30 seconds for plans up to 200 lines

## Integration

- Runs between `after_plan` and `before_tasks` — timing is critical; it must complete before the engineer reviews and approves
- Does not interact with lens-trace, lens-drift, lens-compress, lens-contract, or lens-probe
- `.specify/plan-human.md` is a human artifact; it is not consumed by any other speckit command

## Open questions

- Should lens-humanize support a `--format` flag for different output styles (e.g., GitHub issue format, JIRA ticket format)?
- Should chunk size estimates be configurable per-team (some teams have different definitions of S/M/L)?
- Should the dependency graph be rendered as a Mermaid diagram for GitHub rendering?
- How to handle plans that are already chunked by the agent in a human-readable way — skip, enrich, or replace?
