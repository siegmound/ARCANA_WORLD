# ARCANA R6 — Original T0 G2/G3 source-to-coupled regional handoff

**Date:** 2026-11-22. **Source of record:** `r6/multiphysics-integration-20261026` at `a05d01c8cec68f3696e85d6ba136ae41316abbd8`.  
**Development branch:** `r6/g2g3-source-to-coupled-physical-scenario-20261122`.  
**Development decision:** `REGIONAL_T0_SOURCE_TO_G2_G3_FULL_PARENT_AUTHORING_HANDOFF_IMPLEMENTED__FAIR_PENDING__PHYSICAL_INPUTS_UNSELECTED`.  
**D-024:** ACTIVE, with `physical_T1=null`, `mechanical_solve_authorized=false`, and no WorldHistory/HistoryStore publication.

## What this delivers and why it is the next engineering increment

The preceding source packet at SHA `c053ea561c0e2874664957b4e27a3236a0885f4c` passed on FAIR with **42 targeted, 410 selected** test cases and original T0 source readbacks for **8×8 and 16×16**. Each packet has verified original FEG/PRE, the four chained manifest inputs, authentic original source parent IDs and domain-side incidence, and an entirely **unselected** G2/G3 physical proposal. That establishes source *support*, not rock identity, constitutive law, mantle forces, contact mechanics or physical T1.

This development makes that source packet consumable as the **authoring basis** for the existing `g2_g3_core_exterior_source_runner.py` explicit-full-parent input contract, without trying to run unselected physics. It adds three precise units:

1. **Original regional junction source guard** (`g2_g3_junction_source_guard.py`). The old coupled runner incorrectly assumed `34587 in parent_nodes` if and only if extent 16×16. FAIR demonstrated original 8×8 may include the *global* parent ID `34587` without any locally incident three-plate junction. The revised runner reads `actual_3plus_plate_junctions` from the already-SHA-validated G3 interface provider. The 8×8 local incidence is empty; the 16×16 local triple is exactly source `34587` with incident plates `[5,8,11]`. The source node itself is never split into assumed fault slip DOFs.
2. **Source-authentic to coupled authoring adapter** (`g2_g3_source_to_coupled_handoff.py`). It reads and SHA256-validates the two immutable FAIR `NEW02` source-packet directories, verifies each `SOURCE_INDEX`, `UNSELECTED_PHYSICAL_PROPOSAL` and `MANIFEST`, and reuses the previously FAIR-qualified cross-extent rule: **four common upstream manifests**, but **different original FEG/PRE files/hashes for the two source regions**. It emits distinct 8×8 and 16×16 **full-parent scenario templates with the same field names as the existing engineering runner**. All required original node IDs, outer cuts and exterior basal facet IDs are covered exactly; the core eight basal triangles are kept separately identified and their loads/GPE intentionally remain absent. There are no invented material laws, prescribed velocities, zero loads, flow or fluid pressures.
3. **Early fail-closed template handling in existing G2/G3 runners.** A generated template has `authoring_template_unselected=true`. Both the exterior coupled runner and full core+exterior runner reject that marker explicitly, before any material-force assembly. An authored and source-calibrated **new record** would require separate scientific selection, engineering validation and FAIR qualification. Removing the marker does not in itself make values true or physical.

## Exact output and semantics

`SCENARIO_8X8_UNSELECTED.json` and `SCENARIO_16X16_UNSELECTED.json` contain:

- `schema=ARCANA_R6_G2_G3_EXPLICIT_FULL_PARENT_ENGINEERING_INPUT_V1` with explicit **unselected** marker and physical authorization flags false;
- exact `source_manifest_sha256` keys `multiscale`, `interface`, `nodal`, `force`, and original FEG/PRE SHA256, connected back to each FAIR source-packet index/manifest SHA;
- 81/289 `candidate_material_by_parent_node` and `velocity_en_by_parent_node` **null** placeholders;
- 32/64 `line_tractions_by_edge` and 120/504 `basal_tractions_by_triangle` **null** placeholders, with the eight exact core facet IDs listed separately and no fabricated source core load;
- separate `core_basal_tractions_by_triangle=null`, `core_gpe_increment_by_parent_node=null`, `external_gpe=null`, plus explicit missing lithology/fluid, constitutive law, mechanical-LAB/mantle coupling, GPE, sided fault and nonlinear solver requirements;
- no mechanical solve, physical T1 or HistoryStore write.

