# v0.6D1-R3.7C-R1 — NEMO Composite Selection Lifecycle Repair

## Scope

This stage repairs only the external NEMO 2.4.2 directional-selection oracle introduced by R3.7C. It does **not** alter World 1 production runtime, `mu`, `b`, `q*`, the VA ceiling, migration authority, speciation/RI, fission/coalescence, paleogeography, R3.7 reduced genetic state, or the R3.7A/B neutral lifecycle closure.

## Parent failure retained as evidence

The locally executed R3.7C suite completed 16/16 chains and 80/80 NEMO phase runs, but all 32 selected-vs-neutral qfreq checkpoint pairs were byte-identical. The parent suite therefore had engine-complete evidence with zero realized selection effect and is invalid for `K_eff` calibration.

## Root cause

The selected branch used standalone `viability_selection` together with `breed_disperse` under `mating_isWrightFisher`. NEMO's `breed_disperse` performs the WF generation transition internally. Consequently, placing `viability_selection` after it leaves no offspring in the selected age class; placing viability before breeding is also semantically wrong because offspring do not yet exist.

## Repair

Selected branch:

```text
quanti_init                 1
breed_selection_disperse    2
save_stats                  3
save_files                  4
```

Matched neutral branch:

```text
quanti_init                 1
breed_disperse              2
save_stats                  3
save_files                  4
```

The selected branch uses Gaussian patch-local optima with explicit `selection_fitness_model absolute`.

The existing `breed_disperse_matrix` remains the migration parameter because the composite event inherits the breed/dispersal implementation.

## New fail-closed selection-efficacy gate

A suite cannot report `NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED` unless every engine-complete chain also passes a numerical liveness gate:

1. selected and matched-neutral final allele-frequency states are not exactly identical;
2. maximum allele-frequency difference exceeds `1e-12`;
3. selected-minus-neutral trait divergence is aligned with the imposed optima and exceeds `1e-12`;
4. selected-minus-neutral cross-group segregation potential is positive.

The `1e-12` values are numerical null tolerances only. They are not biological acceptance thresholds and do not calibrate effect size.

Failure status:

`INVALID_SELECTION_ORACLE_SELECTION_EFFICACY_GATE_FAILED`

## Governance

- Parent R3.7C files are restored byte-for-byte and remain historical authority for that stage.
- R3.7C-R1 is implemented in new source/runner/test/config files.
- The invalid local R3.7C results are retained as diagnostic evidence and explicitly barred from `K_eff` inference.
- `scalar_K_eff_authorized = false`.
- `production_runtime_binding_authorized = false`.
- `canonical_write_allowed = false`.
