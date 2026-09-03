# v0.6D1-R3.11 STATUS

**State:** CANDIDATE — PRODUCTION LONG RUN REQUIRED  
**Stage:** Post-CHA1 H0 Recovery & Adaptive-Radiation Restart

## Boundaries

- parent: R3.10 SEALED, `65.5 Ma POST_CHA1_500KY`;
- canonical target: `61.0 Ma`, exactly +5 Myr after CHA-1;
- ordinary biology steps required: 36.

## Scientific authority

R3.11 reuses R3.7I/R3.8 production mechanics. No old D3.1 solver is restored and
no post-CHA1 radiation multiplier is introduced.

A one-time lifecycle-thaw adapter prevents the 500-kyr special CHA-1 interval
from being incorrectly counted toward founder/vicariance/reconnection/extinction
persistence.

## Validation completed

- R3.11 unit tests: 5/5 PASS;
- R3.11 + R3.10 immediate regression: 17/17 PASS;
- 65.5→65.0 Ma smoke: PASS;
- smoke serialization identity: exact;
- smoke q clipping: 0;
- CHA-1 events added during smoke: 0.

## Smoke outcome

- 94 species;
- 206 components;
- 1 speciation;
- 1 coalescence;
- 2 paleogeographic remaps;
- 0 ordinary extinctions;
- peak q `0.045762434061137815`.

The smoke speciation is a pre-CHA1 founder carry-over, not yet evidence of a new
CHA-1-caused adaptive-radiation pulse.

## Seal state

R3.11 is **not SEALED yet**. Seal requires the canonical 65.5→61.0 Ma local run,
its checkpoint, full evidence audit, regression and package reseal.