`AUDIT.json` records the two source-index and manifest hashes, region counts, no selected materials, no qualified tractions and the exact **eight** unresolved physical groups. `MANIFEST.json` hashes every authored output. All new output is **write-once in FAIR external evidence**, separate from the previously validated `NEW02` source-packet outputs.

### Why this does *not* qualify geology

A complete list of inputs is not a physically valid force or material provider. Neither a crust configuration code nor a PRE reference temperature is modal mineralogy. A published Earth lab friction curve does not identify a natural Arcana fault. Euler motion is a kinematic prior, not basal drag or prescribed tractions. Original FEG is a 2D faceted surface with shared parent DOFs, not resolved independent slipping fault sides. Unknown pore pressure cannot be silently set to zero. Source thermal base is not the rheological/mechanical LAB. No global tectonic history, mineral distributions, ore/Deep production or geological resources can be inferred by filling nulls with generic benchmarks.

## Validation requested on FAIR

New tests: **41 expected** (source guard 15; source-to-coupled handoff 20; source-coupled integration 6). Previous selected regression: 410; combined expected **451 selected total**, including new 41 (not 451+41). The 35 pure local new tests already PASS; the six integration tests involving the actual earlier runner must run in the full FAIR project environment. **The 451 and original-source handoff are NOT YET FAIR-qualified.**

Run on a clean detached checkout at the exact published development HEAD under FAIR conda `arcana-r6-linux`:

```bash
bash scripts/r6_g2g3_source_to_coupled_fair_gate.sh
```

Input is the immutable:

```
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
```

New, initially absent output/logs:

```
R6_G2G3_SOURCE_COUPLED_TARGET_41_NEW01.log
R6_G2G3_SOURCE_COUPLED_SELECTED_451_NEW01.log
R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01/
  SCENARIO_8X8_UNSELECTED.json
  SCENARIO_16X16_UNSELECTED.json
  AUDIT.json
  MANIFEST.json
```

The actual full coupled runner is **not executed as physical or even synthetic engineering solve with these null values**. Test-only mocked provider fixtures are explicitly not geologic values. If actual source packet bytes cannot be authenticated or there is more than one provenance chain, the run fails and must not substitute fabricated input.

## Next scientific task after FAIR

Select **one** source-complete, noncanonical bounded regional *physical hypothesis* jointly for G2 material/phase/hydration and calibrated rheology (full T/P/rate range), G3 original cut plus **all** basal tangential/normal tractions with independent mantle reference, valid GPE/vertical datum and no double count, and a real sided fault/continuum transmission law including triple-junction treatment. This necessarily requires authorial decisions and independent source-provider support; no values are selected here. Then test full source-bounded residual, tangent, rank, dissipation, force/torque, restart and dt sensitivity **before** explicitly adjudicating a short physical EXPLORE T0→T1. The long-term WorldSim objective remains causal geological, resource, Deep, biotic and human-history evolution; none of these are produced by this handoff.

```
SOURCE_TO_COUPLED_AUTHORING_IMPLEMENTED=true
FAIR_SOURCE_TO_COUPLED_41_451=PENDING
ORIGINAL_SOURCE_8X8_AND_16X16_UPSTREAM_FAIR=PASS_OPERATOR_REPORTED
MATERIAL_PHASE_WATER_AND_BIOT_LAW_SOURCE_QUALIFIED=false
FULL_BASAL_CUT_MANTLE_GPE_SOURCE_QUALIFIED=false
FAULT_SLIP_LAW_SOURCE_QUALIFIED=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```
