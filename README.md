# speckit-lens

> Human-facing visibility and contract tooling for [spec-kit](https://github.com/github/spec-kit) workflows.

speckit-lens is a suite of six extensions that address the parts of spec-driven development that speckit leaves opaque: plan readability, execution tracing, spec drift, token cost, and runtime contract validation. Each extension is independent and installable separately, but they are designed to work together as a cohesive layer on top of a standard speckit setup.

---

## Status

| Extension | Status | Notes |
|-----------|--------|-------|
| `lens-trace` | ⚠️ Implemented — needs verification | Includes static HTML dashboard (`/speckit.lens.dashboard`) |
| `lens-drift` | ⚠️ Implemented — needs verification | EARS-aware scoring, drift.log output |
| `lens-humanize` | ⚠️ Implemented — needs verification | Writes `.specify/plan-human.md` |
| `lens-contract` | ⚠️ Implemented — needs verification | OpenAPI + JSON Schema, interactive Q&A |
| `lens-compress` | 🔲 Not started | |
| `lens-probe` | 🔲 Not started | |

---

## The Problem

speckit is powerful but optimized for agent consumption, not human oversight. During a typical `implement` run:

- You don't know which task is executing or which files it intends to touch
- Spec drift happens silently — the code compiles but violates the contract
- The plan is structured for the agent, not for your team to review and own
- Token consumption compounds across every session with no compression
- Contracts are tedious to write, so they get skipped — leaving runtime behavior unvalidated
- When runtime output violates a contract, there's no path to bring that evidence back into speckit

speckit-lens closes each of these gaps.

---

## Extensions

### `lens-trace` — Task Execution Visibility

Surfaces what speckit is doing inside `implement` in real time: which task is running, what files it intends to modify, and a summary of what changed. Appends a structured log to `.specify/trace.log`. Generates a static HTML dashboard on demand.

```
/speckit.lens.trace
/speckit.lens.dashboard
```

**Solves:** Black-box `implement` runs where the only feedback is file changes after the fact.

---

### `lens-drift` — Per-Task Spec Adherence Guard

After each task in the `implement` loop, diffs the generated code against the spec section mapped to that task. Scores adherence using EARS-pattern detection, flags violations with spec line references, optionally injects a correction prompt before the next task, and appends scores to `.specify/drift.log`.

```
/speckit.lens.drift
```

**Solves:** Silent mid-implement drift where speckit "succeeds" but the output doesn't match spec intent.

---

### `lens-humanize` — Human-Readable Plan Translation

Translates the agent-oriented `plan.md` into PR-sized chunks with clear ownership signals, visible dependencies, and entry/exit criteria per chunk. Runs between `/speckit.plan` and `/speckit.tasks` so the plan is human-reviewable before implementation begins.

```
/speckit.lens.humanize
```

**Solves:** Plans written for agent consumption that engineers can't review, own, or divide into real work units.

---

### `lens-compress` — Speckit Artifact Compression

Applies semantic compression to speckit artifacts (`spec.md`, `plan.md`, `tasks.md`) before `implement` runs, reducing context token consumption without losing semantic content. Originals are backed up before compression.

```
/speckit.lens.compress
```

**Solves:** Excessive token consumption during `implement` caused by full artifact re-reads on every turn.

---

### `lens-contract` — Conversational Contract Generation

Accepts an OpenAPI spec or base JSON schema as input, asks targeted questions about expected runtime behavior (cardinality, required fields, invariants, event ordering), and generates a structured contract file in `.specify/contracts/`. Runs as a `before_implement` hook so contracts exist before code is written.

```
/speckit.lens.contract --from openapi.yaml
```

**Solves:** Contract generation being too tedious to do manually, leading to skipped contracts and unvalidatable runtime behavior.

---

### `lens-probe` — Runtime Output Validation

Accepts raw ADK response stream JSON and validates it against a contract in `.specify/contracts/`. Reports violations with event index, rule reference, and what was found versus what the contract expects. Suitable as a CI gate (exit code `1` on violations).

```
/speckit.lens.probe --input stream.json --contract contracts/api.md
```

**Solves:** No path to bring Postman/runtime output evidence back into speckit for contract validation.

---

## Extension Pairs

`lens-contract` + `lens-probe` — one generates the contract from your schema, the other validates runtime output against it.

`lens-trace` + `lens-drift` — designed to run together during `implement`: trace surfaces what's happening, drift validates that what happened matches the spec. Both feed the dashboard.

---

## Adding extensions to a speckit project

### Prerequisites

- speckit `>=0.9.1` (hooks stable from this version)
- `uv` installed (required for `lens-trace` dashboard script only)

### From this repo (local dev)

Install each extension directly from its directory:

```bash
cd /your/speckit/project

specify extension add lens-trace    --from /path/to/speckit-lens/extensions/lens-trace
specify extension add lens-drift    --from /path/to/speckit-lens/extensions/lens-drift
specify extension add lens-humanize --from /path/to/speckit-lens/extensions/lens-humanize
specify extension add lens-compress --from /path/to/speckit-lens/extensions/lens-compress
specify extension add lens-contract --from /path/to/speckit-lens/extensions/lens-contract
specify extension add lens-probe    --from /path/to/speckit-lens/extensions/lens-probe
```

Or via zip:

```bash
zip -r lens-trace.zip /path/to/speckit-lens/extensions/lens-trace
specify extension add lens-trace --from ./lens-trace.zip
```

### From a release (once published)

```bash
specify extension add lens-trace    --from https://github.com/josechudev/speckit-lens/archive/refs/tags/v0.1.0.zip
```

### Verify installation

```bash
specify extension list
# lens-trace    0.1.0   ✓
# lens-drift    0.1.0   ✓
# ...
```

### Recommended install order

Install all at once — extensions are independent. If installing selectively, respect these dependencies:

1. Install `lens-contract` before `lens-probe` (probe reads contracts that contract writes)
2. Install `lens-trace` before `lens-drift` (drift.log feeds the trace dashboard)
3. `lens-compress` and `lens-humanize` have no dependencies on other lens extensions

### Recommended workflow

```
/speckit.specify          # define what to build
/speckit.lens.contract    # generate contracts before any code is written
/speckit.plan             # agent builds plan.md
/speckit.lens.humanize    # translate plan for human review → .specify/plan-human.md
/speckit.lens.compress    # compress artifacts to reduce token load
/speckit.tasks            # agent breaks plan into tasks
/speckit.implement        # implement loop — lens-trace + lens-drift fire after each task
/speckit.lens.dashboard   # post-run: generate HTML report from trace.log + drift.log
/speckit.lens.probe       # validate runtime output against contracts
```

### Hook execution order during `implement`

Both `lens-trace` and `lens-drift` run as `after_task` hooks. Priority is fixed:

| Priority | Extension | Hook |
|----------|-----------|------|
| 10 | lens-trace | after_task |
| 20 | lens-drift | after_task |

Lower number runs first. lens-trace always runs before lens-drift.

---

## Repository Structure

```
speckit-lens/
  extensions/
    lens-trace/
      extension.yml
      spec.md
      commands/
        trace.md
        dashboard.md
      scripts/
        dashboard.py      # uv inline — stdlib only
    lens-drift/
      extension.yml
      spec.md
      commands/
        drift.md
    lens-humanize/
      extension.yml
      spec.md
      commands/
        humanize.md
    lens-compress/
      extension.yml
      spec.md
      commands/
        compress.md
    lens-contract/
      extension.yml
      spec.md
      commands/
        contract.md
    lens-probe/
      extension.yml
      spec.md
      commands/
        probe.md
  catalog.community.json
  README.md
  CONTRIBUTING.md
  LICENSE
```

---

## Roadmap

- [x] `lens-trace` v0.1 — task execution visibility + HTML dashboard
- [x] `lens-drift` v0.1 — per-task spec adherence guard (EARS-aware)
- [x] `lens-humanize` v0.1 — human-readable plan translation
- [ ] `lens-compress` v0.1 — artifact compression
- [x] `lens-contract` v0.1 — conversational contract generation
- [ ] `lens-probe` v0.1 — ADK runtime output validation
- [ ] Acceptance verification pass (trace, drift, humanize, contract)
- [ ] Community catalog submission (spec-kit/extensions/catalog.community.json)

---

## Contributing

Contributions welcome. If you're hitting speckit pain points not covered here, open an issue with the failure mode — not just the feature request.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and extension authoring guidelines.

---

## License

MIT
