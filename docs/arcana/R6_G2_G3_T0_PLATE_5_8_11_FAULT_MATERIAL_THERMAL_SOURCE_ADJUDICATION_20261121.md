# ARCANA R6 — T0 source contact-side rock identity and laboratory thermal applicability

**Date:** 2026-11-21. **Base R6 FAIR software HEAD:** `55650b9caedd899f8bfd43a90dbaf945611c8d21` (166/166 regression PASS and 66 PANGAEA fitted rows analyzed).
**Development branch:** `r6/g2g3-t0-contact-thermal-material-provenance-20261121`.
**Decision:** `T0_CONTACT_SOURCE_SIDED_FACETS_AND_CRUST_THERMAL_SUPPORT_EXTRACTABLE__ACTUAL_GOUGE_PRESSURE_AND_SLIP_NOT_QUALIFIED`.
**FAIR original-source executable gate:** pending.

## Why this is the next substantive geological step

The WorldSim mission is physically grounded historical geology and resources, including spatial mineralogy, water/Deep, tectonics, hydrology, flora/fauna, and time-dependent provenance. An Earth lab *fitted friction coefficient* is not a geological facies map for the original 210 Ma planet. We must establish whether the source T0 contact geometry and sampled PRE columns contain enough physical identity/conditions to place it.

**Existing R6 support is richer than a total absence of material data:** `B6N8L_SUPPORT_MATERIAL_BINDING_MATRIX.json` and `B6N8N_EXACT_SUPPORT_MATERIAL_BINDING_AUDIT.md` provide explicit reference roles (continental/oceanic crust and lithospheric mantle) and some specialist thermal `rho,k,Cp,A` tuples on original 1-degree geographic support, subject to their scope. They **explicitly disallow inferring real rock composition** from categorical crust-domain codes. PRE supplies authentic original 51-field nodal thermal, density and layer geometry columns with material configuration codes, not measured mineralogy, clay percentage, pore pressure or actual T0 fault gouge.

The original 8×8 (81 nodes, 128 faces, 12 contact edges between plates 5/8) and 16×16 (289 nodes, 512 faces, 36 source contact edges spanning 5/8/11 with authentic triple parent `34587`) source inventories exist. The original FEG has **open 2D faceted plate contact geometry**, not two mechanically split fault-side nodes nor closed 3D solid fault faces.

## New implementation

`experiments/plate58_deforming_explore_v1/g2_g3_t0_contact_material_applicability.py`

- Reopens **original SHA-pinned** FAIR `CONTINUATION_A.json` + 8/16 `OUTER_A_{08|16}x{08|16}.feg` and `*_PRE_T0_PASSIVE.dat`, and the source SHA-chain-bound G2 nodal 51-column records.
- Reconstructs both *original source owner faces* of every original `R6BND-T0-` contact via `g2_source_owned_face_topology.source_face_incidence`. Keeps original parent IDs, plate pair, owner-face third vertex and shared edge IDs. Does not synthesize a fault thickness, split node or extra sliding DOF.
- Independently reopens and checks the **FAIR real-source PANGAEA921284 stability `REPORT.json` and `MANIFEST.json`**, source SHA `b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d`, 66 model-fit rows, pressure assignment count 0, and ARCANA assignment count 0.
- For every original source-owner-face vertex, evaluates exact mathematical roots of its **original cubic crust temperature polynomial** `T(z)=293.15 K` (the 20°C laboratory test condition), using normalized depth to avoid numerical ill-conditioning. Reports every root in `[0,H_crust]`, no crossing `[]`, or non-unique whole-layer crossing `null`.
- Distinguishes *necessary thermal isotherm reachability* in each of the 3 source vertex columns from actual shared physical fault temperature at a common depth, spatially continuous thermal field, geological fluid condition, or laboratory P/T/rate applicability. No interpolation across third-vertex values, no implicit pressure from depth, no mapping to a gouge material.
- Counts exact source contacts, their two owner faces and the subset where **all three vertex columns on both source sides have some 293.15 K crustal isotherm**. This is a mathematical diagnostic, not a co-located fault-temperature or applied physical law.
- Persists **write-once** source SHA and manifest bound `REPORT.json` and `MANIFEST.json` without touching original FAIR outputs, canonical data or world HistoryStore.

### Novel physical finding targeted

