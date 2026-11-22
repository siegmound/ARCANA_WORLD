# ARCANA R6 — Original T0 cold-crust G2 material, fluid and constitutive-law experimental bridge

**Date:** 2026-11-22. **Integration base:** `r6/multiphysics-integration-20261026` at `a2c285ba22f2dbc40bda9d1c097989c0a7e1f249`.  
**Isolated development branch:** `r6/g2-t0-material-fluid-law-trial-20261122`.  
**Decision:** `G2_T0_EXPLICIT_MATERIAL_TRIAL_ENGINE__SOURCE_LITHOLOGY_UNSELECTED__FAIR_PENDING`.  
**Governance:** `D-024 ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## 1. Why this is not another thermal inventory

The preceding original-source FAIR G2 sequence has shown that the two regions have **no** wet quartzite GT95 temperature-only laboratory overlap (1173.15–1373.15 K), whereas the terrestrial quartz-rich *contextual* 523.15–623.15 K zone intersects 81/81 source 8×8 nodes and 248/289 source 16×16 nodes. Neither observation selects natural mineralogy, brittleness, a fault slip law or a mechanically true transition. We must now make **candidate material and fluid hypotheses testable by actual constitutive equations** and unconditionally reject invalid T/P/rate or stress-invariant transfers. This stage implements that numerical capability, but does not choose the geologic material on behalf of the author.

## 2. Concrete mathematical engineering increment

`experiments/plate58_deforming_explore_v1/g2_t0_material_trial.py` provides:

**A. Noncanonical continuum brittle reference** (modern ASPECT Drucker–Prager **3D, 6P** convention, not a fault Coulomb/slip law):

\[
\sigma_{\mathrm{DP}}=\frac{6c\cos\varphi+6P_{\mathrm{eff}}\sin\varphi}{\sqrt 3\,(3+\sin\varphi)}.
\]

Required inputs are source-named candidate cohesion `c` [Pa], friction angle `phi` [degrees], **conditional continuum effective pressure** [Pa], temperature [K] and strain rate [s⁻¹], all with explicit empirical applicability ranges. The code rejects legacy 3D **2P** pressure convention and values outside the supplied envelopes; the equation is a material candidate, not an independently measured fault traction.

**B. Noncanonical triaxial differential-stress creep reference**:

\[
\dot{\epsilon}=A\sigma_d^{n}\left(\frac{f_{\mathrm{H_2O}}}{f_{\rm ref}}\right)^r
\exp\left[-\frac{E+PV}{RT}\right]
\quad\Rightarrow\quad
\sigma_d=\exp\left[\frac{\ln\dot{\epsilon}-\ln A-r\ln(f/f_{\rm ref})+(E+PV)/(RT)}{n}\right].
\]

The input requires `A [Pa^-n s^-1]`, `n`, `E [J/mol]`, `V [m³/mol]`, water-fugacity exponent `r`, independent water fugacity (when `r>0`), explicit pressure and source-provenanced **temperature / confining-pressure / strain-rate validity bands**. Its output is **triaxial differential stress** [Pa], not the Drucker–Prager continuum J2-equivalent invariant. These two stresses are not equated, minimized or interpreted as a physical brittle–ductile crossing without an independently validated invariant transformation and mechanics law.

**C. Full-crust exact PRE T and conditional P/rate screening**. For one author-supplied T0 material candidate at an original parent node, the engine checks that **both** proposed mechanism validity envelopes cover the *entire* original exact PRE crust temperature interval. The caller must explicitly supply hypothetical `surface_total_pressure_pa`, pore pressures at the surface and Moho, Biot coefficient, hydration, strain rate and noncanonical authorial selection record. The previously verified source gravity-weight pressure **increment** supplies only `P1-P0`: it is NOT substituted for real absolute pressure or the fault normal load. An author-specified *linear pore-pressure interpolation* is a provisional hypothesis, not hydrology. The engine can numerically evaluate the separate brittle and ductile stress ranges at conservative endpoint bounds, not a true constitutive transition. Invalid domain coverage fails closed.

**D. Exact original regional node + oxide-candidate linkage.** An unselected source-authored pair of region records contains 81 and 289 exact original source parent IDs, the individually SHA-authenticated original T0 FEG/PRE, cold-context and conditional P–T report IDs, **all material assignments null**, no assumed fluid state and no fault-side split. A separate optional **in-memory authored trial evaluator** accepts a candidate material record for each of the **81 original 8×8 parent nodes**, with no fallback material or missing-node interpolation. It can read a self-hash-consistent report from the prior `experiments/t0_authorial_composition_v1/provider.py` and link an exact **authorial bulk-oxide candidate** ID. Such oxide ratios **do not determine mineral phase** and the previous native 1° geography is not automatically a source-parent / fault-side placement. This attachment is not independent laboratory-data authentication or an authorial geology ratification.

The original parent IDs may be shared between plates. A per-parent **continuum column hypothesis is not a separate plate-side rock identity**, a fault-gouge identity or an independent displacement jump. The authentic 8×8 has no local 3-plate junction, even though parent 34587 can belong to its regional footprint; the original 16×16 has 5:8:11 junction at 34587. The adapter refuses to silently construct side-specific physics.

## 3. Published terrestrial references and nontransferable bounds

Earth analogues are retained for **research alternatives**, never automatically selected material for ARCANA.

- 2023 Sly et al., *Low-temperature plastic rheology of granitic feldspar and quartz*, Tectonophysics 858 (2023) 229850, https://doi.org/10.1016/j.tecto.2023.229850: low-temperature plasticity can be investigated in quartz/feldspar, but nanoindentation and nature-scale rheology cannot be interchanged without mechanism/rate/geometry calibration.
- 2025 quartz–albite mixtures, https://doi.org/10.1029/2025JB031249: material mixtures and pressure affect the brittle–plastic transition; the findings do not identify original ARCANA mineralogy.
- 2026 quartz-gouge ring-shear experiments, https://doi.org/10.1029/2026JB033942: reported experiment includes effective normal stress **50 MPa**, fluid pressure **100 MPa**, temperature **25–650 °C**, and slip velocities **1 nm/s–300 μm/s**. These are **specific Earth fault gouge laboratory conditions**: the tested slip-velocity interval is NOT bulk strain-rate without an independently known deformation width; its effective fault pressure cannot be derived from original ARCANA 1D lithostatic increment.
- Existing R6 GT95 reference DOI `10.1016/0040-1951(95)00011-B` does NOT overlap original regional T0 crust temperature. The contextual 250–350 °C corridor remains a qualitative study of terrestrial quartz-rich crust, not a law validity range.

The current numerical unit tests use **explicitly synthetic** lab coefficients and synthetic oxide records to verify units, signs, monotonicity, overflow checks, uncertain water, guards and source coverage. These values are neither measured data nor chosen ARCANA geology. The code labels hypothetical lab datasets as unverified. A SHA from a self-supplied candidate document establishes file consistency, not scientific validity of its content.

## 4. FAIR test and authentic source readback

New target: **67 tests**. Previous selected regression: **538**. New combined selected target: **605** (includes the 67, not 605+67). The complete **67/67** new targeted tests run locally with test-only synthetic fixtures and pass; the source-original FAIR execution is **pending**. Tests cover conditional pressure/temperature/fluids, pore Biot constraints, both stress conventions, stress/rate/temperature applicability, water-dependent creep, numerical overflow, original node coverage, SHA-hardened prior source/published-candidate integrity, malformed authorship, simulated full regional trial and original evidence reconstruction failure cases.

FAIR clean detached SHA, activated `arcana-r6-linux`, repository root:

```bash
bash scripts/r6_g2_t0_material_trial_fair_gate.sh
```

Read-only existing FAIR original evidence:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
  R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01/
  R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01/
  R6_G2G3_T0_COLD_CRUST_REGIME_NEW01/
```

