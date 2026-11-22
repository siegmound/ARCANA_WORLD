# ARCANA R6 — FAIR 451: original-T0 G2/G3 source-to-coupled authoring handoff

**Date:** 2026-11-22. **Experiment branch:** `r6/g2g3-source-to-coupled-physical-scenario-20261122`.  
**Exactly tested source HEAD:** `d3787e3d6683a1209994cacbdecdb13cb63df54a`.  
**Base integrated R6:** `a05d01c8cec68f3696e85d6ba136ae41316abbd8`.  
**Decision:** `G2G3_SOURCE_TO_COUPLED_FAIR_451_AND_ORIGINAL_T0_HANDOFF_PASS__PHYSICAL_PARAMETERS_UNKNOWN`.  
**Evidence class:** `FAIR_OPERATOR_TERMINAL_REPORTED_PASS__RAW_EXTERNAL_MANIFEST_AND_REPORT_BYTES_NOT_INDEPENDENTLY_IMPORTED`.  
**Authority:** `NONCANONICAL_UNSELECTED_NO_PHYSICAL_SOLVE`; `D-024 ACTIVE`.

## FAIR operator terminal — exact run

The operator reported the following terminal output from the clean detached HEAD `d3787e3d6683a1209994cacbdecdb13cb63df54a` running `bash scripts/r6_g2g3_source_to_coupled_fair_gate.sh` under the `arcana-r6-linux` environment:

```text
G2G3_SOURCE_COUPLED_CODE_HEAD=d3787e3d6683a1209994cacbdecdb13cb63df54a
G2G3_SOURCE_COUPLED_GOVERNANCE=NONCANONICAL_UNSELECTED_NO_PHYSICAL_SOLVE
--- 41 NEW targeted junction / source-to-coupled authoring tests ---
41 passed in 0.74s
--- 451 selected R6 regression cases, including 41 NEW tests ---
451 passed in 3.94s
--- Read original already FAIR-certified NEW02 source packet pair and emit scenario templates ---
{"status":"T0_SOURCE_AUTHENTIC_TO_COUPLED_INPUTS_MAPPED__PHYSICAL_PARAMETERS_UNKNOWN","source_8x8_nodes":81,"source_16x16_nodes":289,"unresolved_physical_groups":8,"mechanical_solve_authorized":false,"physical_T1":null,"D_024":"ACTIVE"}
FAIR_G2G3_SOURCE_TO_COUPLED_SOURCE_PINNED_HANDOFF=PASS
FAIR_G2G3_SOURCE_TO_COUPLED_ORIGINAL_JUNCTION=PASS
FAIR_G2G3_SOURCE_TO_COUPLED_PHYSICAL_INPUTS=UNKNOWN
FAIR_G2G3_SOURCE_TO_COUPLED_PHYSICAL_T1=NULL
FAIR_G2G3_SOURCE_TO_COUPLED_TARGET_41=PASS
FAIR_G2G3_SOURCE_TO_COUPLED_SELECTED_451=PASS
FAIR_G2G3_SOURCE_TO_COUPLED_SOURCE_HANDOFF=PASS
```

The **41 targeted cases are included in the 451 selected cases**, not additive. The reported 451 cases are a selected R6 regression subset, **not a whole-repository test claim**. The tested Bash script validates the new output files against their recorded SHA-256 and checks that the two source packet indices retain the authentic regional topology.

## Source support and handoff

The two inputs were the *already-qualified* original T0 support packages under:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
```

New **write-once** output/log paths used by the tested gate:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_SOURCE_COUPLED_TARGET_41_NEW01.log
  R6_G2G3_SOURCE_COUPLED_SELECTED_451_NEW01.log
  R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01/
    SCENARIO_8X8_UNSELECTED.json
    SCENARIO_16X16_UNSELECTED.json
    AUDIT.json
    MANIFEST.json
```

The source 8×8 region contains 81 original parent nodes and the source 16×16 region 289. The incident-plate guard correctly allows global parent ID `34587` in the 8×8 footprint **without** identifying a local triple junction, and retains the actual 16×16 `34587` junction with plates 5/8/11. The handoff preserves the previously-verified four shared source provider manifest SHA-256 values and the *distinct* original FEG/PRE hashes for the two region sizes.

The new authoring templates align with the existing **full-parent explicit engineering scenario** schema, but keep all material, velocity, cut tractions, exterior basal tractions, core basal/GPE, GPE, fluid, fault and solver values unset (`null`). The existing runners explicitly refuse the `authoring_template_unselected=true` marker; filling or removing the marker alone cannot establish ARCANA physical authority.

**Limit of verification here:** The raw FAIR output folders, `AUDIT.json`, `MANIFEST.json`, and log bytes have not been imported into this authoring environment for an independent second hash review. The test results and external output identity are based on the user's operator terminal and the independently read, unchanged GitHub runner source at the exact SHA.

## Scientific and governance adjudication

| Criterion | Result |
|---|---|
| Targeted source-junction and authoring adapter | 41/41 FAIR operator PASS |
| Selected R6 regression including new tests | 451/451 FAIR operator PASS |
| 8×8 and 16×16 source-to-coupled handoff | FAIR operator PASS |
| Validated original T0 4-manifest chain | PASS by committed source readback and prior FAIR NEW02 |
| 8×8 `34587` membership vs actual local triple | Correctly distinguished |
| Source-provenance and immutable authorship outputs | PASS by committed script (not separately byte-imported) |
| **Actual 210 Ma rock identity / hydration / pressure** | **UNKNOWN / not qualified** |
| **Full T/P/rate constitutive, fault and mantle tractions** | **UNKNOWN / not qualified** |
| Mechanical solver or physical T1 | **Not authorized / null** |
| HistoryStore or canonical world production | **Never written / unauthorized** |

**Software-only** no-force integration is eligible after confirming that the R6 branch is an ancestor of the development branch and that all implementation, test and runner **Git blobs** match exactly the FAIR-tested SHA. Subsequent receipt/ledger commits do not change the tested executable code.

Next physically substantive milestone: select one scientifically source-qualified bounded 8×8 **G2 material+water/pressure+creep/brittle law, G3 cut and all basal+GPE/mantle vertical datum, and FAULT sidedness/traction/slip hypothesis** supported by original T0 IDs and calibrated applicability masks. Then validate the same model with 16×16 *domain sensitivity*, not assumed mesh convergence. Do not infer these values from source IDs, Earth-only lab analogues, Euler velocities, or thermal LAB. D-024 remains ACTIVE; `mechanical_solve_authorized=false`, `physical_T1=null`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
