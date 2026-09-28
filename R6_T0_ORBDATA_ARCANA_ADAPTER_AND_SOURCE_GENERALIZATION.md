# R6 T0 OrbData ARCANA adapter and source generalization

**Decision:** `R6_T0_ORBDATA_ARCANA_ADAPTER_IMPLEMENTED__SHELLSET_SOURCE_GENERALIZATION_AWAITS_PATCH_AND_FAIR_QUALIFICATION`

The deterministic ARCANA-side grid exporter is implemented in `src/arcana_worldsim/r6/shellset_mesh/orbdata.py`. It reads governed 180×360 fields and writes OrbData grid text plus replay and support lineage. The full field package remains surface-closed at SHA-256 `31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534`; its historical parent hash remains recorded separately as `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`.

## Export contracts

- `aArray`: oceanic lithosphere age in Ma. Physical authority is limited to governed ocean cells. Land cells receive a deterministic nearest-ocean numerical interpolation halo; the separate physical domain field always controls branch classification.
- `cArray`: crust thickness is exported in kilometres (`m / 1000`) because pinned OrbData multiplies this input by 1000.
- `ARCANA_DOMAIN.grd`: values come from `physical_crust_domain_id` (ocean code 1, governed continental codes >=2), not plate identity and not age interpolation.
- `ARCANA_CONT_MANTLE_THICKNESS_M.grd`: governed continental lithosphere thickness in metres, transferred as a direct physical field. The adapter does not emit `sArray` or synthetic `delta_ts` data.
- Every grid has a one-cell periodic longitude halo and edge-row latitude halo. Grid headers match OrbData’s two coordinate records. Rows are serialized north-to-south although source arrays are south-to-north.

## FEG projection

`scripts/r6_t0_project_surface_to_feg_nodes.py` reuses the existing R6 mesh/provider adapter. It preserves incident source-cell lineage, unknown values, and mixed categorical support. It makes no resolution claim and applies no smoothing. The canonical partition payload is unavailable on this Windows checkout, so the 64,442-node projection remains pending FAIR execution.

## ShellSet source and runtime

The exact upstream source files were audited against `JonBMay/ShellSet` commit `e4a6fbd5997b6c4978924649dff1abab0c96ca57`; no external ShellSet checkout was modified. **The minimum source patch has not yet been generated.** Its intended contract is to use a complete explicit domain/thickness input pair, fail closed on a partial pair, preserve stock behavior without the pair, bypass the exact-zero elevation sentinel in explicit mode, and keep ocean age-derived thickness and downstream density/curvature equations intact.

The historic runtime at `09a06ecd061f00b80a52af86e31d609ff5545a8b` with executable SHA-256 `03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349` is evidence for unmodified ShellSet only. A modified build is not qualified.

## Readiness and gates

`PRE_ORBDATA_ready` remains false. The heat-flow route for zero-valued FEG inputs and governed `qLim0`, `dQL_dE`, and `qLim1` configuration remain unresolved; age-zero GDH1 handling also depends on these limits. No values were invented. OrbData and ShellSet mechanics were not run; no `dt`, T1, or forward evolution was authorized.

The FAIR validator now requires the surface-closed package SHA and the surface-closure commit as its ancestor gate. The historical parent package hash is retained in this report. The integrated machine-readable record is `R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json`.
