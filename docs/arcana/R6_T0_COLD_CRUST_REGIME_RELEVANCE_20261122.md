# ARCANA R6 — Original-T0 cold-crust brittle/plastic relevance: first conditional rheology stage

**Date:** 2026-11-22. **Integrated starting R6 HEAD:** `b095c051d55589e28546be49c9db603c8f409cea`.  
**Development only:** isolated branch `r6/g2-cold-crust-rheology-relevance-20261122`.  
**Decision:** `ORIGINAL_T0_COLD_CRUST_MECHANISM_RELEVANCE_IMPLEMENTED__G2_MATERIAL_AND_FAULT_LAW_UNSELECTED__FAIR_PENDING`.  
**D-024:** ACTIVE. `physical_T1=null`. `mechanical_solve_authorized=false`. No HistoryStore or WorldHistory production.

## Why a contextual study, not a fabricated full-rheology law

The exact original source 8×8/16×16 T0 region and source PRE input have been authenticated on FAIR, and the source conditional P–T model passed **36/36 targeted and 487/487 selected** cases on exact SHA `38f68c329751520849745dad6f2c9c022b78b59e`. The entire crust in both source extents has **zero** temperature-only overlap with terrestrial GT95 wet quartzite laboratory 1173.15–1373.15 K. A complete warm-quartzite constitutive law cannot be extrapolated downward and passed as natural Arcana creep. 8×8 original Moho conditional Δσv is 0.769888–1.3748 GPa, lithosphere base Δσv 2.455–4.20296 GPa. These are 1-D *incremental vertical model overburden* values, not normal effective pressure on real faults or observed tectonic stresses.

Published work distinguishes brittle friction/slip, pressure–temperature–strain-rate-dependent semibrittle mechanisms, and low-temperature plasticity that can coexist in quartz-rich *terrestrial* crust. No single temperature by itself assigns the mechanism; mineral/phase, hydration, pressure, strain rate, geometry and tectonic stress are required. Rather than assigning an unratified default granite/quartzite or a friction coefficient to plates 5,8,11, this stage quantifies exactly **which original T0 crustal depth intervals** intersect one **explicitly non-universal Earth contextual BPT temperature corridor**, and reports conditional overburden there with null fault-effective pressure and null laws.

## Scientific reference register, explicitly Earth's-only

- **Quartz-rich continental-crust qualitative BPT context 250–350 °C (523.15–623.15 K)**: *Geochemical, Mineralogical, and Fluid Processes in the Brittle-Plastic Transition of Continental Crust*, Geochemistry, Geophysics, Geosystems (2024), DOI `10.1029/2024GC011446`, <https://doi.org/10.1029/2024GC011446>. This range is **an indicative context associated with quartz-rich crust**, NOT a laboratory fit domain, universal transition depth, or observational inference about Arcana. Comparisons of temperature alone establish neither brittle nor plastic dominance.
- **Byerlee terrestrial sliding friction reference**: Byerlee (1978), *Friction of rocks*, *Pure and Applied Geophysics* 116:615–626, DOI `10.1007/BF00876528`, <https://pubs.usgs.gov/publication/70012542>. The module includes a strictly opt-in **pure Earth benchmark operator** τ≈0.85 σ′ₙ below 200 MPa and τ≈50 MPa +0.6 σ′ₙ between 200 and 1700 MPa for common-rock sliding, using positive **independently supplied effective normal stress**. It never uses model vertical Δσv as fault σ′ₙ and never runs on the real original nodes. Clay/weak mineral gouge, hydration/temperature/rate and actual fault orientation may invalidate this analogue.
- **Low-temperature plasticity and fracture complexity**: *Low-temperature plastic rheology of granitic feldspar and quartz* (2023), <https://www.sciencedirect.com/science/article/pii/S0040195123001488>; *Testing constitutive equations for brittle-ductile deformation associated with faulting in granitic rock* (2017), DOI `10.1002/2017JB014000`, <https://doi.org/10.1002/2017JB014000>. These provide discussion of mechanisms, **not** a validated all-regional P/T/rate creep parameter set for the original source planet.

