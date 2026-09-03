# v0.6D1-R3.21 — H0 Present Lineage Registry, Historical Lineage Closure & Generic Functional-Phenotype Fork Readiness

## Status

`CANDIDATE — REQUIRES LOCAL EXACT-R3.19 CHECKPOINT RUN`

## Scope

R3.21 is a **read-only derived-data stage** above the SEALED R3.19 H0 0 ka checkpoint.
It does not replay biology and does not alter any SEALED environmental, biological, genetic,
CHA-1 or CHA-2 authority.

## Exact parent authority

The production run MUST consume the exact R3.19 SEALED pair:

- JSON SHA-256 `658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71`
- NPZ SHA-256 `f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406`

Expected exact 0 ka state:

- 134 present species;
- 295 present components;
- total population `1217.2506240828814`;
- Deep biological coupling OFF.

Any parent mismatch fails closed.

## R3.21A — Present registry extraction

Materialize every present species and component directly from the checkpoint fields already
preserved by the restartable runtime: `component_ids`, `root_species`, `current_species`,
`registry`, `events`, and the numerical `pop`, `guild`, `trait`, `va`, `gen` arrays.

No species is created, removed, merged, ranked or relabeled.

## R3.21B — Historical lineage closure

For each present lineage:

- resolve `parent_species_id` recursively to a root;
- reject missing parent references;
- reject ancestry cycles;
- index historical events touching the lineage or its ancestors;
- reject a directly extinct species appearing in the present set.

The full historical registry is preserved in the derived output; R3.21 does not delete extinct
ancestors merely because they are not present at 0 ka.

## R3.21C — State/accounting closure

Required gates:

1. exactly 134 unique present species;
2. exactly 295 unique present components;
3. every component maps to one present species and one root species;
4. every present species exists in the historical registry;
5. population finite and non-negative;
6. component and species sums reproduce the checkpoint total;
7. exact-0 ka inaccessible population is zero when the checkpoint accessibility mask is exposed;
8. additive-variance state is finite/non-negative;
9. the four canonical reduced genetic-state arrays from R3.19 are present, finite and
   component-axis consistent;
10. pairwise ancestry covariance and neutral segregation potential preserve the exact
    R3.19 component ordering;
11. historical event classes are preserved from `event_type`, `event`, or `type`;
12. all extinction events, including ordinary background extinction, participate in the
    no-resurrection gate;
13. Deep biological coupling remains OFF;
14. no biological time advancement and no new lifecycle event generation.

## R3.21D — Functional-phenotype fork readiness

R3.21 reserves a schema for R3.22 domains only. All values remain `null` / `UNDEFINED_UNTIL_R3_22`.
No human-readiness score exists in R3.21.

Reserved generic domains:

- manipulative capability;
- locomotor flexibility;
- cognitive capacity;
- learning/plasticity;
- sociality;
- dietary flexibility;
- life-history;
- ecological generalism;
- tool-use potential;
- environmental problem-solving capability.

The names reserve an interface; they do **not** assign phenotype values, human similarity or
selection pressure.

## Canonical outputs

A successful local run materializes:

- `R3_21_PRESENT_LINEAGE_REGISTRY.json`
- `R3_21_PRESENT_COMPONENT_REGISTRY.json`
- `R3_21_HISTORICAL_LINEAGE_CLOSURE.json`
- `R3_21_REDUCED_GENETIC_STATE.npz`
- `R3_21_REDUCED_GENETIC_STATE_SUMMARY.json`
- `R3_21_FUNCTIONAL_PHENOTYPE_FORK_INTERFACE.json`
- `R3_21_AUDIT_SUMMARY.json`
- `R3_21_AUDIT.md`
- `R3_21_OUTPUT_MANIFEST.json`

## Forbidden in this stage

- changing H0 parameters or arrays;
- changing CHA-2 or hydrological hazard;
- enabling Deep biological coupling;
- choosing a human lineage;
- computing a human-likeness/readiness ranking;
- filling new functional phenotype values;
- running a new evolutionary replay to manufacture missing ancestry.

If historical lineage data are incomplete, R3.21 must fail closed and report the missing
provenance rather than infer author-selected ancestry.

## REV4 extraction-geometry correction

The first canonical R3.21 candidate run exposed two extraction-only issues:

- the R3.19 checkpoint names the governed reduced arrays with a `reduced_` prefix;
- most historical lifecycle records store their event class in field `event`.

REV3 corrected only those read-only mappings. The subsequent canonical run then correctly failed closed because REV3 had imposed pairwise `(component, component, trait)` geometry on `reduced_ancestry_covariance`.

The SEALED reduced-state authority instead defines:

- `VA_within[component,trait]`;
- `C_ancestry_LD[component,trait]`;
- `S_neutral[component,component,trait]`;
- `h[component,trait]`.

REV4 restores that exact geometry and validates a common trait axis. Only `S_neutral` is pairwise. This is an extraction/audit correction only; it does not alter source checkpoint values, event semantics, ancestry, biological state, environmental state, or governance.
