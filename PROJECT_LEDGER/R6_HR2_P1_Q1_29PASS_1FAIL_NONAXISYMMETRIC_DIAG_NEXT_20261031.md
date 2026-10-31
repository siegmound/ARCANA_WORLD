# ARCANA R6 — HR2-P1-Q1 actual qualification BLOCKED; next D1 read-only spatial-consistency diagnosis

**Recorded:** 2026-10-31. **Source/authority:** user-reported FAIR local `docs/arcana/R6_HR2_P1_Q1_FAIR_20261031.md`, external sealed evidence root referenced therein. This GitHub documentation process cannot inspect the actual FAIR file tree and makes no independent numerical-qualification claim.

## Outcome

`HR2_P1=BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE`. **ONE** numerical qualification launch, **29 tests PASS / 1 FAIL**. Reported spatial axisymmetric convergence ~2; temporal convergence ~1; nonaxisymmetric degree-one harmonic `h=H0+epsilon cos(phi) cos(lambda)` has plateauing area-weighted L2 error and increasing max error across refinement, violating frozen required spatial order >=1.5. Conserved finite-volume volume/declared mass, nonnegativity/positivity, CFL checks, native/B0 direct/split 3Y and 10Y independent-process restart, corrupted/source/stale negatives PASS. Observed launcher wall **5.108 s**, sampled process-tree RSS peak **124.32 MiB**, all **317 source/input pins** unchanged. No source patch, changed tolerance, retry, second qualification run or long simulation. Original prepared `SOURCE_CONTRACT.json` SHA256 `544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186` remains frozen. No scientific source admission, no six-grid or 1000Y physics success.

Do NOT promote any property from this BLOCKED to full multidimensional convergence. Conservation and positivity do not imply consistency, accuracy or convergence. Axisymmetric success vs nonaxisymmetric failure points to the longitude-dependent stencil/metrics, seam, polar rows, manufactured cell averages, or analytical-reference phase; these are **hypotheses**, not an established root cause.

## Proposed next gate: HR2-P1-D1 READ_ONLY diagnostic evidence (not a model revision)

Objective: isolate exactly where the first-harmonic nonaxisymmetric truncation / reference error grows and whether it is polar, longitudinal, seam or reference construction, using the already sealed Q1 evidence, frozen model source and manufactured geometry.

1. Verify Q1 manifest/finalization and frozen model, `acceptance.json`, `manufactured.py`, `checks_method.py` SHAs and exact logs/output, once. Snapshot all current source bytes before investigation, leave frozen tests/criteria untouched. Check full numerical convergence table for each grid (16x8,32x16,64x32,128x64,256x128), mode, weighted L1/L2/Linf, dt/substeps and analytic temporal phase. Report available evidence and gaps; no invented numbers or claim of full-grid separate oracle where only a scalar receipt exists.
2. From **existing persisted Q1 arrays if available**, compute signed local error by cell and latitude band; area-weighted L1/L2, Linf, contribution-to-L2 by 10-degree band and polar-row index; report global, excluding first/last 1/2/4 polar rows, and abs(latitude) <= 60/75/85 degrees; localize whether error blows up near poles, seam or interior. Preserve exact Q1 state; any derived rasters must be read-only outputs with source hash references.
3. Independently verify true spherical **cell area averages** of the manufactured field and continuum solution (not point samples at a centroid), using analytical integrals/independent high-precision quadrature; compare constructor and oracle field values by latitude/longitude. Audit face center distance, spherical meridional/east-west edge lengths, boundary flux/no-flux and periodic seam against separate geometry formulas. Check especially pole-adjacent rows and longitude flux coefficients `kappa*Lface/dcenter` for `cos(phi)` denominators, angle signs and adjacent-cell coupling. Pole outer faces must have zero length and no point-contact/clique flux.
4. If existing Q1 records do not retain the necessary per-cell numerical state, **do not silently rerun physical model** under read-only gate: record exact missing diagnostic array/telemetry and produce an opt-in bounded diagnostic replay proposal with a new isolated output directory and unchanged frozen model. No Q1 in-place rerun. For future separately approved diagnostic execution: compute the frozen **one-step spatial consistency defect** on exact analytic cell-average inputs, `A_i*L_h(h_exact)-A_i*(Δ_S h_exact)_cellmean`, at every grid, and distinguish time error by dt refinement. Report area-weighted residual, maxima and band maps for both harmonics. This distinguishes stencil inconsistency from end-time accumulated error; do not change physical coeff/acceptance.
5. Classification requires evidence: `POLAR_FACE_METRIC_OR_LIMIT`, `LONGITUDE_FLUX_DISCRETIZATION`, `SEAM_PERIODIC_CONNECTIVITY`, `CELL_AVERAGE_REFERENCE`, `TEMPORAL_REMAINDER`, `OTHER` or `UNRESOLVED`. Prioritize **smallest falsifiable diagnosis**, not speculative optimization. A geographic high resolution 2K was NEVER actually numerically qualified by Q1.
6. Deliver `DIAGNOSTIC_MATRIX.csv`, `LATITUDE_ERROR_BANDS.csv`, `FACE_METRIC_AND_ORACLE_AUDIT.md`, observations vs hypotheses vs missing evidence, actual source SHA/manifest, one minimal proposed model-correction experiment under **new revision/gate** if warranted. A D1 PASS means reproducible diagnosis, NOT corrected convergence. If missing required arrays prevent definitive claim, produce `HR2_P1_D1=BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED` plus precise minimal additional read-only/opt-in replay requirements.

**Absolute guardrails:** no change to the frozen acceptance order>=1.5 or 5% temporal-refinement condition; no source patch, no post-hoc acceptance relaxation, no automatic repeat, no new 1000Y/10k/100k, no original evidence modifications or FAIR commit/push. If eventual method revision is needed, create distinct `HR2_P1_R1` change candidate with new SHA/contract and requalify full original Q1 suite plus adversarial tests after explicit authorization. Q1 remains historically BLOCKED.

```yaml
HR2_P0: PASS_GROUNDED_GLOBAL_PHYSICS_AND_ARCHIVAL_READINESS_MAP_OPERATOR_REPORTED
HR2_P1_PREPARATION: PREPARED_SOURCE_TESTS_AND_FIXED_ACCEPTANCE_NOT_RUN
HR2_P1_Q1: BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE
HR2_P1_Q1_TESTS: 29_PASS_1_FAIL
HR2_P1_D1_DIAGNOSIS: PROPOSED_NOT_EXECUTED
HR2_P1_GLOBAL_SCIENTIFIC_SOURCE_ADMISSION: false
GLOBAL_1000Y_EXECUTION_AUTHORIZED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
```
