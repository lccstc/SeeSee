# Research Summary

## Stack

The best-fit architecture for this project is not model-first parsing. It is a deterministic publish pipeline built on the existing Python core and PostgreSQL-backed quote wall: raw message ledger -> candidate builder -> validator -> publisher -> exception/replay loop.

## Table Stakes

- raw message as sole evidence
- parser/model only produce candidates
- explicit validator and publishability gate
- failure never clears old active facts
- default `delta_update`, explicit `full_snapshot`
- every failure enters replayable exception handling

## Watch Out For

- parser output being treated as fact
- partial failures wiping old wall state
- business rules hidden in prompts
- exception pool growing without industrialized fixes
- over-refactoring before the safety loop is closed

## Recommendation

Build the smallest possible set of hard boundaries that enforce:

1. no direct publish from parsers or agents
2. no publication without `publishable_rows`
3. no destructive fact mutation unless `full_snapshot` is explicitly confirmed
4. no repeated exception pattern without replay/test/rule follow-up

This fits the current repo well and aligns with the business requirement that quote-wall correctness is the heart of the system.
