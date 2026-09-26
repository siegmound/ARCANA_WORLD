# R6 Wave 3A — Simulation-1 Bootstrap Authority Recovery

**Baseline:** `main` / `origin/main` at `592b1651b405363373590092e133bd25569d99a5`

**Finding:** `STRONG_INFERRED_RECONSTRUCTION`; insufficient to establish canonical bootstrap authority.

## Git archaeology

Read-only search covered the seven local/remote refs reported in the JSON, all 142 reachable commits, path/content history for A1, 210 Ma, bootstrap, initial-state, paleogeography, Pangaea/Pangea/supercontinent, land mask and plate state, plus deleted-path history. There are no tags and `git fsck --full --no-reflogs --unreachable` reported no unreachable objects. The reachable history begins at root import `15ef285e554658125744056ec9266d9b0ed4c0ba` (2026-09-03), which already contains A1 and the R1/R3 material. No matching deleted bootstrap contract or A1 producer was recoverable. This only establishes the Git-history boundary; it does not prove no external archive exists.

## Evidence graph

```text
UNKNOWN pre-import producer / upstream source
        ├──> A1 R1 210 Ma reference (hash recorded in R1 reference manifest)
        └──> A1 R3 210–0 Ma mixed reference trajectory (hash recorded in R3 source manifest)
                  │
                  ├──> R1 materializer + R1 config + D1 metadata + Deep reference
                  │      └──> later R1 biological common state (candidate; not original Sim1 physical state)
                  ├──> R2/R3 replay consumers (environment/topology boundaries; later biological simulations)
                  └──> D3.2C endpoint-constrained transition reconstruction (derived timing, not tectonic observations)
```

The R1 and R3 A1 artifacts have identical first-frame values for all 11 shared arrays checked, including age, grid, land mask, plate code, climate/aridity and forage. R1’s materializer explicitly loads the R1 A1, Deep, D1 metadata and config to create a later species-level rebaseline. It does not create A1. The R2 runtime uses A1 210/180 land/plate endpoints with a topology switch and interpolated environmental support. D3.2C derives event timing from A1 land/plate endpoints. `late_cenozoic/paleogeography.py` is scoped to 30→0 Ma and labels its output a derived endpoint-constrained reconstruction. None is the original Simulation-1 physical bootstrap consumer or a physical plate-motion solver. Accordingly, A1 is called an ARCANA physical/environmental reference trajectory here; its relationship to original Simulation 1 is unproven.

The exact A1 provenance chain is therefore **open at the source/generator edge**. The root import is the first Git record, not evidence of who generated A1. `PACKAGE_MANIFEST_v0_6D1_R3.json` records A1 R3 and the R1 common-state output by hash/size; `SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3.json` records A1 R3 and `REFERENCE_HASHES_v0_6D1_R1.json` records A1 R1. `SIMULATION_RESULTS/MANIFEST.json/.csv` also record the R1 common-state output with matching hash/size, but label its repository authority and semantic status pending. The aggregate manifest does not directly list A1 R3; the semantic catalog is bounded to other payloads. These manifests authenticate file identity and copy lineage, not who generated A1 or its original Simulation-1 semantics.

## Decision

210 Ma remains the best-supported candidate because A1 begins there, R1 is explicitly a 210 Ma candidate rebaseline, and R2/R3 start at 210 Ma. But this is **strong inferred reconstruction**, not a direct contract or exact multi-artifact reconstruction of the original Simulation-1 bootstrap. Do not freeze `R6_GLOBAL_T0` yet. Exact Pangaea semantics, initial physical fields, planetary assumptions and the original consumer remain unbound. A1 and every later frame remain reference-only; no field is authorized for R6 state by this audit.

**Decision:** `CANDIDATE_R6_GLOBAL_T0_210MA_AUTHORITY_INCOMPLETE`

**Next recovery:** obtain the pre-import Simulation-1 archive/source manifest and original physical-geography generator/consumer chain.