New, write-once external evidence:

```text
R6_G2_MATERIAL_TRIAL_TARGET_67_NEW01.log
R6_G2_MATERIAL_TRIAL_SELECTED_605_NEW01.log
R6_G2_T0_MATERIAL_FLUID_TRIAL_NEW01/
  MATERIAL_8X8_UNSELECTED.json
  MATERIAL_16X16_UNSELECTED.json
  AUDIT.json
  MANIFEST.json
```

The source compiler rechecks original evidence SHA, **independently replays** the old original-source conditional P–T and cold-context computation, then emits the two unselected region authoring contracts. The manifest hashes all new files. On actual FAIR run the original source nodes and mechanics authority will be rechecked before and after output. No published canonical, HistoryStore, WorldHistory, resource, Deep, flora or fauna layers can be written.

## 5. The physical decision still needed after gate

The user must eventually choose or explicitly authorize a provisional noncanonical **material hypothesis**, with original phase chemistry and spatial heterogeneity, independent water/pore-pressure and stress-state basis, and actual laboratory observation sources spanning *full original T/P/strain-rate/stress-convention* conditions. This module can then numerically screen and evaluate its strength without a mechanical solve. Until that record exists, all natural material, bulk rheology, fluid and physical-fault inputs stay `null` and physical `T1` remains forbidden. **Do not automatically pick granite, quartzite, olivine, an Earth-wide average, dry rock or zero pore pressure.** G3 cut/128 basal tractions, mantle flow, GPE vertical datum, fault sidedness and force/tangent rank closure still require independent physical qualification.

**Decision at development close:** `G2_T0_EXPLICIT_MATERIAL_TRIAL_ENGINE_IMPLEMENTED__ORIGINAL_FAIR_GATE_REQUIRED__NO_PHYSICAL_SELECTION`.
