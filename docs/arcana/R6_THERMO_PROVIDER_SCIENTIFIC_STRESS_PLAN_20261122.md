# ARCANA R6 — Thermodynamic provider pilot: staged scientifically meaningful stress tests

**Date:** 2026-11-22  
**Status:** `PLAN_AUTHORIZED_BY_AUTHOR__EXTERNAL_ENGINES_NOT_YET_RUN`  
**Scope:** MAGEMin_C.jl v2.4.5 / Perple_X v7.3.3; future GeoParams v0.10.0.  
**Principle:** Expensive scientific tests are authorized when they test a physical/numerical hypothesis or a reproducibility failure mode. Mere longer runtime is not evidence.

## Already accepted, software-only

FAIR reported on exactly `393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2`:
- 35/35 targeted, 640/640 selected (including 35) PASS.
- Source register pinned SHA256 `1cdfa4b3e361e5398ebba4c07a9516995ee04f419e6ce365c3b07c91e1cd8948`.
- Actual external MAGEMin and Perple_X executions **0**; scientific comparison NOT authorized.
- Exact pass receipt `docs/arcana/R6_THERMO_PROVIDER_PREFLIGHT_FAIR_640_RECEIPT_20261122.md`.
- Current external runner tied to **that exact tested HEAD** via `PRE/MANIFEST.json.code_head_git_sha`. Always execute `scripts/r6_thermo_provider_run_official_fair.sh` on detached SHA `393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2`, not on a later docs commit; use the original preflight NEW01 evidence.

## Stage S1 — Real upstream executables, independently reproducible

**S1a. Installation provenance.** Isolate toolchains outside ARCANA source and existing `arcana-r6-linux` conda env. Verify exact Julia package/Manifest, MAGEMin upstream commit, Perple_X source tag and release archive SHA256 and binary-inside-archive match; retain compiler/OS CPU, BLAS and thread configuration. Record tool-specific *thermodynamic database* names, versions and composition systems; provider version alone is insufficient.

**S1b. Official Earth fixture reproduction.** Run 2 official MAGEMin `ig` examples and 1 upstream `Perple_X/test/bl691_MEEMUM`. Validate all upstream provider statuses and convergence, pressure/temperature units, phase names, phase weight fractions (nonnegative, total approximately 1 or 100%, correct normalization), density and chemical mass-balance when complete output is available. Compare Perple_X reference `.prn` to same-tag reference. MAGEMin official examples are compared to their **own official reference** where numerically specified; do not treat example-only smoke checks as complete quantitative match. Preserve all raw output files and SHA256. Do NOT compare the different upstream compositions against each other.

**Required S1 exit:** `MAGEMIN_EXTERNAL_OFFICIAL_PASS` + `PERPLEX_EXTERNAL_OFFICIAL_PASS` + full pinned artifact manifest, else FAIL/UNKNOWN. Incomplete NEW01 output is a failed evidence attempt; never overwrite it; rerun with NEW02 scope and written disposition.

## Stage S2 — Repeatability and numerical stability (after S1)

- At least **five independent fresh-process executions** per selected common Earth reference case, with identical manifest-fixed chemistry, P/T, H2O/redox and source/database/solver versions. Compare stable phase *sets* (normalize aliases only through a published phase crosswalk), mineral mass fractions, density, convergence/mass-balance residual. Report both maximum observed absolute difference and relative difference; use explicit numerical tolerance set before inspecting results.
- Repeat at single thread versus a chosen multi-thread count **only if the provider documents safe parallel evaluation**. Report any nondeterminism or thread-dependent phase minima and all runtime measurements. No concurrency assumptions about Perple_X.
- Confirm independent mass and chemical composition closure: sum of phase fractions, reconstruction of bulk oxide inventory from phase mass fractions and compositions, conservation of specified H2O and Fe species. A phase fraction sum alone does not establish component-wise mass balance.
- Confirm numerical convergence/error status for each point and identify legitimate phase-boundary discontinuities rather than smoothing or rejecting them arbitrarily.

**Required S2 exit:** Reference case convergence; mass closure within separately justified numerical thresholds; repeatability quantified and source/schema coverage preserved.

## Stage S3 — P/T and chemistry sensitivity, not raw computational escalation

After matching database/component capabilities and choosing one **independently sourced complete terrestrial chemistry**:

- Sample a **5×5 P/T matrix (25 points)** *entirely inside both database validity domains* with predetermined pressure, temperature and fluid states. Include a grid likely to cross documented phase boundaries only if physically meaningful and available from published diagrams; no fabricated precision/phase boundaries.
- Revisit a subset of points in reversed traversal order and with fresh solver initialization to detect local-minimum/path-dependence artifacts; compare Gibbs energy or available optimality evidence.
- Execute controlled, **explicitly bounded** chemistry perturbations for redox, H2O and oxide ratios only where the database species and sources support the perturbation; record uncertainty propagation, not fantasy ARCANA geology.
- Use common P/T units: Pa↔bar↔kbar and °C↔K with dimensional assertions; normalize chemical component set only with a documented stoichiometric map, accounting explicitly for FeO/Fe2O3/O2 and H2O.
- Create provider-specific numerical differences **and an explicit thermodynamic database/model-form difference report**; disagreement does NOT automatically mean one code is wrong. If database models differ too much to be comparable, report `CROSS_PROVIDER_SCIENCE_INCOMPARABLE` and stop ranking.

## Stage S4 — Model and science decisions

Benchmark against known analytical invariants and published phase diagrams/experiments. Evaluate convergence quality, T/P/composition coverage, uncertainty, runtime, memory, deployment friction, legal/data reuse terms, reproducibility and long-term stability. **Prefer scientific validity over equal reproduction of obsolete R6 outputs**. A provider is promotable only for a specified computation/material/data domain. Model replacement is a **software decision**, not an automatic ratification of ARCANA T0 mineralogy or physical T1.

## Stage S5 — ARCANA original-source bounded pilot, if justified

Only after a scientifically credible common Earth baseline and an **explicit authorial hypothetical** rock/fluid/composition is selected:

- Evaluate at exact original 8×8 81 parent IDs with source geometry and PRE P/T profiles *where a true absolute thermodynamic pressure and valid component chemistry are available*. Existing source conditional lithostatic Δσv is **not** automatically thermodynamic pressure. Unsupported nodes remain `UNKNOWN`.
- Keep per-plate/fault-side material identity distinct from per-parent thermophysical quantities; do not invent fault gouge or hydrologic state.
- Compare old G2 material trial with proposed GeoParams/ASPECT mechanisms only with same stress convention, laboratory domain, strain rate and water fugacity.
- Escalate to 16×16 for regional extent sensitivity rather than claiming mesh convergence, and to historical time only after full physical gating.

```text
35_TARGET / 640_SELECTED_SOFTWARE_FAIR = PASS
EXTERNAL_REAL_MAGEMIN = NOT_RUN
EXTERNAL_REAL_PERPLE_X = NOT_RUN
STRESS_TEST_S2_S3 = DESIGNED_NOT_RUN
THERMO_DATABASE_COMMON_MODEL = NOT_QUALIFIED
ARCANA_T0_PHASES_AUTHORIALLY_ASSIGNED = 0
D-024 = ACTIVE
mechanical_solve_authorized = false
physical_T1 = null
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```

**Implementation work next:** Run the exact currently published upstream scientific runner on FAIR after installing pinned engines. When both S1 cases pass, author S2/S3 scripts in a separate branch with new SHA/test evidence; do not retarget the already issued code-head-pinned `NEW01` manifest without a formally versioned transition.
