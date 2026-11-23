# ARCANA R6 — S2 real-repeatability NEW01: bounded independent read-only audit closure
Date: 2026-11-23.
Decision: `S2_REPEATABILITY_UPSTREAM_EARTH_SCREEN_PASS__INDEPENDENT_READONLY_AUDIT_CONFIRMED`.
Scope: five independent MAGEMin_C.jl Julia OS processes, each computing KLB1 and CUSTOM_IG, and five separate Perple_X v7.3.3 MEEMUM invocations on their original **Earth upstream reference** cases. This is **not** authorial ARCANA T0 chemistry, independent experimental accuracy, physical T1, or cross-provider same-database/same-bulk equivalence. This is a bounded technical qualification, not a universal scientific seal.

## Provenance
- Repository: `siegmound/ARCANA_WORLD`, active R6 S2 branch `r6/thermo-s2-repeatability-protocol-20261123`.
- Exact FAIR tested executable source SHA: `632c4a570f876e3963b1dcd8a1f411a143fc8a59`; not any later docs-only HEAD.
- Source-bound S2 preflight 94/94 software test PASS, nine file hashes, original preflight MANIFEST SHA256 `e96b52635d9755acd36ae9473c7a75c23eb8d1f0a2d80d384a6e09807a77f08b`.
- Earlier immutable official S1 manifest SHA256 `538c1b61f801c9902f8aa9b1b189b07ba38357eec339eb2b0211713f83299227`.
- One official S2 real write-once output: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_S2_REPEATABILITY_NEW01`.
- Real S2 manifest SHA256: `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`.
- User-operated FAIR execution first returned `S2_REAL_ENGINE_REPEATABILITY_SCREEN_PASS` and `S2_REAL_CAMPAIGN_EXIT=0`; this was followed by separate read-only Python independent manifest and numerical recomputation on FAIR with `S2_INDEPENDENT_READONLY_AUDIT_PASS` and `S2_INDEPENDENT_AUDIT_EXIT=0`.
- Evidence provenance: user supplied full terminal output and recorded hash-check result. GitHub ledger operation **did not mount, download, independently inspect, or rehash bytes on FAIR itself**. It records the operator-executed independent verifier, rather than misrepresenting the chat-side GitHub review as a second file-audit.

## Independent audit: exact reported checkpoints
```text
SOURCE_AND_UPSTREAM_GUARDS_PASS
S2_REAL_MANIFEST_STRUCTURE_PASS
S2_ALL_MANIFEST_MEMBERS_SHA256_PASS
FILES_VERIFIED=68
S2_RUN_PROVENANCE_PASS
S2_MAGEMIN_5_NATIVE_READBACK_PASS
S2_PERPLEX_5_NATIVE_READBACK_PASS
S2_REPEATABILITY_RECOMPUTATION_PASS
MAGEMIN_PROCESSES_VERIFIED=5
PERPLEX_PROCESSES_VERIFIED=5
S2_REAL_MANIFEST_SHA256=74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604
S2_INDEPENDENT_READONLY_AUDIT_PASS
PHYSICAL_T1=NULL
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
S2_INDEPENDENT_AUDIT_EXIT=0
```

## Numerical repeatability reported by the independent recomputation
- MAGEMin CUSTOM_IG: G_system, rho_kg_m3, liq, cpx, opx fractions: max absolute delta **0.0** and max relative delta **0.0** across five OS-process outputs for each field.
- MAGEMin PREDEFINED_KLB1: G_system, rho_kg_m3, ol, spl, cpx, opx fractions: max absolute delta **0.0** and max relative delta **0.0** across five OS-process outputs for each field.
- Perple_X: Augite(G), Fsp(C1), Ilm(WPH), cAmph(G), melt(G), q native printed phase wt.%: max delta **0.0 percentage points**, relative delta **0.0** across five process outputs.
- Independently revalidated existing native MAGEMin oxide/bulk chemistry and original Fe2O3-to-internal FeO/O bookkeeping and Perple_X full-assemblage printed oxide molar interval closure within source formatting precision; did not execute a new engine to perform the audit.
- This does not prove byte-identical raw run outputs, unmeasured fields, additional operating environments, solver experimental accuracy, or cross-database equivalence. Perple_X printed chemistry precision is limited to the original report's decimal rounding.

## Governance and next action
- No S2 re-run, directory overwrite, deletion, threshold change or posthoc reinterpretation.
- `D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- S2 is complete **in the declared EARTH_UPSTREAM_FIXTURES_ONLY numerical-repeatability scope**. Do not promote physical ARCANA T0/T1.
- Next bounded gate: **S3 design/contract only** for the previously contemplated 5×5 P/T screening (25 candidate pressure-temperature states if scientifically justified). Define valid P/T ranges, chemistry and database-specific comparisons, legal phase/discontinuity handling, uncertainty, independent verification, output and resource estimates, and fail-closed acceptance **before** any run. Never compare MAGEMin and Perple_X as equivalent chemistry across their presently different databases/bulk inputs. Only separately authorized S3 executable source and write-once evidence may run.
