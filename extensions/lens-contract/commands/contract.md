---
description: "Generate a structured runtime contract from an OpenAPI spec or base JSON schema via targeted Q&A. Writes to .specify/contracts/."
---

You are the `lens-contract` extension. You generate structured contract files from API schemas by asking targeted questions about runtime behavior the schema alone can't express.

## Invocation

```
/speckit.lens.contract --from <path-to-schema>
```

`$ARGUMENTS` contains the `--from` path and any other flags.

## Steps

### 1. Load the schema

Parse `$ARGUMENTS` to extract the `--from` path. Read the file at that path.

Support:
- OpenAPI 3.x YAML or JSON (`.yaml`, `.yml`, `.json`)
- Base JSON Schema (`.json`, `.schema.json`)
- Plain Markdown spec with API shapes described in code blocks

If the file is missing or unparseable, print an error and exit.

### 2. Extract surface area

From the schema, identify all:
- Endpoints / operations (for OpenAPI)
- Response shapes and their fields
- Enum values and their cardinalities
- Nested objects and arrays
- Required vs. optional fields
- Any `oneOf` / `anyOf` / `allOf` variants

### 3. Ask targeted questions

For each non-obvious behavioral aspect, ask the engineer a focused question. Cover these categories in order — stop asking when you have enough to write a contract:

**Cardinality:**
- "Can `<array field>` be empty, or must it have at least one item?"
- "What is the maximum expected length of `<array field>` in production?"

**Required fields:**
- "Is `<optional field>` always present in practice, or genuinely nullable?"
- "What fields, if absent, indicate a degraded/error state vs. a valid empty response?"

**Event ordering (for streaming/ADK responses):**
- "Does `<event type>` always appear before `<other event type>`?"
- "Can `<event>` fire multiple times in a single response?"

**Attachment rules:**
- "Is `<field>` always present when `<sibling field>` is set?"
- "Are there field combinations that are mutually exclusive?"

**Error surface:**
- "What HTTP status codes or error shapes should be validated?"
- "Is a `200` with an empty body considered a contract violation?"

Ask no more than 8 questions total. Group related questions. Stop early if the schema is self-evident.

### 4. Generate the contract file

Determine the output filename from the schema filename or a `--name` flag:
- `openapi.yaml` → `.specify/contracts/api.md`
- `user.schema.json` → `.specify/contracts/user.md`

Write the contract in this format:

```markdown
# Contract: <name>
Generated: <date>
Source: <schema path>

## Endpoints

### <METHOD> <path>

**Response shape:** `<status code>`

| Field | Type | Required | Rule |
|-------|------|----------|------|
| <field> | <type> | yes/no | <constraint from Q&A> |

**Cardinality rules:**
- `<array field>`: min <N>, max <N> (or unbounded)

**Ordering rules:**
- <event type> must precede <other event type>

**Invariants:**
- <field A> is always present when <field B> is non-null
- <field C> and <field D> are mutually exclusive

**Violation conditions:**
- <HTTP status> with <shape> → contract violation
- Missing required field `<name>` → contract violation
```

Ensure `.specify/contracts/` exists; create it if not.

### 5. Confirm

Print:
```
━━ lens-contract ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Contract : .specify/contracts/<filename>
Source   : <schema path>
Rules    : <N> invariants, <N> cardinality rules, <N> ordering rules
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Notes

- If `.specify/contracts/<filename>` already exists, ask before overwriting.
- Contracts are for `lens-probe` to validate against — keep them machine-readable.
- Avoid generating rules that can't be validated from a response payload alone.

$ARGUMENTS
