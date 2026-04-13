# Architecture Research

## Recommended Component Model

### 1. Raw Message Ledger

Input:

- immutable supplier group message

Responsibilities:

- preserve original evidence
- associate message with chat, sender, platform, timestamp

Existing fit:

- current incoming message storage and runtime ingestion already cover much of this

### 2. Candidate Builder

Input:

- raw message
- current group template
- dictionaries / normalization rules
- optional local heuristics or model-assisted helpers

Output:

- candidate rows
- candidate classification hints
- structured rejection reasons for lines that failed early

Rule:

- no direct write to active quote facts

### 3. Validator

Input:

- candidates from builder

Validation stages:

1. schema validation
2. normalization validation
3. business rule validation
4. snapshot/delta safety validation
5. publishability decision

Output:

- `publishable_rows`
- `rejected_rows`
- message-level decision

### 4. Publisher

Input:

- source message identity
- validated publishable rows
- confirmed or inferred message type

Responsibilities:

- apply active updates safely
- never clear old active on failure
- only inactivate unseen rows when message is explicitly confirmed as `full_snapshot`
- record publish audit details

### 5. Exception / Replay Workbench

Input:

- failures from candidate builder, validator, or publisher

Responsibilities:

- exception pooling
- replay current rules on stored evidence
- manual classification help in v1
- export repeatable fixes into tests and rules

## Suggested Build Order

1. Introduce explicit candidate and publishability concepts
2. Introduce validator boundary and rejection taxonomy
3. Introduce publisher with hard fact-protection semantics
4. Thread snapshot/delta classification through the publish path
5. Upgrade exception + replay loop to support industrialization
6. Add regression suites from real samples

## Boundaries To Preserve

- Finance and settlement stay separate
- Adapters stay thin
- UI does not get authority to bypass publisher
- Template management remains an operator tool, not the final rule engine by itself

## Architectural Risk To Avoid

The largest mistake would be to keep parsing, validation, and publishing blurred together in one implicit flow. If those boundaries remain fuzzy, the system will always be one helper function away from accidental direct publication.