## New code

`experiments/plate58_deforming_explore_v1/g2_g3_t0_cold_crust_regime.py`:

1. Reopens the original immutable 8×8 and 16×16 FAIR `NEW02` source packet directories. Reopens immutable `NEW01` full-parent coupled handoff and the verified `NEW01` conditional lithostatic P–T report including exact SHA256 output manifests. It **independently reruns the earlier P–T computation** and checks full report and audit dictionaries equal; no stale or swapped source reports are accepted.
2. For each original crust PRE cubic T(z), finds all exact-isolated boundary intersections with `523.15 K` and `623.15 K`, splitting into monotone arcs at derivative roots and solving for thresholds with bracketed bisection. Handles nonmonotone cubic, multiple disjoint depth bands, constant profiles, boundaries and finite-width contact correctly. Does **not** identify a true mechanical transition.
3. At the endpoints of each nonzero-width Earth-context temperature interval, evaluates **only** Δσv = ρ_crust * g * depth, preserving source model density and gravity and the unknown real surface stress. Emits **null** actual σ′ₙ, fault stress, pore pressure, mineral phase, brittle law, ductile law, P/T/rate material qualification, true BPT depth, mantle tractions and GPE.
4. Retains the exact original region IDs and actual regional triple-junction semantics (`34587` is in 8×8 footprint but no local 3-plate junction; 16×16 has incident plates 5/8/11), preserving the 8 unresolved physical groups, explicit D-024 block, and no HistoryStore mutation.
5. Writes fresh, **write-once external** `REGION_8X8_COLD_CRUST.json`, `REGION_16X16_COLD_CRUST.json`, `AUDIT.json`, and SHA256 `MANIFEST.json` and never modifies old FAIR outputs.

The unit tests are deliberately synthetic **only** for mathematical correctness, not geological assignment. They cover analytically checkable constant/linear/cubic profiles, multiple disjoint temperature windows, strict null-pressure/rock-law states, pure Earth friction-operator reference and domain limits, hash tampering, report scope, and non-overwriting authoring outputs.

## FAIR validation contract

Target **51 new** test cases. Combined **538 selected R6 tests including 51** (not 538+51). Authentic FAIR source/conditional P–T readback must produce two regional noncanonical thermal-context reports and no physical law assignment.

Runner: `scripts/r6_g2g3_t0_cold_crust_regime_fair_gate.sh` on a **clean detached, exact development commit**, activated `arcana-r6-linux`, from repository root. Uses existing certified evidence:

```
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
  R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01/
  R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01/
```

Creates fresh, non-overwriting output:

```
R6_G2G3_COLD_CRUST_TARGET_51_NEW01.log
R6_G2G3_COLD_CRUST_SELECTED_538_NEW01.log
R6_G2G3_T0_COLD_CRUST_REGIME_NEW01/
  REGION_8X8_COLD_CRUST.json
  REGION_16X16_COLD_CRUST.json
  AUDIT.json
  MANIFEST.json
```

**FAIL path:** any test/scientific-source mismatch leaves all prior evidence intact; do not integrate. **PASS path:** compare new executable, test and runner Git blob SHAs with the exact FAIR-tested SHA, then consider software-only no-force fast-forward in the R6 integration branch. No automatic T0→T1 permission.

## Next real model-authority work

With quantified original depth intervals, the next required substantive decision is a **specific, explicitly proposed 210 Ma regional material/phase composition**, hydration and pore-fluid state; a compatible, independently calibrated brittle/frictional + low-temperature plastic/ductile constitutive law over the actually computed temperature/pressure/strain-rate/stress-invariant domains, including an *explicit* cross-over rule. Then require real fault-sidedness/traction/normal pressure, independent 32 cut + 128 basal G3 loads including core, GPE vertical single owner, mantle reference flow and nonlinear balance/rank/restart. An Earth reference is not an authorial mineral map. **No canonical geology, ore, Deep or history** follows from this diagnostic alone.
