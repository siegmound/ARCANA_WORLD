# ARCANA R6 — Source-bound original T0 lithostatic P–T reference (not physical T1)

**Date:** 2026-11-22.  
**Branch:** `r6/t0-source-lithostatic-pt-20261122`.  
**Parent integrated R6:** `042545cc8e86eb39770d54be697a2216062e05a9`.  
**Decision:** `ORIGINAL_T0_CONDITIONAL_LITHOSTATIC_PRESSURE_AND_EXACT_THERMAL_PT__NOT_PHYSICAL_STRESS`.  
**Scientific state:** numerical implementation completed; **FAIR original-source execution pending**.  
**Governance:** D-024 ACTIVE; `physical_T1=null`; no mechanical solve, WorldHistory/HistoryStore or canon edits.

## Why this development produces genuine numerical physics rather than another source list

The original FAIR 42/410 T0 source packet and 41/451 source-to-coupled handoff already preserve 81/289 original parent-node IDs, 128/512 basal triangles, 32/64 original external cut edges and per-node source PRE material-density/temperature metadata. They are fully provenance-bound but provide *no* actual stress, mineralogy, fault gouge, fluid effective pressure, deep-mantle traction or constitutive law. Treating a new null-valued template as a physical simulation would not advance the science.

The next safely derivable **physical equation** is a **conditional column weight balance** from original PRE crust/mantle thicknesses and densities, plus the canonical gravity value declared in an existing exact-pinned R6 source scenario. This yields an interpretable **vertical overburden pressure increment relative to the model's surface**, Δσ_v(z), with a mathematically exact pressure integral, the original thermal polynomial profile T(z), and a quantitative lab temperature-domain screening *per source parent node*. This is neither an arbitrarily prescribed traction nor an absolute physical pressure.

## Equations and units

For source PRE downward depth z, original crust thickness Hc and lithospheric mantle thickness Hm, original PRE densities ρc,ρm, and source-declared planet gravity g=9.82 m s⁻²:

\[
\Delta\sigma_v(z)=
\begin{cases}
 g\rho_c z,&0\le z\le H_c,\\
 g(\rho_c H_c+\rho_m(z-H_c)),&H_c<z\le H_c+H_m.
\end{cases}
\]

Pressure jump at the Moho **relative to model surface**: `g*rho_c*Hc` Pa. Pressure increment at source-model lithosphere base: `g*(rho_c*Hc+rho_m*Hm)` Pa. Exact integrated pressure increment (not GPE):

\[
\int_0^{H_c+H_m}\Delta\sigma_v(z)\,dz=
 g\left(\frac{\rho_c H_c^2}{2}+\rho_c H_cH_m+\frac{\rho_m H_m^2}{2}\right)
\quad[\mathrm{Pa\,m=N/m}].
\]

Checks: positive density and thickness, original contiguous layer z bounds, monotone positive pressure, exact equality to independent trapezoid integration of both linear layers, finite results and depth-in-domain. At each node **ten** depth samples, including both crust and mantle sides of the original Moho, report the original PRE source cubic polynomial `T_i(z)=c0+c1*(z-z0)+c2*(z-z0)^2+c3*(z-z0)^3`. Exact within-layer temperature extrema are obtained by **reusing the previously FAIR-tested** `g2_exact_thermal_validity.exact_layer_temperature_bounds_k` (including internal extrema), not just five sampling points.

**Fundamental physical boundary:** Δσ_v(0)=0 is a **pressure difference**, NOT a claim that absolute surface fluid/pore/dynamic/tectonic pressure equals zero. No elevation-dependent seawater load, gravity-potential gradient, pressure boundary condition, normal traction on arbitrary dipping faults, effective pressure, fault depth, or mechanical LAB is inferred. Local zero overburden *increment* at the top cannot be consumed as physical `p_pore=0` or `fault_normal_pressure=0`.

## Provenance and source constraints

