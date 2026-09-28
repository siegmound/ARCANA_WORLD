# R6 T0 OrbData ARCANA adapter and source generalization

**Decision:** `R6_T0_ORBDATA_ARCANA_SOURCE_GENERALIZATION_FAIR_QUALIFIED__PRE_ORBDATA_SCIENTIFIC_BLOCKERS_REMAIN`

The deterministic ARCANA-side grid exporter is implemented in `src/arcana_worldsim/r6/shellset_mesh/orbdata.py`. It reads governed 180×360 fields and writes OrbData grid text plus replay and support lineage. The full field package remains surface-closed at SHA-256 `31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534`; its historical parent hash remains recorded separately as `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`.

## Export contracts

- `aArray`: oceanic lithosphere age in Ma. Physical authority is limited to governed ocean cells. Land cells receive a deterministic nearest-ocean numerical interpolation halo; the separate physical domain field always controls branch classification.
- `cArray`: crust thickness is exported in kilometres (`m / 1000`) because pinned OrbData multiplies this input by 1000.
- `ARCANA_DOMAIN.grd`: values come from `physical_crust_domain_id` (ocean code 1, governed continental codes >=2), not plate identity and not age interpolation.
- `ARCANA_TOTAL_LITHOSPHERE_M.grd`: governed continental **total** lithosphere thickness in metres, with semantic role `GOVERNED_REQUESTED_TOTAL_LITHOSPHERE_STRUCTURE`. Patched Assign initializes mantle lithosphere as requested total minus crust, then applies the original bounds and downstream thermal consistency correction. The adapter does not emit `sArray` or synthetic `delta_ts` data.
- Every grid has a one-cell periodic longitude halo and edge-row latitude halo. Grid headers match OrbData’s two coordinate records. Rows are serialized north-to-south although source arrays are south-to-north.

## FEG projection

`scripts/r6_t0_project_surface_to_feg_nodes.py` reuses the existing R6 mesh/provider adapter. It preserves incident source-cell lineage, unknown values, and mixed categorical support. It makes no resolution claim and applies no smoothing. The canonical partition payload is unavailable on this Windows checkout, so the 64,442-node projection remains pending FAIR execution.

## ShellSet source and runtime

The exact source patch is [R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch](D:/corsi/Arcana/ARCANA_WORLD/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch), SHA-256 `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`. It changes only `src/MOD_ShellSet.f90`, `src/OrbData5.f90`, `src/MOD_Data.f90`, and `src/ShellSetMain.f90`. Both `INPUT/ARCANA_DOMAIN.grd` and `INPUT/ARCANA_TOTAL_LITHOSPHERE_M.grd` activate ARCANA staging: `InputSetup("OD")` copies them to per-model `.15` and `.16` and omits `.12`. With neither source file, stock `DataFiles(6)` is copied to `.12`; a partial pair records `FatalError` and returns without staging stock `.12`. `OpenInput` repeats the all-or-none check. `ShellSetMain` now checks the existing FatalError state immediately after OD `InputSetup` and invokes `MPI_Abort` before `OpenInput`, `OpenOutput`, or `OrbData5`. This orchestration edit is classified `FAIL_CLOSED_INPUT_GOVERNANCE_ONLY`, with no physics or mechanics equation change. The preceding patch SHA `74fa912d913a82314453ab00addc3e6bcfe1ede87f51866035412e4393f9ad94` is superseded. Domain ID 1 selects oceanic physics; governed IDs 2–6 select continental structure using categorical nearest-cell lookup, never bilinear age or plate/elevation inference. `cArray` remains the required source-compatible crust input. Stock `sArray` read and inversion remain on the stock path; ARCANA does not read `sArray` and does not synthesize `delta_ts`. Exact zero elevation bypasses the ETOPO sentinel in both global and local checks only in explicit mode. Downstream geotherm, `cooling_curvature`, `chemical_delta_rho`, and consistency corrections remain active.

The Assign fixture reported requested total lithosphere 135 km, crust 35 km, and initial mantle component 100 km. ARCANA continental output was invariant to extreme synthetic `sArray`; stock output changed strongly with `sArray`. Its non-isostasy diagnostic is recorded as test-fixture-parameter behavior, not T0 physical evidence. The production-path `InputSetup -> OpenInput -> CloseInput` fixture covers stock and full-pair modes. For partial modes it now calls `InputSetup` only and requires both `FatalError.txt` and `Error/FatalError_1.txt` to contain the partial-pair diagnostic; it does not continue to `OpenInput`.

The initial FAIR attempt failed before linking because the script forced `FC=nvfortran`, bypassing `mpifort`. The next attempt passed the NVIDIA build, Assign fixture, stock staging/open check, and full ARCANA staging/open check. It confirmed partial-pair detection, but did not qualify end-to-end fail-closed behavior: upstream `abort(11)` only prints, and the old fixture then failed in its unsupported partial mode. MPI smoke and ListEx1 were not reached. This is qualification infrastructure evidence, not a scientific failure. The current patch adds the ShellSetMain MPI fatal gate and the fixture now checks recorded fatal files without opening inputs for partial cases. The script retains `make -B ShellSet`, the exact n10_t5 ListEx1 invocation, and transactional failure recovery that restores only patched tracked source files and the qualified parent executable while retaining logs and untracked output. It is [r6_t0_fair_apply_qualify_shellset_arcana_patch.sh](D:/corsi/Arcana/ARCANA_WORLD/scripts/r6_t0_fair_apply_qualify_shellset_arcana_patch.sh). `PRE_ORBDATA_ready` remains false, mechanics remains unauthorized, and the historical runtime identity applies only to unmodified ShellSet.

