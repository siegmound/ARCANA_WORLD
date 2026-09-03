# v0.6D1-R3.18 — Recent H0 Exposure Completion & Transport-Phase Readiness

## Scope
R3.18 starts from the SEALED R3.17 dual-clock restart:

- physical/environment age: 120 ka,
- biology state age: 125 ka,
- pending environmental exposure: 5 kyr (125->120 ka),
- biology cadence: 125 kyr,
- transport cadence: 62.5 kyr,
- Deep biological coupling: OFF.

R3.18 completes environmental integration from 120 ka to 0 ka and materializes the exact forcing integrals needed for the still-pending 125 ka -> 0 ka biology macrostep.

## Non-authorities
R3.18 MUST NOT:

- advance biology,
- execute migration/transport,
- execute gene flow,
- execute lifecycle/speciation/extinction/fission/coalescence gates,
- relabel the SEALED 125 ka biology state as 0 ka,
- use adaptive environmental checkpoints as biology steps,
- add a human-lineage or richness target,
- enable Deep biological coupling.

## Exact transport phase boundary
The SEALED transport cadence is 62,500 y. Therefore the pending 125 ka -> 0 ka macrostep contains exactly two transport phases:

1. 125 ka -> 62.5 ka,
2. 62.5 ka -> 0 ka.

62.5 ka is inserted as a coupling boundary even when it is not an explicit R3.14 adaptive-clock checkpoint. It is supported by the SEALED recent provider on the exact 100-y grid.

## Exposure identities
R3.18 computes:

- I_recent = integral(120 ka -> 0),
- I_full = I_R317(125 -> 120) + I_recent,
- I_T1 = I_R317(125 -> 120) + integral(120 -> 62.5),
- I_T2 = integral(62.5 -> 0).

The exact numerical closure required is:

I_full = I_T1 + I_T2

for every governed environmental field.

## Why production biology closure is deferred
R3.8 currently executes two 62.5-kyr transport substeps using one environment object. Recent forcing is time dependent. R3.18 therefore measures the difference between the two transport-phase effective environments and support transitions but does not invent a new migration/remap ordering.

If the two phase environments are not roundoff-equivalent, R3.19 must validate a phase-aware transport coupling operator before the final 125-kyr biology macrostep can be promoted.

## Canonical R3.18 output
R3.18 is an evidence/restart-readiness stage. Its biological state remains the SEALED 125 ka state. Canonical outputs are an exposure/readiness envelope and an NPZ bundle containing the full and phase-separated integrals.