- The exact pre-existing `G2_G3_PAIRED_PHYSICAL_SCENARIO_V1.json` is Git-blob pinned to `7b182347014747f14ffcd591bdcf4f7f87640e87`; the scenario declares `g3.gpe.gravity_m_s2=9.82` and `gravity_authority=CANONICAL_PARAMETER`, but itself is an unratified engineering **scenario**. This new code uses only the declared gravity as a model parameter, not the scenario's unratified load/rock assumptions.
- The same pinned scenario declares an Earth wet-quartzite GT95 laboratory **temperature window** `1173.15–1373.15 K`, DOI `10.1016/0040-1951(95)00011-B`, and `arcana_rock_identity_ratified=false`. The code measures true PRE temperature-range *intersection* and *whole-layer temperature-only* inclusion, one node at a time; it **never** treats the laboratory pressure ~1.5 GPa as a certified pressure interval, or infers unmeasured rate/water/stress invariants or Arcana rock identity.
- The code independently opens and SHA256-verifies both prior immutable original `R6_G2G3_PHYSICAL_SOURCE_PACKET_{8X8,16X16}_NEW02` outputs and source SHA-chain correspondence. It also verifies the unselected full-parent `R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01` `MANIFEST.json`, both scenario files and its `AUDIT.json`, with exact source-index references. Four provider hashes are common between regions; FEG/PRE hashes are **different** for the original 8×8 and 16×16 regions.
- Uses the source original 81-node **8×8** as the first regional reference and 289-node **16×16** for domain-extent sensitivity. Common original node IDs are tracked and any changes in conditional pressure increments are **reported** but not concealed or silently interpreted as mesh convergence. No numerical solver time-step or physical T1 is evaluated.

## Files and FAIR evidence

`experiments/plate58_deforming_explore_v1/g2_g3_t0_lithostatic_pt_reference.py`

`tests/test_r6_g2_g3_t0_lithostatic_pt_reference.py`

`scripts/r6_g2g3_t0_lithostatic_pt_fair_gate.sh`

Local portable tests: **36/36 PASS**, verified on synthetic unit fixtures only. FAIR gate expected **36 new** and **487 total selected** (prior 451 cases **plus** new 36, including the 36 in the 487). The FAIR execution, authentic-source numerical ranges, actual GT95 applicability counts and independently hashed evidence **are not yet known**.

From a clean detached checkout of the published experimental SHA, activate `arcana-r6-linux` and run:

```bash
bash scripts/r6_g2g3_t0_lithostatic_pt_fair_gate.sh
```

Reads immutable source directories, writes external **NEW01** evidence under `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/`:

```
R6_G2G3_PT_REFERENCE_TARGET_36_NEW01.log
R6_G2G3_PT_REFERENCE_SELECTED_487_NEW01.log
R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01/
  REGION_8X8_SOURCE_PT.json
  REGION_16X16_SOURCE_PT.json
  AUDIT.json
  MANIFEST.json
```

The output is write-once, outside the repository. Its manifest SHA256 hashes all three generated data files. Every source node records Moho/base Δpressure [Pa], exact within-layer temperatures [K], ten paired P–T samples and the exact pressure integral [N/m]. The audit carries the unchanged source packet/handoff manifest hashes, the original two regions and explicit `no_GPE_or_mantle_coupling_generated=true` for source data. The FAIR gate checks counts, finite numbers, authority markers, no use as actual normal pressure or T1, and input hash retention. Any FAIL retains previous evidence and prevents integration.

## What physical qualification remains (not claimed here)

This increment **does not close any of the eight original physical authority groups**. Before any real G2/G3 coupled mechanics or WorldHistory production, the project must still select and source: actual Arcana T0 lithology/phase/hydration and water/pore pressure/Biot field; valid stress invariant, rate and P/T creep law and low-T brittle mechanism; *actual* cut and all basal tangential and **normal** tractions including the eight source core facets; independent deep-mantle flow, vertical reference and mechanical LAB; single-owner GPE; explicit sided fault law/true junction DOFs; validated nonlinear solver with rank, force, torque, work, energy and restart tests. The upper surface load must be sourced and its relationship to the 1D pressure reference physically justified. Earth analogues cannot fill these missing properties by default.

**After this FAIR**, the next actual model step should be to propose one explicitly authored 8×8 lithology/hydration/constitutive hypothesis within these measured source temperature/conditional pressure domains, and quantify compatibility/rejection before independently deriving mechanical boundary loads. The 16×16 case is for domain-extent comparison only. Do not automatically scale synthetic geological history or write resource/Deep/flora/fauna history on this reference.

```text
SOURCE_T0_CONDITIONAL_OVERBURDEN_AND_PT=DEVELOPMENT_IMPLEMENTED_FAIR_PENDING
REAL_ORIGINAL_T0_PRESSURE_T_PROFILE_NUMERICAL_READBACK=FAIR_PENDING
ACTUAL_SURFACE_PRESSURE=UNKNOWN
ACTUAL_PORE_OR_FAULT_NORMAL_PRESSURE=UNKNOWN
ACTUAL_ROCK_PHASE_AND_CREEP_FIT=UNKNOWN
ACTUAL_G3_MANTLE_CUT_BASAL_GPE=UNKNOWN
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```
