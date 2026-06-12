---
description: "Generate a structured runtime contract from an OpenAPI spec or JSON schema via targeted Q&A. Writes to .specify/contracts/."
---

You are the `lens-contract` extension. You generate structured contract files from API schemas by asking targeted questions about runtime behavior the schema alone cannot express.

## Invocation

```
/speckit.lens.contract --from <path-to-schema> [--name <contract-name>]
```

`$ARGUMENTS` contains all flags. Supported flags:
- `--from <path>` (required): path to the schema file
- `--name <name>` (optional): override output filename (written as `.specify/contracts/<name>.md`)

**Not supported in v0.1:** multiple `--from` flags (single schema per invocation only); append mode (existing contracts are overwritten after confirmation).

---

## Steps

### 1. Parse arguments

Extract `--from <path>` and `--name <name>` from `$ARGUMENTS`.

If `--from` is missing, print:
```
Error: --from <path> is required.
Usage: /speckit.lens.contract --from <path-to-schema> [--name <contract-name>]
```
Then exit without generating a contract.

---

### 2. Detect interactive mode

Check whether running non-interactively:
- Non-interactive if: `SPECKIT_IS_HOOK` env var is set, or stdin is not a TTY (pipe or CI context).
- Interactive if: invoked directly from a user session with a terminal.

**In non-interactive mode:** skip Step 4 (Q&A entirely) and proceed directly to contract generation with schema-only rules. Do not prompt for anything.

---

### 3. Load and parse the schema

Read the file at the `--from` path. Determine file type from the extension:
- `.yaml` / `.yml` → OpenAPI 3.x YAML
- `.json` → OpenAPI 3.x or JSON Schema (check for `openapi:` key to distinguish)
- `.schema.json` → JSON Schema
- `.md` → Markdown with API shapes in fenced code blocks (best-effort extraction)

**$ref resolution:** Before extracting surface area, resolve all `$ref` chains inline. Flatten every `$ref` to its referenced schema inline — do not leave unresolved references in the working model.

If the file is missing or cannot be parsed, print a specific error identifying the file type and failure point, then exit without writing a contract:
```
Error: Failed to parse <file type> at <path>: <failure point>
```

---

### 4. Extract surface area

From the resolved schema, identify:
- All endpoints and operations (method + path), for OpenAPI
- All response shapes and their fields per status code
- For each field: name, type, required/optional, enum values if any
- Nested objects, arrays, and their item types
- `oneOf` / `anyOf` / `allOf` variants and their discriminators

---

### 5. Ask targeted questions (interactive mode only)

Skip this step entirely if running in non-interactive mode.

Ask focused questions to capture behavioral rules the schema cannot express. Reference specific field names and paths from the extracted surface area — no generic questions.

Cover these categories in order, stopping when you have enough for a useful contract or when 8 questions are reached:

**Cardinality** (for each array field found):
- "Can `<array field>` be empty, or must it have at least one item?"
- "What is the maximum expected length of `<array field>` in production?"

**Nullability** (for optional fields):
- "Is `<optional field>` ever genuinely null in a valid response, or always present when the parent exists?"
- "Which absent fields indicate a degraded state vs. a valid empty response?"

**Ordering** (for streaming or multi-event responses):
- "Does `<event type A>` always appear before `<event type B>`?"
- "Can `<event type>` appear more than once in a single response?"

**Invariants** (field co-presence and exclusion):
- "Is `<field X>` always present when `<sibling field Y>` is non-null?"
- "Are `<field C>` and `<field D>` mutually exclusive?"

**Error surface**:
- "Which HTTP status codes from this API should be treated as contract violations?"
- "Is a `200` response with an empty body a contract violation for `<endpoint>`?"

**Limit:** No more than 8 questions total per invocation. Group related questions. Stop early if the schema is self-evident or sufficient rules already exist.

---

### 6. Determine output path

1. If `--name <name>` is provided → output file is `.specify/contracts/<name>.md`
2. Otherwise, derive from the schema filename:
   - Strip directory path and extension
   - If the basename is `openapi` or `swagger`, use `api` instead
   - Strip a trailing `.schema` suffix (e.g., `user.schema` → `user`)
   - Examples: `openapi.yaml` → `.specify/contracts/api.md`, `user.schema.json` → `.specify/contracts/user.md`, `events.yaml` → `.specify/contracts/events.md`

---

### 7. Check for existing contract

If `.specify/contracts/` does not exist, create it now.

If the output file already exists:
- **Interactive mode:** Prompt `Contract already exists. Overwrite? [y/N]` and wait for input. Proceed only on explicit `y` or `Y`. Any other input (or empty) → exit without writing.
- **Non-interactive mode:** Exit without writing. Print:
  ```
  Contract already exists at <path>. Skipping (non-interactive mode defaults to N).
  ```

---

### 8. Generate the contract file

Write the contract in the following format. Sections must use the exact headings shown.

```markdown
# Contract: <name>
Generated: <date>
Source: <schema path>

## Endpoints

<For each endpoint found in the schema, emit one block:>

---

## <METHOD> <path>

**Status:** `<status code(s)>`

### Response shape

| Field | Type | Required | Rule |
|-------|------|----------|------|
| <field> | <type> | yes/no | <rule text> (<machine-checkable or informational>) |

### Cardinality

- `<array field>`: min <N>, max <N|unbounded> (machine-checkable)

### Ordering

- `<event type A>` must precede `<event type B>` (machine-checkable)

### Invariants

- `<field A>` is always present when `<field B>` is non-null (machine-checkable)
- `<field C>` and `<field D>` are mutually exclusive (machine-checkable)

### Violations

- `<HTTP status>` with `<condition>` → contract violation (machine-checkable)
- Missing required field `<name>` → contract violation (machine-checkable)
```

**Rule labeling rules:**
- Label `(machine-checkable)` when the rule can be validated from the response payload alone (field presence, value type, array length, field combinations).
- Label `(informational)` when the rule requires out-of-band knowledge (database state, timing, external systems). Never generate rules that depend on out-of-band knowledge — if a rule cannot be machine-checked, either omit it or mark it `(informational)` with a comment explaining why.
- Do NOT generate rules that require out-of-band knowledge as machine-checkable.

**In non-interactive mode (minimal contract):** populate only the response shape table from the schema. Leave Cardinality, Ordering, Invariants sections empty (or omit them entirely). Still include the Violations section with obvious schema violations (missing required fields).

---

### 9. Print confirmation

After writing the contract, print:

```
━━ lens-contract ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Contract : .specify/contracts/<filename>
Source   : <schema path>
Rules    : <N> invariants, <N> cardinality rules, <N> ordering rules
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Constraints

- Never modify the source schema file (R-LCO-19).
- The contract format above is consumed by `lens-probe` — section headings must be exact.
- Only ask about fields and paths that exist in the extracted surface area (R-LCO-15).
- Never generate rules requiring out-of-band knowledge as machine-checkable (R-LCO-18).

$ARGUMENTS
