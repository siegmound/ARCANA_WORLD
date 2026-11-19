# ARCANA R6 — Paired G2/G3 physical scenario, single regional EXPLORE

**Date:** 2026-11-19. **Parent:** `df3776ce10a4f4b14daedbffd4bd351fe2ac5529`. **Decision:**
`G2_G3_COUPLED_REGIONAL_EXPERIMENT_FAMILY_SELECTED__PHYSICAL_PARAMETERIZATION_OPEN`.

This is a **substantive model-family selection**, not a new geometrical
gate, not parameter ratification, and not a mechanical calculation. The
machine-readable companion is
`experiments/plate58_deforming_explore_v1/G2_G3_PAIRED_PHYSICAL_SCENARIO_V1.json`.

## Model selected

**A single, source-keyed spherical faceted thin-lithosphere EXPLORE
continuum**, retaining original PRE columns, 5:8:11 plate source topology,
the original parent node IDs, and a two-layer nonlinear constitutive potential
with independent crust/mantle creep exponents. Use the already implemented
source-bound G3 A regional continuum for exterior transfer. Prefer a separately
versioned engineering experiment to an unqualified patch to original SHELLS:
SHELLS shares `eCreep` across crust/mantle in `Diamnd`, `Mohr`, `OneBar`.
The currently implemented smooth-cap response is **not** a complete
elastoplastic/frictional fault model and does not establish SHELLS equivalence.

Reference domain: 8×8 (5/8), 81 nodes and 120 exterior facets. Sensitivity:
16×16 (5/8/11), 289 nodes and 504 exterior facets; triple source parent
node `34587`. These are domain extents, not mechanical mesh convergence.

## G2: assign only validated physical roles

1. SOURCE_AUTHENTIC: PRE thermal cubic, density and two-layer thickness with
   absent/present flags. 51 input fields per node. `material_configuration_code`
   does not prove rock identity; zero numerical chemical-density reference
   does not prove absence of real compositional heterogeneity.
2. ENGINEERING_CANDIDATE: two independent non-Newtonian creep exponents
   with pressure, temperature, rate and water validity requirements; a 3D
   pressure-aware Drucker–Prager smooth harmonic cap. Choose **6P** as the
   reference *ASPECT Rheology::DruckerPrager convention*, preserve 2P as a
   separately labeled sensitivity, never mix. No claim that smooth-cap
   is a nonassociated return-mapping plasticity or fault weakening law.
3. LITERATURE_ANALOGUE_EXPERIMENT only: Byerlee 1978 friction concerns
   sliding surfaces, not an automatically equivalent continuum law.
   GT95 quartzite `n≈4` and calibration around 1173.15–1373.15 K,
   whereas source T0 crust spans ~280–1051.558 K. **GT95 is inapplicable
   to the reported full T0 crust**. Dry olivine n≈3.5 remains an Earth
   benchmark, not an ARCANA mantle mineral assignment.
4. UNKNOWN: rock-specific material fractions, depth-resolved hydration,
   pore pressure/Biot, stress-invariant conversion to tested laws,
   experimental P/T/rate coverage, damage/fault rules and element mixing.
   The adopted model family therefore cannot be run as physical G2 today.

Scientific evidence:
- GT95 https://doi.org/10.1016/0040-1951(95)00011-B
- Quartzite experimental comparison https://doi.org/10.1002/2016JB013798
- Byerlee https://doi.org/10.1007/BF00876528
- ASPECT 6P https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1Rheology_1_1DruckerPrager.html
- ASPECT legacy 2P https://aspect-documentation.readthedocs.io/en/latest/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html

## G3 A: unique gravitational force owner and real continuum transfer

Use `g=9.82 m/s²` from **canonical R6 authority**. Retain
`z_ref=-200 km` as **engineering Earth analogue** only. The source FEG
height field is `NUMERICAL_DERIVED_SUPPORT`; a numeric GPE magnitude
cannot validate ancient topography. The candidate GPE has a single owner
`EXPERIMENTAL_EXTERNAL_GPE_ONLY__ORIGINAL_SHELLS_GPE_NOT_COMBINED`.
Never add it to internal SHELLS `Squeez`/`Fixed` GPE.

The consistent tangent momentum budget separates
`F_outer_cut + F_basal_tangential + F_GPE`. Its normal-pressure
closure is a separate requirement, not a free balancing reaction.
The source outer cut requires 32/64 tractions and exterior
base requires 120/504 triangle entries. The Euler velocities are
kinematic priors: **the 5:8:11 triple node is still one mechanical
East/North degree-of-freedom pair**, not three imposed Dirichlet fields.

Candidate basal constitutive research route is
`tau_b=beta_b*(v_deep_mantle-v_lithosphere)`, with
`beta_b=eta_asthenosphere/H_coupling`. This equation is **not active**:
`eta_asthenosphere`, `H_coupling`, and deep-mantle velocity remain null.
Outer-cut transfer is to be derived from a sourced regional/global
mechanical continuum and shared-node force balance, not guessed from
Euler speed or arbitrary zero traction.

The candidate GPE norms ~1.6833e18 N (8×8) and ~5.1533e18 N (16×16)
are **L2 norms of different discrete nodal vectors**, not equilibrium
or numerical convergence evidence.

Scientific context:
https://doi.org/10.1029/2007JB005460
https://se.copernicus.org/articles/13/583/2022/

## The *next* substantive unit, not another geometric microgate

**Integrated physical-source selection, using existing providers where
possible**: establish ARCANA T0 lithology and hydration with authoritative
provenance; qualify full temperature/pressure/strain-rate constitutive
coverage and brittle fault/damage response; establish deep mantle/cut
traction source fields and vertical reference; reconcile the unique GPE
owner with the selected solver. Each unknown stays `null`, not zero.

After this science-led parameterization, check joint rank/gauge,
force/torque/virtual work and 8×8→16×16 sensitivity using **the same**
selected physical law, then explicitly adjudicate bounded mechanical
EXPLORE authorization. No automatic T1.

| Gate | Current |
|---|---|
| Model family selected | YES (noncanonical EXPLORE) |
| G2 physical rock/creep/fluid law | OPEN |
| G3 cut/basal/vertical force physics | OPEN |
| One-owner GPE accounting | ENGINEERING PASS; physical closure OPEN |
| Full SHELLS or alternate EXPLORE solver parity | OPEN |
| Mechanical solve authorized | NO |
| D-024 | ACTIVE |
| physical_T1 | null |
