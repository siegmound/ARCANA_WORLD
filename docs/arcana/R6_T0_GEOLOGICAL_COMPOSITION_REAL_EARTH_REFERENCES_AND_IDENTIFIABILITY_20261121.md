# ARCANA R6 — T0 geological composition source audit + real Earth chemistry reference library

**Date:** 2026-11-21.
**Governing R6 engineering parent:** `04c90396f7bf68bea76d1b89968ff7962e41474f` (FAIR 183/183 PASS).
**Dev branch:** `r6/t0-earth-geochemical-reference-library-20261121`.
**Decision:** `EARTH_PUBLISHED_BULK_OXIDE_REFERENCE_LIBRARY_IMPLEMENTED__ARCADIAN_COMPOSITION_SPATIAL_AUTHORITY_UNSELECTED`.
**Phase:** REAL-SOURCE DATA RESEARCH, not physically authorized T0 materialization.

## I. What already exists in R6

The exact source-material registry:
- `docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json` (Git blob `e06770577ebaf549aa113a4e72ec9f6095a29c2d`);
- `docs/arcana/research/B6N8L_SUPPORT_MATERIAL_BINDING_MATRIX.json` (`2c6ff8f755afb91445fe229b2edef416b835bcec`);
- `docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json` (`6e51db00a5df691f8021097af4ff4929fabe8691`).

They define a **180 × 360 = 64,800 cell original geography** with:
- 14,258 admitted continental thermophysical/reference material support cells;
- 49,362 admitted positive-age ocean thermal support cells;
- 1,072 unresolved excluded positive-age ocean cells;
- 108 excluded age-zero ridge cells.

Thus 63,620 cells are admitted for the **particular reduced thermal model**, and 1,180 are excluded. These support counts are **NOT** a mineralogically mapped world, and the code MUST report `geochemical_composition_assigned_cells=0`, not 63,620.

The B6N8L and B6N8N role references (continental/oceanic crust, mantle lithosphere) have `rho,k,Cp` and reference heating terms, but **no natural bulk chemistry, phase assemblage or fault gouge clay fraction**. The original FEG/PRE node `crust_material_code`, `material_configuration_code` and thermal-class categorical IDs do not encode oxide mass fractions. The first G2/G3 FAIR geology 183/183 source audit established the authentic plate5:8:11 contact owner facets and 293.15 K mathematical column crossings, but not a coherent fault depth, P, hydration or physically independent slip sides.

## II. Canon authority: physical minerals, resource formation and Deep are distinct

Audited the user-provided `ARCANA_UNIVERSE_CANON_v0_3_73_MC_FAMILY_H3_CHARACTER_AUTHORIAL_RATIFICATION_RATIFIED` package (archive SHA256 `58ce3ccdef7a1e395877446948b5e4a06c1316bc1b5a79e9af679b66448778fd`):

- `CANON/12_DEEP_ENERGY_GEOGRAPHY_EXTRACTION_AND_TRANSPORT.md`, SHA256 `d82eba8b048cbb54eb80c9b54c34a35e8ce1dcc40abc6822ba31ae62f645d983`: energy accessibility, physical stock, tech extractability and economic resource separate; local Deep behavior depends on geology, minerals, crystal structure, thermal and tectonic history. Oxide totals do **not** give `f_X,a`, `zeta_a`, modal accessibility or an ore reserve.
- `CANON/53_MATERIAL_COUPLING_AND_CONSTITUTIVE_RESPONSE_CANDIDATE.md`, SHA256 `d8e2ec657e03a54c0b845e38a71a3286c5a3725df45b0662508d07b4c22b32ad`: mode access `Q` and ordinary constitutive properties `Theta_M` are distinct.
- `CANON/57_MATERIAL_PROPERTY_LIBRARY_AND_MODE_ACCESS_NUMERICAL_CALIBRATION_CANDIDATE.md`, SHA256 `c43c782db49d0b9e0c9785cb5fd39707a2090efce6eb5f889727ec68bb0d655c`: author-side ambient granite example and other material properties are **not** ARCANA T0 lithological distribution or natural mineral abundance.

The canon package is a **separate uploaded project source**, not R6 1° geography; the hashes above are provenance metadata and are not runtime-fetched by the compiler. This record respects both authorities and does not silently overwrite the current R6 continuation branch.

## III. Real, licensed terrestrial chemical models retained as analogues

Imported exact-byte copies from the MIT-licensed `abuseki/georefdatar` source repository commit `e82b70de1b65d8e9cde52166b93ebc88a50934b2`. Original SHA is verified using Git's **blob SHA-1 including object header**, not a guessed source checksum. Data provenance and original license are under `experiments/t0_geochemical_reference_v1/data/SOURCES_AND_LICENSE.md`.

| Source table | Content; scientific origin | Git blob SHA |
|---|---|---|
| `CC__Rudnick_Gao__2014.csv` | Earth upper, middle, lower, bulk continental crust: mean oxides in wt.% and trace concentrations, DOI 10.1016/B978-0-08-095975-7.00301-6 | `4127120d7499e3d9b62a22384465c39b8806aaf0` |
| `DM__Salters_Stracke__2004.csv` | Depleted terrestrial MORB-source mantle reservoir model, includes H₂O estimated from H₂O/Ce, DOI 10.1029/2003GC000597 | `262447b687f5cae36fde836ffd12c7d439a9f16b` |
| `Sun_McDonough__1989.csv` | Earth N-type mid-ocean-ridge **basaltic melt trace-element analogue**, DOI 10.1144/GSL.SP.1989.042.01.19 | `10e8fce96afa6ddd2b50f0f8a43d783f60d5c34c` |

