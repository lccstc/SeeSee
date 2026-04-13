# Features Research

## Table Stakes

These are mandatory for a trustworthy supplier quote wall.

### Evidence & Traceability

- Every published row links back to raw message, source line, sender, group, and time
- Operators can inspect the original raw text behind any active quote

### Candidate Safety

- Parsers only generate candidates
- Invalid candidates never reach active facts
- Failed parsing does not destroy prior valid wall state

### Exception Operations

- Every failure enters an exception pool
- Operators can replay the original message
- Operators can fix templates or rules and verify replay result before accepting

### Fact Protection

- Only a single publish path can mutate active quote facts
- Snapshot/delta semantics are explicit
- Default behavior is conservative

## Differentiators

These would make this system materially stronger than a generic parser tool.

### Industrialization Loop

- Promote repeated failures into:
  - templates
  - deterministic rules
  - scripts
  - skills
  - unit tests

### Publish Auditability

- Every publish decision records:
  - why rows were publishable
  - why other rows were rejected
  - why old active rows stayed untouched or were inactivated

### Human-in-the-Loop Snapshot Typing

- In v1, the system proposes `full_snapshot` vs `delta_update`
- You confirm during debugging
- Later versions can automate only where evidence is strong

## Anti-Features

These should be deliberately avoided.

| Anti-Feature | Why It Is Dangerous |
|--------------|---------------------|
| Model directly decides publish result | Turns prompt behavior into business authority |
| Clear old active when current parse fails | Converts one bad message into wall corruption |
| Default full overwrite | High chance of deleting valid unseen SKUs |
| Prompt-only business rules | Not testable, not enforceable, not auditable |
| Manual review of every line forever | Doesn't scale and blocks industrialization |

## Dependencies Between Features

- Candidate safety depends on explicit validator and publisher boundaries
- Fact protection depends on snapshot/delta classification
- Exception industrialization depends on replay and persistent failure records
- Production trust depends on all four layers working together, not on parser quality alone

## Complexity Notes

- Low complexity:
  - adding explicit publish state machine concepts to docs and tests
  - surfacing richer rejection reasons in exception flows
- Medium complexity:
  - formalizing candidate objects and publishable rows
  - wiring snapshot/delta semantics into publish behavior
- Higher complexity:
  - proving replay stability across templates, validators, and publish decisions on large real-world sample sets
