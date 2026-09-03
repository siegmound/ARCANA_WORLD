# ARCANA WorldSim — v0.6D1-R3.17
## Exact 120 ka Environmental Restart & Deferred-Biology Phase Contract

**Parent:** v0.6D1-R3.16 SEALED 125 ka biology checkpoint  
**Branch:** World 1 H0 / Deep biological coupling OFF

## Decision
R3.17 does **not** execute a 5 kyr partial biology step. The exact 120 ka boundary is an environmental/provider restart while the SEALED biological state remains the exact R3.16 125 ka state.

This is required because the R3.8 production operator is a composed fixed-cadence operator:

- biology cadence: 125 kyr;
- transport cadence: 62.5 kyr;
- gene-flow/recombination: once per biology step;
- speciation/extinction/fission/coalescence checks: 500 kyr cadence;
- demography, trait response, VA and RI clocks contain dt-dependent terms but are ordered inside the same composed macrostep.

Executing only the dt-dependent terms for 5 kyr would create a new operator ordering that has never been validated. Executing all terms for 5 kyr would violate transport and gene-flow cadence. Therefore neither is authorized.

## Governed transition

```text
R3.16 exact biology state: 125 ka
        |
        | 10 x 500-y C2 environmental intervals
        | biology/transport/gene-flow/lifecycle: NO UPDATE
        v
R3.17 exact environment restart: 120 ka
biology state still: 125 ka
pending exposure: 5 kyr
```

## Dual-clock phase
At the R3.17 envelope:

- physical/environment age = 120 ka;
- biological state age = 125 ka;
- elapsed phase since last biology boundary = 5 kyr;
- remaining to next 125-kyr biology boundary = 120 kyr;
- next full biology boundary = 0 ka;
- elapsed phase since last transport boundary = 5 kyr;
- remaining to next 62.5-kyr transport boundary = 57.5 kyr;
- next transport boundary = 62.5 ka.

The 120 ka restart is **not** a new biology cadence origin.

## Pending environmental exposure
R3.17 integrates the exact remaining C2 bridge interval 125→120 ka on its ten 500-y segments using trapezoid quadrature. It stores **field integrals**, not just averages:

```math
I_X^{125\to120} = \int_{125ka}^{120ka} X(t)\,dt
```

for the D3 substrate fields used by the production runtime. R3.18 must combine this 5-kyr accumulator with the 120→0 ka recent exposure before applying the next single 125-kyr biology macrostep.

This preserves:

```math
I_X^{125\to0}=I_X^{125\to120}+I_X^{120\to0}
```

without inventing a 5-kyr biology step.

## Support-transition diagnostic
The exact 125 and 120 ka accessible masks are compared against the parent population. R3.17 reports cells lost/gained and any parent population mass located on cells that are inaccessible at 120 ka. This is diagnostic only: R3.17 does not insert a sub-cadence migration/remap operator. A later stage must resolve any support mismatch before treating the 120 ka envelope as an independently advanced population state.

## Forbidden
R3.17 may not:

- change biology or transport cadence;
- call R3.8 `advance_state`;
- apply demography, migration, selection, gene flow, VA, RI clocks, speciation, extinction, fission or coalescence;
- relabel the 125 ka biology state as 120 ka;
- claim the C2 200–120 ka bridge is historical glacial chronology;
- enable Deep biological coupling;
- use human/sapience/richness targets.

## Acceptance
PASS requires:

1. exact R3.16 SEALED parent and canonical checkpoint hashes;
2. exact ten 500-y C2 intervals from 125 to 120 ka;
3. exact replay-safe 120 ka provider boundary;
4. pending exposure accumulator closes to 5,000 y and round-trips exactly;
5. parent biology state is bit-identical before/after envelope construction;
6. no partial biological operator is executed;
7. phase metadata closes to the next 62.5-kyr transport and 125-kyr biology boundaries;
8. no scientific parameter or Deep change.