The 4 crustal reference compartments are published average/estimated *Earth* reservoirs; **they must not become four stratigraphic layers in ARCANA**. DMM is a source reservoir model rather than ARCANA actual lithospheric mantle. N-MORB melts are not the composition of the whole oceanic crust: oceanic crust contains variable basalt, gabbro, hydrated material and sediments. This particular source N-MORB table has **no unit column**, therefore the compiler deliberately emits raw trace values with `source_trace_unit=null`; it does not infer ppm/ppb or convert to a mass budget.

**Source-checked spot quantities (analogues only):**
- Rudnick/Gao upper continental SiO₂: 66.6 wt.%; bulk continental SiO₂: 60.6 wt.%.
- Upper continental 10 major oxides sum to approximately **100.07 wt.%**. This is published rounding/estimated chemistry, not license to silently normalize or add/subtract artificial oxide.
- Salters/Stracke DMM SiO₂ 44.9 wt.%, MgO 38.22 wt.%, FeO 8.07 wt.%, Al₂O₃ 4.28 wt.%, CaO 3.5 wt.%, Na₂O 0.29 wt.%; the six major oxide terms sum to **99.26 wt.%**, a partial original-source subset, not total planetary mantle.
- DMM model water estimate `H2O=116 ppm`, source constraint H₂O/Ce. This is **not** ARCANA T0 mantle water, pore pressure, Biot coefficient or aqueous fault state.
- Continental `FeO*` is total iron conventionally expressed as FeO equivalent. Its converted Fe/O elemental budget is an **oxide-equivalent accounting** and cannot supply Fe²⁺/Fe³⁺ mineral redox speciation.

## IV. New implementable research pipeline

`experiments/t0_geochemical_reference_v1/compile_references.py` now:
1. Checks original unchanged Earth reference CSV Git blobs and source dataset expected shapes and units;
2. Checks the exact three R6 B6N8 source registries by SHA and validates 64,800/63,620/1,180 partition closure;
3. Compiles 4+1 Earth major-oxide estimates and a distinct N-MORB trace-only proxy (6 records), with original references, oxide/element mass budget, no implicit normalization or redox assumption;
4. Creates one immutable `REPORT.json` and SHA-pinned `MANIFEST.json` in a new output directory;
5. Explicitly emits `planetary_composition_field_T0=null`, `arcana_cell_assignments=0`, `fault_mineralogy_hydration...=null`, `geochemistry_to_thermo_phase_equilibrium_mapping=null`, `ore_deposit_resource_field=null`, `Deep_X_accessibility_field=null`, `mechanical_solve_authorized=false`, `physical_T1=null`.

`tests/test_r6_t0_geochemical_reference_library.py`: published-source bytes/contents, exact-source R6 cardinalities, FeO* caveats, unit/missing-oxide rejection, water not inferred and write-once reports.

**FAIR not yet run on this development code.** Source data files have been independently compared byte-for-byte by Git blob SHA to upstream Git objects; the Python analysis, source-native runtime and defined new regression have not yet been executed on FAIR. Do not report 6 valid compiled records until runtime succeeds.

## V. Decision that can advance real ARCANA chemistry

Once FAIR source-data integration is reproducible, we need an explicit **authorial initial compositional hypothesis** with selectable scientific analogues but no assumed spatial assignment. A defensible first experiment would require:

1. An independent T0 **original support-to-bulk-composition** provider, tied by cell ID and plate provenance, distinguishing continental crust source facies, oceanic crust source facies, regional sediment/melt/alteration, mantle source and boundaries; uncertainty should not collapse into a universal Earth default.
2. A material model with exact **bulk elemental oxide chemistry**, trace isotope/element units, valence/oxygen redox, volatile contents and water fugacity/fluids, with explicit `null` when unknown. A bulk chemical composition alone does **not** determine modal mineral assemblage: selecting P/T, oxygen fugacity, fluid activity and a thermodynamic database is a separate petrological closure. Perple_X or an equivalent phase equilibrium provider is relevant only once those inputs and their validity are fixed.
3. A conserved **tectonic material transport history** and crust formation/remelting/recycling processes to generate mineral geographies T0→T1, rather than imprinting a static map at each later time. Actual economic ore deposits additionally demand enrichment processes, fluid movement, mineral precipitation, erosion and redistribution; multiplying Earth oxide fractions by thickness is not a deposit map.
4. A rock-specific G2 creep, brittle law and fault-gouge model with valid P/T/rate/fluids envelopes and mechanical sidedness; plus G3 mantle/boundary physical loads. R6's 20°C laboratory frictional analogue does not automatically cover real T0 P/T.
5. Only after these physical fields have been validated, use the geology/mineral structure and actual Deep-mode coupling to construct Deep `f_X`, accessibility `zeta` and recoverable resources. Do not infer magical energy from oxide weight percentages.

This is a **true reference-data acquisition** stage, not a source-supported assignment of ARCANA minerals. No T0/T1 or HistoryStore write is authorized.

```text
T0_EARTH_OXIDE_REFERENCE_TABLES=PINNED_2
T0_EARTH_TRACE_REFERENCE_TABLES=PINNED_1
EARTH_BULK_CONTINENTAL_REFERENCES=4
EARTH_DEPLETED_MANTLE_REFERENCES=1
EARTH_N_MORB_TRACE_ONLY_REFERENCES=1
ARCANA_T0_BULK_CHEMISTRY_SPATIAL_ASSIGNMENTS=0
ARCANA_T0_MINERAL_PHASE_SPATIAL_ASSIGNMENTS=0
ARCANA_T0_FAULT_GOUGE_SPATIAL_ASSIGNMENTS=0
ARCANA_T0_ORE_RESOURCES=null
ARCANA_T0_DEEP_SPATIAL_ACCESSIBILITY=null
PHYSICAL_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```
