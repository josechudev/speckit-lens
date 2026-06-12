---
description: "Validate a raw ADK response stream JSON file against a contract in .specify/contracts/. Report violations with event index and rule reference."
---

You are the `lens-probe` extension. You validate runtime ADK output against a speckit contract.

## Invocation

```
/speckit.lens.probe --input <stream.json> --contract <contracts/api.md>
```

`$ARGUMENTS` contains `--input` and `--contract` paths.

## Steps

### 1. Parse arguments

Extract from `$ARGUMENTS`:
- `--input <path>`: path to the ADK response stream JSON file
- `--contract <path>`: path to the contract markdown file (relative to `.specify/` or absolute)

If either is missing, print usage and exit:
```
Usage: /speckit.lens.probe --input <stream.json> --contract <contracts/api.md>
```

### 2. Load the stream

Read the `--input` file. Expect a JSON array of ADK event objects, or a newline-delimited JSON stream (NDJSON). Parse into an ordered list of events.

If the file is empty or unparseable, report the parse error and exit.

### 3. Load the contract

Read the `--contract` file from `.specify/` (prepend `.specify/` if the path doesn't start with `/` or `.specify/`).

Parse the contract sections:
- Response shape table (field, type, required, rule)
- Cardinality rules
- Ordering rules
- Invariants
- Violation conditions

### 4. Validate

For each contract rule, check it against the stream:

**Required field check:**
For each event of the relevant type, verify all `Required: yes` fields are present and non-null.

**Cardinality check:**
For array fields, count items and verify against `min`/`max` bounds.

**Ordering check:**
Walk the event list and verify ordering rules (e.g., event type A appears before event type B).

**Invariant check:**
For each event, verify field co-presence and mutual exclusion rules.

**Violation condition check:**
Check for any status code / shape combinations explicitly listed as violations.

### 5. Print the probe report

```
━━ lens-probe ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input    : <stream file>
Contract : <contract file>
Events   : <N> parsed
─────────────────────────────────────────────────────────────
VIOLATIONS (<N>):

  [event #<idx>] <event type>
  Rule    : <contract section> — "<rule text>"
  Found   : <what was in the event>
  Expected: <what the contract requires>

WARNINGS (<N>):
  [event #<idx>] <description of ambiguous or near-miss>

PASSED : <N>/<total> rules
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If all rules pass:
```
━━ lens-probe ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All <N> rules passed. No violations detected.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6. Optional: write probe log

If `--output <path>` is passed in `$ARGUMENTS`, write the full probe report as Markdown to the specified path.

## Notes

- Event index is 0-based to match array positions for easy scripting.
- Treat unrecognized event types as a warning, not a violation.
- If the contract has no rules for an event type present in the stream, note it as "uncovered" but do not fail.

$ARGUMENTS
