# R3.11 Diagnostic Smoke Audit

**Window:** 65.5 → 65.0 Ma  
**Ordinary steps:** 4 × 125 kyr  
**Verdict:** `PASS_R311_POST_CHA1_RECOVERY_SMOKE__ORDINARY_LIFECYCLE_RESTART_VALID`

## Gates

- exact R3.10 parent checkpoint: PASS;
- 93 species / 207 components parent: PASS;
- CHA-1 reapplication: 0 events — PASS;
- lifecycle thaw exactly once: PASS;
- founder/vicariance/reconnection frozen-time correction: PASS;
- ordinary lifecycle re-enabled: PASS;
- Deep coupling OFF: PASS;
- negative population: none;
- inaccessible-cell population: zero;
- segregation-potential symmetry/diagonal/nonnegativity: PASS;
- q ceiling: PASS;
- clipping steps: 0;
- save/reload identity: exact PASS.

## Emergent smoke outcome

```text
65.0 Ma
species        94
components    206
population    1606.4745439563944
remap            2
coalescence      1
fission          0
speciation       1
background extinction 0
peak q         0.045762434061137815
```

The speciation at 65.0 Ma is:

```text
RPT_004 -> RPT_004_D04
```

It matches an R3.10 founder candidate that existed before CHA-1. Therefore this
smoke event is recorded as a **pre-CHA1 founder carry-over completing after the
restart**, not as proof of CHA-1-caused empty-niche radiation.

## Implementation correction encountered during smoke

The first smoke attempt completed the biological steps but failed only while
loading the temporary smoke checkpoint because the new loader constructed an
invalid zero-sized temporary reduced-genetic state solely to recover its class.
The loader was corrected to instantiate `ReducedGeneticLifecycleState` directly.
No scientific runtime code, parameters or smoke outcome were changed.

Post-fix:

- R3.11 unit tests: 5/5 PASS;
- R3.11 + immediate R3.10 regression: 17/17 PASS;
- smoke: PASS.
