# ARCANA R6 — Physically guarded T0 authorial bulk-composition hypothesis provider

**Date:** 2026-11-21.
**Parent branch/software evidence:** `r6/multiphysics-integration-20261026` at `083a6a685c177c43ae1e3c321084e7d8b3f9258d`; FAIR 200/200 on geochemical reference compiler.
**New branch:** `r6/t0-authorial-bulk-composition-provider-20261121`.
**Decision:** `EXPLICIT_BULK_OXIDE_AUTHORIAL_HYPOTHESIS_PROVIDER_IMPLEMENTED__REAL_T0_CHEMISTRY_UNASSIGNED`.

## 1. Motivation: first real compositional modeling contract, NOT a natural geology map

The 2026-11-21 FAIR geochemical reference source audit established six source-identified terrestrial analogues (4 average Earth continental crust compartments, depleted mantle reservoir, and N-type MORB melt trace-only), but **zero** natural ARCANA chemical assignments. It also established B6N8N reference thermophysical support over **63,620 of 64,800** native 1° cells, with 1,072 unresolved ocean and 108 excluded zero-age ridge cells. Thermal admissibility, domain IDs and density are **not** evidence of actual mineralogy or rock composition. The source index authoritatively retains exact membership SHA256:

`f61f4a89bacdf458636720ed4df67bd97cc731159bb588f6836e065241e1e499`

The authorial Canon 12 says Deep availability is distributed and depends partly on geology/mineralogy/crystal structure, deformation and history. Canon 53/57 distinguish ordinary constitutive material properties from magical-mode access, and do not grant a global initial mineral map. The uploaded canon package was checked for these chapter titles and scope; none of the present code writes Canon/WorldHistory or assigns Deep `f_X, zeta`.

This stage implements a **source-guarded scientific hypothesis engine**, not a source-complete natural T0 geology. The user has not selected bulk-oxide endmembers, mantle hydration, mineral phase proportions, source chemistry maps, fault gouge or transport dynamics; no selections are made on their behalf.

## 2. Implemented and isolated

`experiments/t0_authorial_composition_v1/provider.py`

`experiments/t0_authorial_composition_v1/UNSELECTED_T0_AUTHORIAL_SCENARIO.json`

`tests/test_r6_t0_authorial_bulk_composition.py`

### Level A: source-derived *unselected* scenario template

The provider reads `docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json` using exact Git blob `e06770577ebaf549aa113a4e72ec9f6095a29c2d`, and verifies original 180×360 grid, 64,800 cells, 63,620 admitted thermophysical support. Its default template deliberately carries `recipes=[]`, `mixtures=[]`, `placements=[]`, `authorial_selection_confirmed=false`, and no T0/T1 authorization. This is a **real executable contract**, not a fabricated lithology or mineral reserve.

### Level B: conditional authored *bulk-oxide* recipe + endmember mixture

An author may propose a source-named research recipe with an explicit rationale, material role and major-oxide subset `{SiO2,TiO2,Al2O3,FeO* OR FeO,MnO,MgO,CaO,Na2O,K2O,P2O5}`. Every supplied oxide is typed `wt.%` with explicitly supplied nominal/low/high mass percentages. The subset may be incomplete; the code neither renormalizes it to 100 wt.% nor infers the missing mass as a mineral, water or oxidation state. The conversion to oxide-equivalent element masses reuses the already FAIR-verified geochemical compiler.

In this first scientific phase `source.kind` must be **`AUTHORIAL_EXPLICIT_HYPOTHESIS`** and contain a transparent author reference string. A label claiming `PUBLISHED_EARTH_ANALOGUE_AS_HYPOTHESIS` is rejected because citation text without a real exact-numeric source join would be an unsupported promotion of literature. Verified Earth references remain independently recorded; a later feature can implement source-joined literature-derived candidates.

A mixture requires **at least two** endmembers of the **same material role and identical oxide keys**, each with strictly positive fractions summing to 1 to absolute (10^{-12}). Per-oxide nominal and declared uncertainty bounds are combined linearly by mass fractions (not probabilistic error propagation):

```text
w_i = sum_j(f_j * w_ij)
lo_i = sum_j(f_j * lo_ij)
hi_i = sum_j(f_j * hi_ij)
sum_j f_j = 1
```

This is **compositional mass bookkeeping**, not thermodynamic equilibrium. Two different `FeO`/`FeO*` conventions cannot be mixed silently. A recipe with non-null oxidation/fO₂, water, fluid pressure or unjustified complete bulk chemical coverage is rejected until independent phase/fluid source models exist. Actual `SiO2` etc must come from an explicit authorial hypothesis, not from an implicit global Earth average.

### Level C: conditional *original native-cell* provenance binding

If `placements` is not empty, an `authorial_selection_id` (minimum 8 chars) and `authorial_selection_confirmed=true` are required. This is **not physical canon ratification**: output remains explicitly `hypothetical_native_cell_assignments`, and `physically_ratified_T0_composition_cell_count=0`.