Because the PRE is **per original shared parent node**, the same edge-node thermal/material-configuration source record is used on each adjoining source face. This tells us that the current shared-node engineering mesh lacks **independent side-specific gouge composition/pressure/depth**. A difference in third-node PRE fields may reflect original regional thermal model heterogeneity; it cannot be presented as a measured fault-wall mineralogical contrast. Consequently physical fault-sidedness, friction law, damage state and gouge phase/mineral fractions **cannot be inferred from this source**.

Numerical roots of 293.15 K along original columns are useful precisely to disambiguate a *temperature feasibility condition* from a physical fault state. An isotherm may occur at different depths in the 6 nodal profiles; there may be no unique common contact-surface temperature anywhere. If not present in a source crust column, application of a strict 20°C laboratory law there **cannot** be justified without explicit extrapolation. If present, this does not prove the law applies: mineralogy, water, test effective normal stress, reference friction and strain/slip rate remain unknown.

## Scientific references and limitations

- Original Earth laboratory: Ikari & Kopf 2017, DOI `10.1126/sciadv.1701269`, tests at 20°C with nominal 10 MPa effective normal stress, but earlier Tohoku tests at 7 MPa; source inverse-fit dataset DOI `10.1594/PANGAEA.921284`. https://pmc.ncbi.nlm.nih.gov/articles/PMC5706663/
- Rate-state parameters depend on natural gouge mineralogy, hydration, temperature, pressure and test path; a fault-rock laboratory analogue is not a universal material law. https://doi.org/10.1029/2023GL106485 and https://doi.org/10.1029/2024JB030596
- ARCANA material reference vs actual composition: `docs/arcana/research/B6N8I_THERMAL_MATERIAL_LAB_BINDING_AUDIT.md`, `B6N8N_EXACT_SUPPORT_MATERIAL_BINDING_AUDIT.md`, and canonical Deep geographies `CANON/12_DEEP_ENERGY_GEOGRAPHY_EXTRACTION_AND_TRANSPORT.md` (geology, mineralogy, crystallography and history are constitutive resource dependencies).

## Validation status

- `tests/test_r6_g2_g3_t0_contact_material_applicability.py`: synthetic 81-node/128-facet/12-contact original-style P1 fixture, both source-owned face identities, exact cubic one/two/zero/infinite-isotherm cases, invalid temperature coefficients, source plate tampering and missing PRE, immutable report source hash and authority fail-closed.
- Tests on FAIR: **PENDING**; original 8×8 and 16×16 real FEG/PRE and source PANGAEA stability report have **NOT been executed with this new adapter yet**. No source results or contact thermal counts may be reported as actual yet.
- Full G2/G3+RSF regression previously 166/166 FAIR PASS on R6 main; this new code/test branch is isolated and not integrated until targeted and full suite PASS.

## Science gate after first FAIR source execution

The physical T0→T1 solve still demands:
1. Source map or explicit authorial material decision for **actual 210 Ma gouge mineralogy, hydration, pore pressure** on original contact boundaries, not extrapolated from `material_configuration_code`;
2. Mechanically independent contact surfaces and bounded slip-side DOFs preserving the source graph 5:8:11 and node 34587, plus compliant fault closure, damage and constitutive law;
3. Actual fault-normal stress, absolute friction reference `mu_ref`, stiffness, rates and lab P/T/rate applicability; no use of the 20°C source globally without relevance proof;
4. Physically supported regional cut tractions, basal normal/tangential mantle driving conditions and unique GPE owner, with force/torque/work and nonlinear solver validation.

```text
PRE_THERMAL_COLUMNS_AND_SOURCE_FACET_OWNERS=SOURCE_AUTHENTIC
R6_THERMAL_AND_DENSITY_ROLE_REFERENCES=SOURCE_SPECIALIST_REDUCED_MODEL_ONLY
T0_CRUSTAL_293_15K_ROOT_DIAGNOSTIC=IMPLEMENTED_FAIR_PENDING
PANGAEA_LAB_EARTH_PARAMETERS_TO_ARCANA_MAP=null
ARCANA_T0_FAULT_GOUGE_MINERALOGY=null
ARCANA_T0_FAULT_FLUID_STATE=null
ARCANA_T0_FAULT_SIDEDNESS=null
ARCANA_T0_FAULT_EFFECTIVE_NORMAL_PA=null
G3_PHYSICAL_BASAL_AND_CUT_LOADS=null
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
HISTORYSTORE_PRODUCTION_AUTHORIZED=false
```
