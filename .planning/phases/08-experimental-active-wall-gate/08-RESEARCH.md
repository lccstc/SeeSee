---
phase: 08
slug: experimental-active-wall-gate
status: researched
created: 2026-04-15
---

# Phase 08 — Research Notes

## Research Summary

Phase 08 is not about inventing a new parser or a second wall. It is about formalizing an operating mode:

- wall mutations are real
- custody is still fully system-owned
- downstream actions remain off
- the operator gets enough observation signal to judge whether the wall is safe enough to promote later

The key implementation lesson from prior phases is that the hardest failures were never “missing one more parser trick”; they were authority confusion and invisible partial behavior. Phase 08 therefore needs to make operating mode and outcomes visible.

## What already exists

- Guarded publisher already owns active quote mutation.
- Snapshot semantics already constrain delta vs confirmed full behavior.
- Workbench already explains one message at a time.
- Failure dictionary already gives reusable repair guidance.

This means Phase 08 does **not** need a new execution core. It needs:

1. explicit experimental-wall mode control
2. explicit downstream-off behavior
3. explicit wall-level observation metrics
4. explicit promotion criteria

## Recommended Operating Model

### Experimental active wall mode

The system should support an explicit mode where:

- guarded publisher is enabled
- quote wall updates are real
- evidence / snapshot / repair lineage are still mandatory
- downstream actions remain disabled

### Observation-first operator surface

The operator should not have to inspect one case at a time to understand whether the wall is healthy. `/quotes` should expose a compact health surface for:

- wall updates today
- new exceptions today
- mixed outcomes today
- remediation success / escalation today
- risky snapshot-authorized mutation count

### Promotion gate

Promotion out of experimental mode should not be gut feel alone. At minimum, the system should make it easy to judge:

- is the wall auto-updating enough to be useful?
- are exceptions shrinking or exploding?
- are mixed outcomes common enough that the wall still feels half-blind?
- which groups remain unstable?
- are risky full-snapshot mutations rare and explainable?

## Concrete constraints to preserve

- No parser / page / script / agent bypass around guarded publisher
- Default unresolved => delta
- Zero publishable rows => no-op
- No automatic downstream notify / settlement / outward actions
- All wall mutations remain traceable to evidence + validator + snapshot lineage

## Recommended Plan Shape

### Wave 1
- Add experimental-wall mode switch and enforce publisher-only mutation with downstream-off guards

### Wave 2
- Add operator-facing wall health / experimental-mode observation surface in `/quotes`

### Wave 3
- Add promotion criteria artifact + API/UI visibility so the operator can judge whether the wall should remain experimental or move toward formal authority

## Open questions resolved for planning

- **Should Phase 08 remain pure no-op shadow?** No. It should be a real experimental active wall.
- **Should it grant downstream business authority?** No.
- **Should it create a new page?** Not necessarily. Reusing `/quotes` is better for single-operator workflow.
- **Should this phase decide formal production handoff?** No. It should define the gate, not execute the handoff.
