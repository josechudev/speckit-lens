# Spec: lens-contract

## Problem

Writing runtime contracts by hand is tedious, so engineers skip them. When contracts don't exist before implementation, runtime behavior is never validated — drift between spec and runtime is only discovered in production or through manual log inspection.

lens-contract removes the friction: it reads an existing schema and asks targeted questions to elicit the behavioral rules the schema can't express.

## Role in the suite

lens-contract runs as a `before_implement` hook (or standalone). It generates a contract file in `.specify/contracts/` that lens-probe uses for runtime validation.

## Inputs

- A schema file passed via `--from <path>`: OpenAPI 3.x (YAML or JSON) or JSON Schema
- Optional: `--name <contract-name>` to control the output filename
- Optional: existing `.specify/contracts/` files (checked for conflicts)

## Outputs

- A contract file at `.specify/contracts/<name>.md`
- Stdout confirmation with rule count

## Behavior

### Schema loading

lens-contract must support:
- OpenAPI 3.x in YAML format (`.yaml`, `.yml`)
- OpenAPI 3.x in JSON format (`.json`)
- JSON Schema (`.json`, `.schema.json`)
- Markdown files with API shapes described in fenced code blocks (best-effort extraction)

If the file cannot be parsed, print a specific parse error and exit.

### Surface area extraction

From the schema, lens-contract must extract and catalog:
- All endpoints / operations (for OpenAPI): method, path, request body, response shapes per status code
- All response object fields: name, type, required/optional
- All enum fields and their values
- Nested objects and arrays
- `oneOf` / `anyOf` / `allOf` variants and their discriminators

### Targeted Q&A

lens-contract must ask targeted questions to capture behavioral rules the schema cannot express. Questions must cover these categories:

**Cardinality:**
- Minimum and maximum lengths for array fields
- Whether optional fields are genuinely nullable in practice vs. always present

**Ordering (for streaming/ADK responses):**
- Whether event types have a required sequence
- Whether any event type can appear multiple times

**Invariants:**
- Field co-presence rules (field A is always present when field B is non-null)
- Mutually exclusive field combinations

**Error surface:**
- Which HTTP status codes and error shapes are contract-validated
- Whether a 200 with an empty body is a violation

**Limits:**
- Ask no more than 8 questions total
- Group related questions to reduce back-and-forth
- Stop asking when sufficient rules have been collected to write a useful contract

Questions must be specific to the schema being analyzed — no generic questions. Each question must reference a field name or operation from the schema.

### Contract file format

Output a structured Markdown file:

```markdown
# Contract: <name>
Generated: <ISO date>
Source: <schema path>
speckit-lens: lens-contract v0.1.0

## <METHOD> <path> — <status code>

### Response shape

| Field | Type | Required | Rule |
|-------|------|----------|------|

### Cardinality
- `<field>`: min <N>, max <N | unbounded>

### Ordering
- <event type A> must precede <event type B>
- <event type C> may repeat

### Invariants
- `<field A>` always present when `<field B>` is non-null
- `<field C>` and `<field D>` are mutually exclusive

### Violations
- <status> with <shape> → violation
- Missing required field `<name>` → violation
```

### Output path

Default: `.specify/contracts/<schema-basename>.md`  
With `--name`: `.specify/contracts/<name>.md`

Create `.specify/contracts/` if it does not exist.

If the target file already exists, prompt: "Contract already exists. Overwrite? [y/N]". Default to no on non-interactive runs.

## Constraints

- Must not generate rules that cannot be validated from a response payload alone
- Must not modify the source schema file
- Must produce valid Markdown
- Must label generated rules as machine-checkable vs. informational

## Integration

- Output consumed by lens-probe for runtime validation
- Contract file must be readable by lens-probe without modification
- Runs `before_implement` alongside lens-compress; order is user-configured
- Does not depend on spec.md, plan.md, or tasks.md

## Open questions

- Should lens-contract support re-running to add rules to an existing contract (append mode)?
- Should it support multiple schema files in a single run (`--from a.yaml --from b.yaml`)?
- Should non-interactive mode skip the Q&A entirely and generate a minimal contract from the schema alone?
- How to handle OpenAPI specs with `$ref` chains — inline references or resolve them?
