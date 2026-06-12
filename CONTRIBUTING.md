# Contributing to speckit-lens

## Dev setup

```bash
git clone https://github.com/josechudev/speckit-lens
cd speckit-lens
```

No build step. Extensions are YAML + Markdown.

To test an extension locally against a speckit project:

```bash
cd /your/speckit/project
specify extension add lens-trace --from /path/to/speckit-lens/extensions/lens-trace
```

Or install from a local zip:

```bash
zip -r lens-trace.zip extensions/lens-trace
specify extension add lens-trace --from ./lens-trace.zip
```

Requires speckit `>=0.9.1`.

---

## Extension authoring

Each extension lives under `extensions/<id>/` and contains:

```
extensions/<id>/
  extension.yml       # manifest — id, version, hooks, commands
  commands/
    <cmd>.md          # one file per command, YAML frontmatter + prompt body
```

### extension.yml

Follow the schema in `extensions/lens-trace/extension.yml` as a reference. Key fields:

| Field | Notes |
|-------|-------|
| `extension.id` | Lowercase, hyphens only. Must be unique in the catalog. |
| `extension.version` | Semver. Bump on every catalog submission. |
| `requires.speckit_version` | Set to the minimum version that supports the hooks you use. |
| `provides.commands[].name` | `speckit.lens.<cmd>` — must stay in the `lens` namespace for this suite. |
| `hooks.<event>.optional` | Set `true` unless the hook must run for correctness. Most lens hooks are optional. |

Available hook events: `before_specify`, `after_specify`, `before_plan`, `after_plan`, `before_tasks`, `after_tasks`, `before_implement`, `after_implement`, `after_task`, `before_analyze`, `after_analyze`.

### command .md files

Frontmatter:

```yaml
---
description: "One line. Shown in `specify extension info`."
tools: []   # optional: MCP tool dependencies
---
```

Body: plain instruction prose. Use `$ARGUMENTS` where user-supplied flags belong.

Design principles:
- Commands are read by Claude, not executed as shell scripts. Write them as clear agent instructions.
- Commands must declare their output format explicitly so output is consistent across runs.
- Never modify files the user hasn't consented to modify. Always back up before overwriting.
- Prefer printing a structured report over silently passing.

---

## Adding a new extension to this suite

1. Copy `extensions/lens-trace/` as a template
2. Update `extension.yml` with the new ID, description, hooks, and command name
3. Write `commands/<cmd>.md` — the full agent instruction for the command
4. Add an entry to `catalog.community.json` at the root
5. Open a PR with the failure mode this extension solves in the PR description

---

## Catalog submission

To submit to the spec-kit community catalog, open a PR on `github/spec-kit` adding your entry to `extensions/catalog.community.json`. Maintainers verify format only — they do not audit extension logic.

---

## Versioning

- `0.x.y` — pre-stable. Breaking changes allowed between minors.
- `1.0.0` — stable API. Breaking changes require a major bump.
- All six extensions share the same version cadence until `1.0.0`.
