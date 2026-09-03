# R3.19-R2 — Exact 0 ka Endpoint Support Reconciliation Audit

## Trigger
The first canonical R3.19 run correctly failed closed after the phase-aware transport step because the final population on exact 0 ka inaccessible cells was `3.4292999049868904e-06`, above the governed numerical audit tolerance `1e-08`.

All other critical gates passed: the constant-forcing phase-aware path was bit-exact to SEALED R3.8, q remained below 0.08 with no clipping, the state remained finite and internally consistent, and no Deep biological coupling was active.

## Root cause
R3.19 correctly time-averaged continuous forcing for the 125→62.5 ka and 62.5→0 transport phases, but it inherited the discrete `accessible` topology from those phase averages. A cell can therefore be accessible during the phase-average forcing while being closed at the exact 0 ka endpoint. The second transport phase can place a tiny amount of population on such a cell.

SEALED R3.8 uses endpoint topology at its biology boundary. Therefore discrete topology must not be treated as a time-averaged continuous field.

## Repair
R3.19-R2 separates the two semantics:

- continuous climate/resource forcing remains time-integrated exactly as in R3.18;
- phase-aware transport remains exactly two 62.5 kyr substeps;
- the discrete macro-boundary `accessible` mask is the exact 0 ka provider topology;
- after the second transport substep, any population on cells accessible in the phase-average forcing but inaccessible at exactly 0 ka is conservatively reconciled with the existing SEALED `remap_to_land` operator;
- the moved mass is recorded in `topology_remap_mass` and the existing `paleogeographic_support_loss_remap` event bookkeeping;
- no parameter, cadence, q ceiling, gene-flow cadence, lifecycle gate, or Deep coupling is changed.

## Promotion invariant
If phase forcing and endpoint support are identical, endpoint reconciliation is a no-op and the generalized path remains bit-exact to SEALED R3.8.

## Regression evidence
- R3.19-R2: 13/13 PASS
- R3.18: 10/10 PASS
- R3.17: 9/9 PASS
- R3.16: 11/11 PASS
- R3.15: 12/12 PASS
- R3.14 binding: 9/9 PASS
- R3.14 numeric portability: 4/4 PASS
- total: 68/68 PASS

Formal candidate audit after repair: 218/218 PASS.
