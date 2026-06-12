# Spec: lens-contract

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

Writing runtime contracts by hand is tedious, so engineers skip them. When contracts don't exist before implementation, runtime behavior is never validated — drift between spec and runtime is only discovered in production or through manual log inspection.

lens-contract removes the friction: reads an existing schema, asks targeted questions to elicit behavioral rules the schema can't express, then generates a structured contract file.

## Role in the suite

Runs as `before_implement` hook (or standalone). Generates a contract file in `.specify/contracts/` that lens-probe uses for runtime validation.

## Inputs

- `--from <path>`: OpenAPI 3.x (YAML or JSON) or JSON Schema file
- `--name <contract-name>` (optional): controls output filename
- Existing `.specify/contracts/` files (checked for conflicts)

## Outputs

- `.specify/contracts/<name>.md` — structured contract file
- Stdout confirmation with rule count

---

## Requirements

### Schema loading

**R-LCO-01:** WHEN invoked with `--from <path>`, `lens-contract` SHALL load and parse the schema file at that path.

**R-LCO-02:** `lens-contract` SHALL support OpenAPI 3.x in YAML format (`.yaml`, `.yml`).

**R-LCO-03:** `lens-contract` SHALL support OpenAPI 3.x in JSON format (`.json`).

**R-LCO-04:** `lens-contract` SHALL support JSON Schema files (`.json`, `.schema.json`).

**R-LCO-05:** `lens-contract` SHALL support Markdown files with API shapes described in fenced code blocks, using best-effort extraction.

**R-LCO-06:** IF the schema file cannot be parsed, THEN `lens-contract` SHALL print a specific parse error identifying the file type and failure point, and SHALL exit without generating a contract.

### Surface area extraction

**R-LCO-07:** WHEN parsing an OpenAPI schema, `lens-contract` SHALL extract all endpoints (method + path), request bodies, and response shapes per status code.

**R-LCO-08:** WHEN parsing any schema, `lens-contract` SHALL extract all response object fields including name, type, and required/optional status.

**R-LCO-09:** WHEN parsing any schema, `lens-contract` SHALL extract all enum fields and their enumerated values.

**R-LCO-10:** WHEN parsing any schema, `lens-contract` SHALL extract nested objects, arrays, and any `oneOf` / `anyOf` / `allOf` variants with their discriminators.

### Targeted Q&A

**R-LCO-11:** WHEN the schema surface area has been extracted, `lens-contract` SHALL ask the engineer targeted questions to capture behavioral rules the schema cannot express.

**R-LCO-12:** WHEN asking questions, `lens-contract` SHALL cover at minimum: cardinality for array fields, nullability of optional fields, event ordering for streaming responses, field invariants (co-presence and mutual exclusion), and error surface (status codes and empty-body violations).

**R-LCO-13:** `lens-contract` SHALL ask no more than 8 questions total per invocation.

**R-LCO-14:** `lens-contract` SHALL group related questions to reduce back-and-forth, and SHALL stop asking when sufficient rules exist to write a useful contract.

**R-LCO-15:** WHEN formulating questions, `lens-contract` SHALL reference specific field names or operation paths from the schema — no generic questions.

### Contract file format

**R-LCO-16:** WHEN generating a contract, `lens-contract` SHALL write a Markdown file with sections for: response shape table (field/type/required/rule), cardinality rules, ordering rules, invariants, and violation conditions.

**R-LCO-17:** `lens-contract` SHALL label each generated rule as either machine-checkable (validatable from a response payload) or informational.

**R-LCO-18:** `lens-contract` SHALL NOT generate rules that cannot be validated from a response payload alone.

**R-LCO-19:** `lens-contract` SHALL NOT modify the source schema file.

### Output path

**R-LCO-20:** WHEN `--name <contract-name>` is not provided, `lens-contract` SHALL derive the output filename from the schema basename (e.g., `openapi.yaml` → `.specify/contracts/api.md`).

**R-LCO-21:** WHEN `--name <contract-name>` is provided, `lens-contract` SHALL write to `.specify/contracts/<name>.md`.

**R-LCO-22:** IF `.specify/contracts/` does not exist, THEN `lens-contract` SHALL create it before writing.

**R-LCO-23:** IF the target contract file already exists, THEN `lens-contract` SHALL prompt `Contract already exists. Overwrite? [y/N]` before writing.

**R-LCO-24:** WHILE running in a non-interactive environment, `lens-contract` SHALL default to `N` (no overwrite) without prompting.

**R-LCO-25:** WHEN `lens-contract` completes, it SHALL print a stdout confirmation showing the output path and counts of invariants, cardinality rules, and ordering rules generated.

---

## Integration

- Output consumed by lens-probe for runtime validation; contract format must be stable and compatible
- Runs `before_implement` alongside lens-compress; execution order is user-configured
- Does not depend on `spec.md`, `plan.md`, or `tasks.md`

## Open questions

- Should lens-contract support append mode to add rules to an existing contract without overwriting?
- Should multiple schema files be supported in a single run (`--from a.yaml --from b.yaml`)?
- Should non-interactive mode skip Q&A entirely and generate a minimal schema-only contract?
- How to handle OpenAPI specs with `$ref` chains — inline or resolve references?

---

## Acceptance

Evaluatable test cases derived directly from requirements above.

- [ ] **R-LCO-01/02:** Running `--from openapi.yaml` with a valid OpenAPI 3.x YAML file succeeds and produces a contract
- [ ] **R-LCO-06:** Running `--from broken.yaml` on a malformed file prints a specific parse error; no contract written
- [ ] **R-LCO-07:** Contract for an OpenAPI file lists all endpoint operations found in the spec
- [ ] **R-LCO-08:** Response shape table contains all required and optional fields from the schema
- [ ] **R-LCO-13:** No more than 8 questions appear in a single run
- [ ] **R-LCO-15:** Every question references at least one field name or path from the schema
- [ ] **R-LCO-17:** Each rule in the contract is labeled "machine-checkable" or "informational"
- [ ] **R-LCO-18:** No rule requires out-of-band knowledge (e.g., database state) to validate
- [ ] **R-LCO-19:** Source schema file is byte-for-byte identical before and after run
- [ ] **R-LCO-20:** `openapi.yaml` → contract written to `.specify/contracts/api.md`
- [ ] **R-LCO-22:** If `.specify/contracts/` absent, it is created; contract written successfully
- [ ] **R-LCO-23:** If contract file already exists, prompt appears before overwrite
- [ ] **R-LCO-24:** In non-interactive mode, existing contract is not overwritten (no prompt, default N)
- [ ] **R-LCO-25:** Stdout shows output path, invariant count, cardinality rule count, ordering rule count
