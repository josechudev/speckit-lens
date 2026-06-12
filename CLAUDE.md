# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

speckit-lens is a suite of six speckit extensions that add human-facing observability, contract tooling, and plan readability on top of [spec-kit](https://github.com/github/spec-kit) workflows. Extensions are independent but designed to work together.

## Development

No build step. Extensions are YAML + Markdown (and optionally Python scripts).

Test an extension locally against a speckit project:

```bash
cd /your/speckit/project
specify extension add lens-trace --from /path/to/speckit-lens/extensions/lens-trace

# Or via zip
zip -r lens-trace.zip extensions/lens-trace
specify extension add lens-trace --from ./lens-trace.zip
```

For extensions with Python scripts (e.g. `lens-trace`), run directly with uv:

```bash
cd /your/speckit/project
uv run /path/to/speckit-lens/extensions/lens-trace/scripts/trace.py
```

## Extension structure

Each extension lives under `extensions/<id>/`:

```
extensions/<id>/
  extension.yml       # manifest — id, version, hooks, commands
  spec.md             # behavioral spec for the extension
  commands/
    <cmd>.md          # one file per command: YAML frontmatter + agent instruction body
  scripts/            # optional Python scripts (uv inline script format)
    <cmd>.py
```

`extension.yml` key fields:

| Field | Constraint |
|---|---|
| `extension.id` | Lowercase, hyphens only. Must be unique in the catalog. |
| `provides.commands[].name` | Must be in the `speckit.lens.*` namespace. |
| `hooks.<event>.optional` | Set `true` for all lens hooks — they are informational only. |

Available hook events: `before_specify`, `after_specify`, `before_plan`, `after_plan`, `before_tasks`, `after_tasks`, `before_implement`, `after_implement`, `after_task`, `before_analyze`, `after_analyze`.

## Command `.md` files

Commands are read by Claude as agent instructions — not executed as shell scripts. Key rules:

- Frontmatter: `description` (required), `tools: []` (optional MCP deps)
- Use `$ARGUMENTS` where user-supplied flags belong
- Declare output format explicitly so output is consistent across runs
- Never modify files without user consent; always back up before overwriting
- Prefer printing a structured report over silent pass

## Python scripts (uv inline format)

Scripts use uv's inline script metadata — no separate `pyproject.toml` needed:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
```

Scripts are invoked by speckit via the hook's command field. The hook injects `SPECKIT_TASK_ID` (and other context) as env vars before invocation.

## Extension pairs

- `lens-trace` + `lens-drift` — both run `after_task`; trace runs first (lower priority), drift second
- `lens-contract` + `lens-probe` — contract generates `.specify/contracts/` files; probe validates runtime output against them

## Catalog

`catalog.community.json` at the root mirrors the catalog entry format for spec-kit community submission. Update it whenever a new extension is added or version bumps.

## Adding a new extension

1. Copy `extensions/lens-trace/` as a template
2. Update `extension.yml` — new ID, description, hooks, command name
3. Write `commands/<cmd>.md` — full agent instruction
4. Write `spec.md` — behavioral spec (problem, inputs, outputs, edge cases, constraints)
5. Add entry to `catalog.community.json`
