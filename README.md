# speckit-lens

> Human-facing visibility and contract tooling for [spec-kit](https://github.com/github/spec-kit) workflows.

speckit-lens is a suite of six extensions that address the parts of spec-driven development that speckit leaves opaque: plan readability, execution tracing, spec drift, token cost, and runtime contract validation. Each extension is independent and installable separately, but they are designed to work together as a cohesive layer on top of a standard speckit setup.

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

Surfaces what speckit is doing inside `implement` in real time: which task is running, what files it intends to modify, and a summary of what changed before the next task begins.

```
/speckit.lens.trace
```

**Solves:** Black-box `implement` runs where the only feedback is file changes after the fact.

---

### `lens-drift` — Per-Task Spec Adherence Guard

After each task in the `implement` loop, diffs the generated code against the spec section mapped to that task. Scores adherence, flags violations with contract line references, and optionally injects a correction prompt before the next task runs.

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

Applies caveman-style semantic compression to speckit artifacts (`spec.md`, `plan.md`, `tasks.md`) before `implement` runs, reducing context token consumption without losing semantic content. Originals are backed up before compression.

```
/speckit.lens.compress
```

**Solves:** Excessive token consumption during `implement` caused by full artifact re-reads on every turn.

---

### `lens-contract` — Conversational Contract Generation

Accepts an OpenAPI spec or base JSON schema as input, asks targeted questions about expected runtime behavior (cardinality, required fields, attachment rules, event ordering), and generates a structured contract file in `.specify/contracts/`. Runs as a `before_implement` hook so contracts exist before code is written.

```
/speckit.lens.contract --from openapi.yaml
```

**Solves:** Contract generation being too tedious to do manually, leading to skipped contracts and unvalidatable runtime behavior.

---

### `lens-probe` — Runtime Output Validation

Accepts raw ADK response stream JSON and validates it against a contract in `.specify/contracts/`. Reports violations with event index, rule reference, and what was found versus what the contract expects.

```
/speckit.lens.probe --input stream.json --contract contracts/api.md
```

**Solves:** No path to bring Postman/runtime output evidence back into speckit for contract validation. Drift that is only visible when you're manually reading a response log.

---

## Extension Pairs

`lens-contract` and `lens-probe` are designed as a pair: one generates the contract from your schema, the other validates runtime output against it. `lens-drift` and `lens-trace` are designed to run together during `implement`: trace surfaces what's happening, drift validates that what happened matches the spec.

---

## Installation

Each extension is installable independently via the speckit extensions catalog or directly from this repo:

```bash
# Install the full suite
speckit extensions install https://github.com/<your-handle>/speckit-lens/archive/refs/tags/v0.1.0.zip

# Or install individually (once per-extension zip releases are available)
speckit extensions install lens-trace
speckit extensions install lens-drift
speckit extensions install lens-humanize
speckit extensions install lens-compress
speckit extensions install lens-contract
speckit extensions install lens-probe
```

Requires speckit `>=0.9.1` (hooks stable from this version).

---

## Repository Structure

```
speckit-lens/
  extensions/
    lens-trace/
      extension.yml
      commands/
        trace.md
    lens-drift/
      extension.yml
      commands/
        drift.md
    lens-humanize/
      extension.yml
      commands/
        humanize.md
    lens-compress/
      extension.yml
      commands/
        compress.md
    lens-contract/
      extension.yml
      commands/
        contract.md
    lens-probe/
      extension.yml
      commands/
        probe.md
  README.md
  CONTRIBUTING.md
  LICENSE
```

---

## Roadmap

- [ ] `lens-trace` v0.1 — task execution visibility
- [ ] `lens-drift` v0.1 — per-task spec adherence guard
- [ ] `lens-humanize` v0.1 — human-readable plan translation
- [ ] `lens-compress` v0.1 — artifact compression
- [ ] `lens-contract` v0.1 — conversational contract generation
- [ ] `lens-probe` v0.1 — ADK runtime output validation
- [ ] Community catalog submission (spec-kit/extensions/catalog.community.json)

---

## Contributing

Contributions welcome. If you're hitting speckit pain points not covered here, open an issue with the failure mode — not just the feature request.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and extension authoring guidelines.

---

## License

MIT