The historic runtime at `09a06ecd061f00b80a52af86e31d609ff5545a8b` with executable SHA-256 `03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349` is evidence for unmodified ShellSet only. A modified build is not qualified.

## Readiness and gates

`PRE_ORBDATA_ready` remains false. The heat-flow route for zero-valued FEG inputs and governed `qLim0`, `dQL_dE`, and `qLim1` configuration remain unresolved; age-zero GDH1 handling also depends on these limits. No values were invented. OrbData and ShellSet mechanics were not run; no `dt`, T1, or forward evolution was authorized.

The FAIR validator now requires the surface-closed package SHA and the surface-closure commit as its ancestor gate. The historical parent package hash is retained in this report. The integrated machine-readable record is `R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json`.

## FAIR executable reproducibility readjudication

The historical qualified executable remains SHA-256 `03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349`; it applies only to the historically qualified unmodified source. Rebuild A is `0d48576ec1b3d8ff38c9b92d1d794d23235ceeaaebc1d6c051ae980b8cc78272`. Rebuild B, the currently readjudicated FAIR parent executable, is `4603c7d2854c2999c1e8e4607b7bbe470e43f300bf2e8ed1650528e49ceb56e9`. A and B are not byte-identical. The next qualification run requires B as its exact pre-patch executable and preserves it transactionally before applying the source patch.

`Models.txt` was compared by global model ID (column 1), ignoring row order, the invocation line, and ThID (column 2), with exact equality for every field from column 3 onward and no tolerance. Duplicate IDs are rejected and exactly the same set of nine model IDs is required:

- Reference vs A: 9 models, MAX_ABS=0, MAX_REL=0.
- Reference vs B: 9 models, MAX_ABS=0, MAX_REL=0.
- A vs B: 9 models, MAX_ABS=0, MAX_REL=0.

Classification: `PARENT_BINARY_NOT_BYTE_REPRODUCIBLE`; `PARENT_NUMERICALLY_REPRODUCIBLE_AT_REPORTED_PRECISION`; `CURRENT_PARENT_ARTIFACT_READJUDICATED_FOR_PATCH_QUALIFICATION`. This does not assert that historical executable `03e1…` equals current parent `4603…`.

The updated FAIR harness now requires pre-patch executable SHA-256 `4603…` and performs the stock ListEx1 comparison by model ID. This is evidence correction only: `PRE_ORBDATA=false`; patched ShellSet runtime remains unqualified; no T0 OrbData, mechanics, dt, T1, or forward evolution was performed. No ShellSet run is claimed by this Windows checkout.

## Previous FAIR qualification attempt: parser-only failure

The latest FAIR attempt passed ARCANA identity, NVIDIA toolchain, patch application, NVIDIA build, Assign fixture, the stock/full/partial-pair InputSetup fixture, MPI smoke, and the complete 9/9 ListEx1 execution. Qualification stopped only in the final `Models.txt` parser: it treated the non-numeric header row (`global model, ThID, ...`) as data and attempted to use `global` as a model ID. This is a harness parsing failure, not a ShellSet runtime or scientific failure.

The parser correction now skips non-numeric/header rows, requires integer global model IDs exactly `1..9`, rejects duplicates, ignores column 2 `ThID`, compares columns 3 onward by global ID independent of row order, and uses exact Decimal comparisons with computed `MAX_ABS` and `MAX_REL` and no tolerance. At that point the patched runtime remained formally unqualified pending the corrected FAIR rerun. `PRE_ORBDATA=false`; no ShellSet execution was run on this Windows checkout, and no T0 OrbData, mechanics, `dt`, T1, or forward evolution is authorized or claimed.

## FAIR source-generalization qualification closure

The corrected FAIR qualification completed with `RC=0`. NVIDIA build, Assign structural fixture, stock/full/partial-pair InputSetup qualification, MPI smoke, and the exact n10_t5 ListEx1 regression all passed. ListEx1 completed 9/9 models. `Models.txt` comparison was keyed by global model ID, ignored asynchronous row order and `ThID`, and compared every field from column 3 onward exactly: `MAX_ABS=0`, `MAX_REL=0`, `PASS_STOCK_LISTEX1_BY_MODEL_ID`.

The governed ShellSet source realization is commit `62fd474f229b2676fd9d39c5def45137d22d2481` on local FAIR branch `arcana-r6-runtime-capacity`, with parent `09a06ecd061f00b80a52af86e31d609ff5545a8b`. The qualified patched executable SHA-256 is `4c0044fe4332184d63408960a2237d4edb7da891b71f74b82bd1d5a83b27e918`. Because the ShellSet `origin` points to the upstream `JonBMay/ShellSet` repository, this local commit was not pushed upstream. The source realization remains reconstructable from qualified parent `09a06ecd061f00b80a52af86e31d609ff5545a8b` plus governed ARCANA patch SHA-256 `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`.

This closes the **OrbData source-generalization runtime qualification blocker**. It does **not** authorize T0 OrbData execution or mechanics. `PRE_ORBDATA_ready=false` remains governed by unresolved heat-flow routing / `qArray` and `qLim0`/`dQL_dE`/`qLim1` configuration, OrbData material/thermal configuration, and the remaining FEG materialization work where applicable. No `dt`, T1, or forward evolution is authorized.

Machine-readable closure evidence is recorded in `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json`. Raw FAIR qualification evidence is retained under `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs/v0_6D1_R6_T0_ORBDATA_ARCANA_QUALIFICATION`.
