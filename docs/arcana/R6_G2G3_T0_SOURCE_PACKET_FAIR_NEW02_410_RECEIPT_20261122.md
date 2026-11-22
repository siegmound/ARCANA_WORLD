# ARCANA R6 — FAIR NEW02 source-original G2/G3 T0 physical support packet

**Date:** 2026-11-22  
**Evidence type:** `FAIR_OPERATOR_TERMINAL_REPORTED_PASS__EXTERNAL_REPORT_MANIFEST_BYTES_NOT_INDEPENDENTLY_IMPORTED`  
**Exactly tested SHA:** `c053ea561c0e2874664957b4e27a3236a0885f4c`  
**Isolated branch:** `r6/g2g3-source-physical-packet-20261122`  
**Parent R6 integration commit at implementation:** `c681f57232d159761d36b0eaf0d6bffd11c18c69`  
**Scope:** original `T0_210_Ma` model source-support readback at 8×8 and 16×16; **no physical G2/G3 solve**.  

## 1. Exact operator-provided terminal acceptance

```text
HEAD is now at c053ea56
PHYSICAL_SOURCE_PACKET_SHA=c053ea561c0e2874664957b4e27a3236a0885f4c
PHYSICAL_SOURCE_PACKET_AUTHORITY=SOURCE_MODEL_REFERENCE_NOT_PHYSICAL_RATIFICATION
42 passed in 0.15s
410 passed in 3.28s
--- Read ORIGINAL FAIR FEG/PRE + four source manifest chain (8x8) ---
decision=SOURCE_AUTHENTIC_SUPPORT__PHYSICAL_INPUTS_UNSELECTED_NO_SOLVE
extent=8; parent_nodes=81; full_basal=128; core=8; exterior=120
outer_cut_edges=32; PRE_records=81; unresolved_physical_groups=8
physical_T1=null; D_024=ACTIVE; world_history_production_authorized=false
--- Read ORIGINAL FAIR FEG/PRE + four source manifest chain (16x16) ---
decision=SOURCE_AUTHENTIC_SUPPORT__PHYSICAL_INPUTS_UNSELECTED_NO_SOLVE
extent=16; parent_nodes=289; full_basal=512; core=8; exterior=504
outer_cut_edges=64; PRE_records=289; unresolved_physical_groups=8
physical_T1=null; D_024=ACTIVE; world_history_production_authorized=false
FAIR_ORIGINAL_T0_G2G3_8X8_SOURCE_INDEX=PASS
FAIR_ORIGINAL_T0_G2G3_8X8_PHYSICAL_INPUTS=UNKNOWN
FAIR_ORIGINAL_T0_G2G3_16X16_SOURCE_INDEX=PASS
FAIR_ORIGINAL_T0_G2G3_16X16_PHYSICAL_INPUTS=UNKNOWN
FAIR_G2G3_SOURCE_SHA_CHAIN=PASS
MECHANICAL_SOLVE_AUTHORIZED=FALSE
CANONICAL_PHYSICAL_T1=NULL
FAIR_G2G3_SOURCE_PACKET_TARGET_42=PASS
FAIR_G2G3_SOURCE_PACKET_SELECTED_410=PASS
FAIR_G2G3_SOURCE_PACKET_REAL_T0_READBACK=PASS
```

**42 targeted test cases are included in the 410 selected tests**; do not claim 452 separate cases. 410 is not a full-repository regression claim. The original 8×8 and 16×16 output come from the existing four source-manifest chain, regional FEG/PRE and the noncanonical metadata compiler. Both authentic-source readbacks were run, and the committed script's fail-closed SHA hash/provenance and two-region output checks printed PASS. The output is supplied by the FAIR operator, **not independently downloaded or byte-rehashed** in this authoring environment.

## 2. Source provenance, regional topology and material scope

The 8×8 packet has 81 original parent nodes, 128 original basal facets (8 core/120 exterior), 32 original cut edges and 81 PRE records. The 16×16 packet has 289 parent nodes, 512 original basal facets (8 core/504 exterior), 64 cut edges and 289 PRE records. The original T0 PRE 16-column thermal/density/geometry reference is preserved per node; it is an authored model description, not a mineralogical composition, natural thermal measurement, hydration, pore-pressure law, or physically calibrated rheology. No synthetic thermal 100- or 1000-year pilot output is smuggled in as T0.

