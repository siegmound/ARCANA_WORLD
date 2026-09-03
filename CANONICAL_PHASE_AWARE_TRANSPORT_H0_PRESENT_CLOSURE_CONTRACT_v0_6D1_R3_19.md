# v0.6D1-R3.19 — Phase-Aware Transport Coupling, Exact Endpoint Topology & H0 Present Biology Closure

## Parent authority
R3.18 SEALED: recent H0 environmental exposure 120 ka -> 0 completed while biology remains at 125 ka.

## Purpose
Promote the minimum transport-only generalization required by R3.18 and execute the single pending 125 kyr biology macrostep from 125 ka to 0 ka.

## Preserved authorities
- R3.8 remains byte-unchanged.
- biology cadence: 125,000 y.
- transport cadence: 62,500 y.
- exactly two transport substeps per biology step.
- demography, selection, gene flow, VA/reduced genetics, pair clocks and lifecycle gates retain the R3.8 ordering and cadence.
- Deep biological coupling: OFF.
- no richness, guild, human or narrative target.

## New coupling only
R3.18 supplies:

`E_macro = mean environment over 125 ka -> 0`

`E_T1 = mean environment over 125 ka -> 62.5 ka`

`E_T2 = mean environment over 62.5 ka -> 0`

R3.19 calls the inherited migration operator twice:

`T(E_T1, 62.5 kyr) -> T(E_T2, 62.5 kyr)`

while all non-transport operators still see exactly one macro environment and one 125 kyr biology step.

## Promotion gate
For constant forcing:

`E_T1 = E_T2 = E_macro = E`

R3.19 MUST be bit-exact to the SEALED R3.8 one-step path, including runtime state, records, events and snapshots. Failure is a blocker.

## Support-remap governance
R3.19 does not invent a new shoreline-remap operator. The R3.8 macro-effective-environment support-remap timing is preserved. The exact 0 ka provider support is checked after the step. If significant population mass lies on exact-0-ka inaccessible cells, the run fails closed and no canonical checkpoint is promoted.

This tolerance is a numerical audit guard only; it is not a scientific parameter.

## Canonical success boundary
A successful run produces the World 1 H0 natural-control biological checkpoint at exactly 0 ka.


## R3.19-R2 endpoint-support repair

The phase-aware transport forcing remains time-integrated over two 62.5 kyr phases. Discrete `accessible` topology is now bound to the exact 0 ka provider endpoint. After phase 2, any population on cells that are accessible in the phase-average forcing but inaccessible at exactly 0 ka is conservatively reconciled with the existing SEALED `remap_to_land` operator. This is an operator-order/topology binding repair, not a parameter or cadence change. The constant-forcing case with identical endpoint support remains bit-exact to SEALED R3.8.
