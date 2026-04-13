# Pitfalls Research

## Pitfall 1: Treating Parser Output as Fact

### Why It Happens

In brownfield systems, parse output often gets written to active tables because that is the fastest path.

### Warning Signs

- parser functions return rows that are immediately persisted
- there is no publish gate with explicit rejection reasons
- UI or scripts can bypass the same path

### Prevention

- separate candidate generation from publishing
- require `publishable_rows`
- ensure only one publisher mutates active facts

### Phase Mapping

- Must be addressed in early foundation phases

## Pitfall 2: Clearing Old Facts On Partial Failure

### Why It Happens

Teams implicitly assume each new message is a complete replacement of current truth.

### Warning Signs

- parse failure causes rows to disappear
- “not seen this time” is treated as “no longer active”
- wall state drops after malformed messages

### Prevention

- default to `delta_update`
- require explicit `full_snapshot` confirmation for destructive inactivation
- keep publisher side-effects conservative

### Phase Mapping

- Must be addressed before any automated publish is trusted

## Pitfall 3: Hiding Rules In Prompts

### Why It Happens

Prompt rules are easy to add and feel fast.

### Warning Signs

- correctness depends on “the model usually understands”
- no unit test can prove a publish guard
- operators cannot explain why one row published and one did not

### Prevention

- move business rules into explicit code
- log rejection reasons
- back repeated failures with tests

### Phase Mapping

- Must be addressed in validation and replay phases

## Pitfall 4: Exception Pool As A Graveyard

### Why It Happens

Systems collect failures but do not convert them into durable fixes.

### Warning Signs

- same exception shape appears repeatedly
- fixes happen only in manual UI sessions
- no new test or rule appears after repeated incidents

### Prevention

- add replay tooling
- add failure clustering or repeated-pattern review
- require frequent promotion into templates, rules, scripts, or tests

### Phase Mapping

- Must be addressed in replay/industrialization phases

## Pitfall 5: Over-Refactoring Instead Of Closing The Safety Loop

### Why It Happens

The current codebase has large files and brownfield pressure points, which makes full redesign tempting.

### Warning Signs

- time spent moving code exceeds time spent making publish decisions safer
- schema changes are large but validation remains weak
- exception volume stays high while architecture churn increases

### Prevention

- prefer minimum structural changes that create hard gates
- improve testability at boundaries first
- keep focus on active-fact safety, not elegance alone

### Phase Mapping

- Must be watched throughout the whole project