Every candidate placement requires all of:
- Full original governed `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz` at SHA256 `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`.
- Full canonical `R6_T0_VECTOR_PLATE_PARTITION.npz` at SHA256 `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`.
- The **complete** 63,620 line lexical-sorted admitted-cell membership list, encoded one `R6G1D-Rrrr-Cccc\n` per entry; its SHA must equal the source index SHA `f61f4a89...`. The index contains a membership **digest, not a standalone published full cell list**, so a future original-provider exact export is needed before real spatial placements.
- The genuine canonical source arrays `face_row`, `face_col`, `face_plate_id` (each 64,800), verified against `plate_support_adapter.py`. They must reconstruct the complete 180×360 native plate grid one-to-one, with no duplicated cells or invented already-shaped plate field.
- Original crust-domain ID for that exact `row,col` and plate ID, both equal to the original arrays. Only continental (domain 2–6) vs oceanic (domain 1) **crustal bulk candidates** are currently placeable. Mantle, deep rock, faults, fractured gouge and sediment are deliberately *not* placeable without their own source volumetric/fault-side support and phase fields.

There are **no placements in the default template**, and no fake list or plate field is substituted. A synthetic 180×360 grid used in tests is explicitly identified as *synthetic* and its hashes are test-local monkeypatches; it is not a R6 source archive nor an authorial source selection.

### Unqualified physics and resources

Even when a research recipe and original cell are provisionally joined, bulk-oxide elemental composition does **not** determine mineral modal volume fractions, phases, chemical zoning, melt, local water, pore pressure, oxygen fugacity, viscosity, damage, rock friction, ore deposits or Deep extractability. A real petrological provider additionally requires selected thermodynamic dataset and assemblage method, T/P/fO₂/water, alteration paths, and heterogeneity bounds; for future resource history, mass flux, crust generation/remelting/recycling and deposition/enrichment physics must be independent. R6 G2/G3 normal pressure/traction and mantle/cut physical loads remain unqualified.

All outputs are fail-closed, immutable and include the source-scenario SHA and report SHA; no world HistoryStore, original NPZ, FEG, PRE or canonical state is modified.

## 3. Validation gates

The development test module defines **24 expected cases** (15 test functions, with one ten-way parametrized check: 15+9=24). Targets include original B6N8N index SHA/count, no-selection template, elemental budget mass balance, 60/40 **synthetic** endmember mixture and uncertainty linearity, negative/NaN/non-matching chemistry, no silent FeO/FeO* co-use, missing author approval, source binary hashes, admitted membership SHA, original plate and domain match, native support boundary, and report write-once SHA. None of the 60/40 numbers is an ARCANA rock composition.

**Current status: TESTS NOT YET RUN ON FAIR**, and no genuine user-authored recipe or cell selection. Engineering R6 main remains on 200/200 tested stable baseline.

Run on FAIR from exact development HEAD:

```bash
python -m pytest -q -ra --tb=short tests/test_r6_t0_authorial_bulk_composition.py
python -m experiments.t0_authorial_composition_v1.provider \
  --repo-root . \
  --template-out "$BASE/R6_T0_AUTHORIAL_BULK_COMPOSITION_EMPTY_TEMPLATE_NEW_01.json"
python -m experiments.t0_authorial_composition_v1.provider \
  --repo-root . \
  --scenario "$BASE/R6_T0_AUTHORIAL_BULK_COMPOSITION_EMPTY_TEMPLATE_NEW_01.json" \
  --output "$BASE/R6_T0_AUTHORIAL_BULK_COMPOSITION_EMPTY_COMPILATION_NEW_01"
```

The empty compile should produce `candidate_recipes=0`, `candidate_mixtures=0`, `hypothetical_native_assignments=0` and `physical_T1=null`. The last full defined G2/G3+RSF+thermal+geochemistry regression was **200/200**; after adding 21 cases, **224 expected** if test collection unchanged. The source code has not yet been tested at FAIR, so no 221/221 or new experimental SHA PASS may be asserted.

## 4. Next physically substantive step

Once the provider passes FAIR, an **explicit authorial decision** must select a regional geology hypothesis (not all 64,800 cells) and its scientific parameters: crustal bulk oxide endmember choice, uncertainty, native cell/plate support with exact source, and a geological process for plausible 210 Ma compositional heterogeneity. Then source-qualify T/P fluid/oxygen fugacity, mineral assemblage via a pinned phase equilibrium provider and tectonic material mass transport. The first original 5:8:11 fault chemistry can only follow valid **true fault-sided geometry and gouge source**; don't infer a gouge from the 20°C original nodal isotherm diagnostic.

```text
SOURCE_ORIGINAL_1DEG_GRID=64800
B6N8N_THERMOPHYSICAL_ADMITTED_SUPPORT=63620
EARTH_REFERENCE_RECORDS_PUBLISHER_VERIFIED=6
AUTHORIAL_EXPLICIT_BULK_COMPOSITION_SCENARIOS_SELECTED=0
AUTHORIAL_EXPLICIT_BULK_COMPOSITION_CELLS_SELECTED=0
ACTUAL_T0_GEOCHEMICAL_CELLS_RATIFIED=0
ACTUAL_T0_MINERAL_PHASES_RATIFIED=0
G2_G3_MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```


### Reproducible Git SHA and original cell-face interpretation

The source-format cross-check against `src/arcana_worldsim/r6/plate_support_adapter.py` established that `R6_T0_VECTOR_PLATE_PARTITION.npz` contains three original one-dimensional arrays `face_row`, `face_col` and `face_plate_id`, each covering 64,800 native faces. The provider now reconstructs the cell grid from these three arrays under an exact one-to-one coverage and integer 12-plate identity check. No non-existent pre-gridded plate array name is presumed. Without a physically sourced *exact admitted-support member list*, no candidate can enter native spatial placement regardless of plausible lithological chemistry. The tests also forbid recipe provenance claims that cannot be numerically reconciled with a pinned published data table.
