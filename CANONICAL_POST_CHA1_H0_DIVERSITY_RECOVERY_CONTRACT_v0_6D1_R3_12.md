# v0.6D1-R3.12 — Canonical Post-CHA1 H0 Diversity Recovery Contract

## Purpose

Continue the sealed H0 World-1 state from **61.0 Ma** (`POST_CHA1_5MY_RECOVERY`) to **46.0 Ma** (`+20 Myr after CHA-1`) and observe long-horizon diversity recovery under the already promoted ordinary production runtime.

R3.12 is an **observation/continuation stage**, not a diversification calibration stage.

## Parent authority

R3.12 MUST load the sealed R3.11 checkpoint exactly:

- age: 61.0 Ma;
- species: 95;
- components: 236;
- Deep biological coupling: OFF;
- CHA-1 completed exactly once;
- post-CHA1 ordinary lifecycle thaw completed exactly once;
- checkpoint JSON SHA-256: `bdf75d08bd39181dee3331f91b1dd6864ab8e0c1e88c94eed7813d148aebda3b`;
- checkpoint NPZ SHA-256: `4f4582ca7f83926941f7224033a83356b2f5df196dcb8d3dbafae2e9b16e987c`.

R3.12 MUST NOT restart from 65.5 Ma, 66 Ma, 150 Ma, or 210 Ma.

## Canonical time window

```text
61.0 Ma -> 46.0 Ma
+5 Myr -> +20 Myr after CHA-1
125 kyr biology cadence
120 biology steps
```

The +20 Myr horizon preserves the established post-CHA1 diversity-recovery staging, but the old historical D3.2 solver is not reactivated. The active scientific runtime remains the promoted R3.7I/R3.8 continuation machinery.

## Scientific authority retained unchanged

R3.12 MUST NOT change:

- mutation variance supply `mu = 0.002/Myr`;
- nonlinear variance depletion `b = 0.9876543209876544`;
- normalized VA ceiling `q_max = 0.08`;
- K_CENTER semantics (`38.47` remains an operational reduced-order coordinate reference, not a physical constant);
- migration or gene-flow limits;
- RI/speciation gates;
- founder persistence = 1 Myr;
- vicariance persistence = 2 Myr;
- reconnection persistence = 2 Myr;
- ordinary extinction semantics;
- paleogeography/barrier authority;
- 125 kyr biology cadence;
- 500 kyr speciation/extinction/fission/reconnection checks.

## No second thaw

R3.11 already performed the unique temporal thaw after the 500 kyr CHA-1 freeze.

Therefore R3.12 MUST preserve:

```text
CHA1_high_resolution_event_bridge_complete cumulative count = 1
post_CHA1_ordinary_lifecycle_thaw cumulative count = 1
```

and MUST produce zero delta for both events.

## No target-driven recovery

The following are descriptive reference values only:

- pre-CHA1 richness: 305 species;
- immediate post-CHA1 richness: 93 species;
- R3.11 boundary richness: 95 species.

R3.12 PASS MUST NOT require:

- richness to rise above 95;
- recovery to any percentage of 305;
- positive net diversification;
- a specific number of speciations/extinctions;
- Earth-like recovery timing;
- a guild-specific richness target.

If the ordinary sealed model yields flat or declining richness while all physical and lifecycle invariants hold, the run is scientifically valid and the unexpected outcome must be audited rather than tuned away.

## Recovery diagnostics

R3.12 records, without using them as gates:

- species richness;
- component count;
- total population;
- species richness by guild;
- fraction of direct CHA-1 richness loss recovered;
- fraction of pre-CHA1 richness present;
- active post-impact root lineages;
- number of root lineages with multiple current species;
- speciation chronology;
- ordinary extinction chronology;
- fission/coalescence chronology;
- provenance of speciation relative to founder candidates already present at 61 Ma.

A speciation not matched to the 61 Ma founder state is **not automatically attributed to empty-niche causation**. Causal attribution requires a later counterfactual comparison.

## Genetic and spatial gates

Every accepted R3.12 run requires:

- no negative population;
- zero population on inaccessible cells;
- q <= 0.08;
- zero clipping steps and contacts;
- symmetric `S` within numerical tolerance;
- zero `S` diagonal within numerical tolerance;
- nonnegative `S` within numerical tolerance;
- exact checkpoint serialization/reload identity.

## Canonical endpoint

The successful full local run must produce a restartable checkpoint at:

```text
46.0 Ma
POST_CHA1_20MY_DIVERSITY_RECOVERY
```

This checkpoint becomes the next H0 continuation boundary only after post-run audit and reseal.
