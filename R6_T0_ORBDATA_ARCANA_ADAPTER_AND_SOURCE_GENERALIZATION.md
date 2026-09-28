# R6 T0 OrbData ARCANA adapter and source generalization

**Decision:** `R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION_PREPARED__FAIR_QUALIFICATION_REQUIRED`

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

The exact source patch is [R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch](D:/corsi/Arcana/ARCANA_WORLD/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch), SHA-256 `74fa912d913a82314453ab00addc3e6bcfe1ede87f51866035412e4393f9ad94`. It changes only `src/MOD_ShellSet.f90`, `src/OrbData5.f90`, and `src/MOD_Data.f90`. Both `INPUT/ARCANA_DOMAIN.grd` and `INPUT/ARCANA_TOTAL_LITHOSPHERE_M.grd` activate ARCANA staging: `InputSetup("OD")` copies them to per-model `.15` and `.16` and omits `.12`. With neither source file, stock `DataFiles(6)` is copied to `.12`; a partial pair fails closed. `OpenInput` repeats the all-or-none check. The preceding patch SHA `4d4e5cfa07e8af0c52bc2fbcf2c77a080c2b68921174ad2e4cde078c5425843c` is superseded. Domain ID 1 selects oceanic physics; governed IDs 2–6 select continental structure using categorical nearest-cell lookup, never bilinear age or plate/elevation inference. `cArray` remains the required source-compatible crust input. Stock `sArray` read and inversion remain on the stock path; ARCANA does not read `sArray` and does not synthesize `delta_ts`. Exact zero elevation bypasses the ETOPO sentinel in both global and local checks only in explicit mode. Downstream geotherm, `cooling_curvature`, `chemical_delta_rho`, and consistency corrections remain active.

The deterministic Assign fixture and production-path `InputSetup -> OpenInput -> CloseInput` fixture are prepared at [assign_source_generalization.f90](D:/corsi/Arcana/ARCANA_WORLD/tests/fixtures/r6_t0_orbdata_arcana/assign_source_generalization.f90) and [open_pair_driver.f90](D:/corsi/Arcana/ARCANA_WORLD/tests/fixtures/r6_t0_orbdata_arcana/open_pair_driver.f90). The production fixture covers stock staging, a complete explicit pair, and both partial-pair failures using temporary test input files. FAIR qualification and fixture execution are pending.

The first FAIR attempt failed before linking because the qualification script forced `FC=nvfortran`, bypassing `mpifort` and the needed `mpif.h` compile setup. This is an implementation/qualification infrastructure failure, not a scientific failure. The corrected script uses the qualified default `make -B ShellSet` path, removes obsolete Intel interface objects from fixture links, and restores the exact n10_t5 ListEx1 invocation and mapping. It is [r6_t0_fair_apply_qualify_shellset_arcana_patch.sh](D:/corsi/Arcana/ARCANA_WORLD/scripts/r6_t0_fair_apply_qualify_shellset_arcana_patch.sh). `PRE_ORBDATA_ready` remains false, mechanics remains unauthorized, and the historical runtime identity applies only to unmodified ShellSet.

The historic runtime at `09a06ecd061f00b80a52af86e31d609ff5545a8b` with executable SHA-256 `03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349` is evidence for unmodified ShellSet only. A modified build is not qualified.

## Readiness and gates

`PRE_ORBDATA_ready` remains false. The heat-flow route for zero-valued FEG inputs and governed `qLim0`, `dQL_dE`, and `qLim1` configuration remain unresolved; age-zero GDH1 handling also depends on these limits. No values were invented. OrbData and ShellSet mechanics were not run; no `dt`, T1, or forward evolution was authorized.

The FAIR validator now requires the surface-closed package SHA and the surface-closure commit as its ancestor gate. The historical parent package hash is retained in this report. The integrated machine-readable record is `R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json`.
