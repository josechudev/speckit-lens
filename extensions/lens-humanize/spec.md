# Spec: lens-humanize

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

`plan.md` is structured for agent consumption: dense, reference-heavy, optimized for task decomposition. Engineers can't use it to review scope, assign ownership, identify risks, or reason about what to ship first. Team review happens blind or gets skipped.

## Role in the suite

Runs as `after_plan` hook, between `/speckit.plan` and `/speckit.tasks`. Translates `plan.md` into a human-reviewable document without modifying the agent-facing artifact.

## Inputs

- `.specify/plan.md` — agent-optimized plan to translate
- `.specify/spec.md` — optional; enriches ownership signals and entry/exit criteria

## Outputs

- `.specify/plan-human.md` — translated plan (created or overwritten)
- Stdout summary (chunk count, size breakdown)

---

## Requirements

### Chunking

**R-LH-01:** WHEN `lens-humanize` runs, it SHALL divide `plan.md` into PR-sized chunks, each representing a coherent and independently shippable unit of work.

**R-LH-02:** WHEN chunking, `lens-humanize` SHALL ensure each chunk maps to a contiguous set of files or concerns; cross-cutting chunks are permitted only when the plan requires it.

**R-LH-03:** WHEN chunking, `lens-humanize` SHALL size each chunk such that a single engineer can estimate it as S (≤1 day), M (1–3 days), or L (>3 days).

**R-LH-04:** WHEN chunking, `lens-humanize` SHALL produce between 3 and 8 chunks; fewer for small plans, more only when the plan genuinely requires it.

### Per-chunk content

**R-LH-05:** WHEN writing a chunk, `lens-humanize` SHALL include: chunk number, title, owner signal, size estimate, entry criteria, exit criteria, files in scope, dependencies, blocks, and key decisions.

**R-LH-06:** WHEN emitting an owner signal, `lens-humanize` SHALL infer it from file paths and concern area (e.g., `src/api/` → backend) and SHALL label it as estimated, not authoritative.

**R-LH-07:** IF no owner inference is possible for a chunk, THEN `lens-humanize` SHALL emit `unknown` as the owner signal.

**R-LH-08:** WHEN listing dependencies, `lens-humanize` SHALL reference other chunks by number (e.g., "Chunk 2") and SHALL also emit which chunks the current one blocks.

### Dependency graph

**R-LH-09:** WHEN writing `.specify/plan-human.md`, `lens-humanize` SHALL prepend a text dependency graph showing chunk execution ordering before the chunk detail sections.

**R-LH-10:** WHEN a chunk has no dependencies and blocks no other chunk, `lens-humanize` SHALL label it `(independent)` in the dependency graph.

### Output file

**R-LH-11:** WHEN `lens-humanize` completes, it SHALL write the human plan to `.specify/plan-human.md`.

**R-LH-12:** IF `.specify/plan-human.md` already exists, THEN `lens-humanize` SHALL overwrite it without prompting.

**R-LH-13:** `lens-humanize` SHALL NOT write to or modify `plan.md`.

**R-LH-14:** `lens-humanize` SHALL NOT write to or modify `spec.md` or `tasks.md`.

**R-LH-15:** WHEN `lens-humanize` completes, it SHALL print a stdout summary containing: number of chunks produced and count per size tier (S/M/L).

### Format constraints

**R-LH-16:** `lens-humanize` SHALL produce valid Markdown parseable by standard renderers (GitHub, VS Code preview).

**R-LH-17:** `lens-humanize` SHALL complete in under 30 seconds for `plan.md` files up to 200 lines.

**R-LH-18:** IF `.specify/plan.md` is missing, THEN `lens-humanize` SHALL print an error and exit without writing any output file.

---

## Integration

- Runs between `after_plan` and `before_tasks` — must complete before the engineer reviews and approves the plan
- Does not interact with lens-trace, lens-drift, lens-compress, lens-contract, or lens-probe
- `.specify/plan-human.md` is a human artifact; no other speckit command reads it

## Open questions

- Should lens-humanize support `--format github-issue|jira` to emit chunks in issue/ticket format?
- Should S/M/L thresholds be configurable per-team?
- Should the dependency graph be rendered as a Mermaid diagram for GitHub rendering support?
- How to handle plans already chunked by the agent in a human-readable way — skip, enrich, or replace?

---

## Acceptance

Evaluatable test cases derived directly from requirements above.

- [ ] **R-LH-01/04:** For a 15-task plan, output contains between 3 and 8 chunk sections
- [ ] **R-LH-05:** Chunk 1 section contains all 9 fields: number, title, owner signal, size, entry criteria, exit criteria, files, depends-on, blocks, key decisions
- [ ] **R-LH-06:** Owner signal for chunk touching `src/api/` reads "backend (estimated)"
- [ ] **R-LH-07:** Owner signal for chunk touching only config files reads "unknown"
- [ ] **R-LH-09:** `.specify/plan-human.md` begins with dependency graph before first `## Chunk` heading
- [ ] **R-LH-10:** Chunk with no deps and no blocked chunks shows `(independent)` in graph
- [ ] **R-LH-11:** `.specify/plan-human.md` exists and is non-empty after run
- [ ] **R-LH-12:** Running twice overwrites `plan-human.md`; no prompt appears
- [ ] **R-LH-13:** `plan.md` byte-for-byte identical before and after run
- [ ] **R-LH-15:** Stdout summary contains chunk count and S/M/L breakdown
- [ ] **R-LH-16:** `plan-human.md` renders without errors in GitHub Markdown preview
- [ ] **R-LH-18:** When `plan.md` missing, error printed and `plan-human.md` not created