The first FAIR NEW01 attempt at original source `ef285fa05eb278143a2700f73aacf3abcdfbb571` passed 38/38 targeted and 406/406 selected tests but failed original 8×8 readback with `PHYSICAL_PACKET_ORIGINAL_TRIPLE_NODE_DRIFT`, so NEW01 **is not an original-source packet PASS**. It revealed that parent node `34587` can belong to the 8×8 regional footprint without being a local 3-plate junction. For NEW02, the compiler uses the verified interface-provider `actual_3plus_plate_junctions` instead of the parent ID membership proxy (0 local triple in 8×8; source parent 34587 with incident plates 5/8/11 in 16×16). Also fixed the nonreached cross-extent runner guard: identical SHA-pinned *four upstream manifests*, but original 8×8 and 16×16 FEG and PRE **must each have their own distinct SHA**. NEW01 is preserved, not overwritten.

## 3. Original non-overwriting external evidence

The committed NEW02 gate creates evidence below:
```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_TARGET_42_NEW02.log
  R6_G2G3_PHYSICAL_SOURCE_PACKET_SELECTED_410_NEW02.log
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
    SOURCE_INDEX.json
    UNSELECTED_PHYSICAL_PROPOSAL.json
    MANIFEST.json
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
    SOURCE_INDEX.json
    UNSELECTED_PHYSICAL_PROPOSAL.json
    MANIFEST.json
```

These paths are derived from the tested committed runner and terminal PASS; the actual external bytes and SHA lists remain on FAIR and were not imported here. Treat the source output hashes as audited by the FAIR script, not independently corroborated by a separate machine.

## 4. Exact acceptance boundary, future prerequisite

```text
SOURCE_SUPPORT_ENGINEERING_FAIR_NEW02=PASS_OPERATOR_REPORTED
TARGETED_TESTS=42/42_OPERATOR_REPORTED_PASS
SELECTED_R6_REGRESSION=410/410_OPERATOR_REPORTED_PASS
ORIGINAL_FEG_PRE_EIGHT_BY_EIGHT=PASS_OPERATOR_REPORTED
ORIGINAL_FEG_PRE_SIXTEEN_BY_SIXTEEN=PASS_OPERATOR_REPORTED
FOUR_MANIFEST_SOURCE_CHAIN_AND_REGIONAL_HASH_RULES=PASS_OPERATOR_REPORTED
PHYSICAL_G2_LITHOLOGY_PHASE_AND_WATER_SELECTED=false
PHYSICAL_G2_CREEP_BRITTLE_FAULT_LAW_CALIBRATED=false
PHYSICAL_G3_FULL_BASAL_CUT_AND_MANTLE_TRACTIONS_QUALIFIED=false
PHYSICAL_G3_GPE_VERTICAL_PRESSURE_CLOSURE_QUALIFIED=false
PHYSICAL_FAULT_SIDEDNESS_STRESS_LAW_QUALIFIED=false
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_T1=null
HISTORYSTORE_MODIFICATIONS=0
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

**Software-only R6 integration** is eligible after explicit fast-forward ancestry check and unchanged tested code/test/script/config Git blob comparison. Writing this receipt and ledger text after tested source `c053ea56` does not change the numerical/source parsing code or extend qualification to unexecuted science.

Next substantive science: jointly propose, source, and validate **one** bounded regional G2+G3+FAULT model: selected rock phases and water/pressure by original T0 node/side; temperature/pressure/rate laboratory support; actual cut traction (N/m), full basal traction/normal (Pa) from a sourced mantle reference, unique full GPE/vertical datum, explicit fault transmission and junction logic, residual/rank/restart/energy. The existing `g2_g3_source_coupled_runner.source_inputs` still contains an older 34587-extent guard; independently repair and test this **in the source-coupled runner's own scope** before any coupled physical scenario. Missing physical evidence stays null; do not promote this source-only packet to physical T1, ore/Deep/geological history or canonical production.
