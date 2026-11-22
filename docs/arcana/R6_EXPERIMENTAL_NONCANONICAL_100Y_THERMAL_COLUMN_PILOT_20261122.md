# ARCANA R6 — Noncanonical experiment governance and 100-year thermal-column pilot

**Date:** 2026-11-22  
**Engineering parent:** R6 main 2ecabde7f86f052ecd25eaa34a6e4042dd7f13e7, previously verified FAIR 304/304 for the selected R6 regression.  
**Development branch:** r6/experimental-thermal-column-100y-noncanonical-20261122.  
**Decision:** EXPERIMENTS_ALWAYS_NONCANONICAL__SYNTHETIC_100Y_THERMAL_COLUMN_IN_DEVELOPMENT.

## 1. Binding experimental governance

The user's standing decision is that **every experimental simulation of ARCANA WorldSim remains noncanonical**. Numerical success, FAIR test success or future completion of the simulator must NEVER automatically elevate an experimental result to canonical historical world state.

A future canonical history instead requires an independently qualified complete production simulator, valid physically sourced state and evolution, scientific and numerical validation, and explicit authorial ratification of a **new production-run lineage**. Experimental outputs are permanently retained as research evidence, never converted in place into canon.

Machine-readable governance: docs/arcana/governance/R6_EXPERIMENTAL_RUN_NONCANONICAL_POLICY.json, exact Git blob 75658d37b12ac3d2c3b3fed5b9e56203a6ae3cf1. The pilot verifies the exact bytes of this source before execution, refuses to write results inside the repository, and cannot write HistoryStore, physical T1, canonical WorldHistory, resource/ore or Deep fields.

This is a general policy applying to all experimental phases, not a claim that the present source code can itself police future unrelated simulation tools. Those tools must honor the same policy.

## 2. Scope of the first 100-year calculation

This is a deliberately **synthetic, noncanonical** one-dimensional, 100-Julian-year thermal-diffusion experiment. Its goal is to validate a numerical reduced model with an exact analytic solution, not to predict the natural 210 Ma crust of ARCANA or solve global G2/G3 mechanics.

The source anchor is the previously authenticated native T0 model cell R6G1D-R089-C359 (plate ID 8 in original 0..11 source, NORMAL_OCEANIC, model crust thickness 6500 m). The 1000 m simulated depth is a **chosen experimental subcolumn**, NOT a physical vertical grid extracted from T0.

Original SHA-verified B-v2 and plate-partition NPZ packages are read using the existing source adapter; the material reference configuration R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json (exact Git blob e041e7dc91f617cf7f755b46ab36e7417d486fd0) supplies these **authored specialist reference model values**, NOT natural cellwise measurements:

| Parameter | Chosen model value | Authority |
|---|---:|---|
| Ocean crust density | 2890 kg/m³ | Authorial thermal reference |
| Heat capacity | 1000 J/(kg·K) | Authorial thermal reference |
| Conductivity | 2.2 W/(m·K) | Authorial thermal reference |
| Uniform bulk heat production | 3 × 10^-7 W/m³ | Authorial thermal reference |
| Column thickness | 1000 m | Explicitly synthetic experiment |
| Initial temperature | T(z,0) = 300 K + 15 K cos(pi*z/L) | Explicitly synthetic experiment |
| Surface and basal boundary heat flux | 0 at each end | Explicitly synthetic insulated boundary |
| Duration | 100 Julian years | Numerical experiment only |

The mathematical problem is rho*Cp*dT/dt = k*d2T/dz2 + Q, with zero normal heat flux on both faces. Because the chosen cosine has zero derivative at both ends, the exact solution is

    T(z,t) = 300 + 15*cos(pi*z/L)*exp[-k/(rho*Cp)*(pi/L)^2*t]
             + Q*t/(rho*Cp).

The initial thermal profile, heat boundaries and thickness are NOT approved ARCANA T0 physical state. The historic temperature field remains unknown.

## 3. Numerical correctness requirements

The module src/arcana_worldsim/r6/experimental_thermal_column.py implements a cell-centred, conservative finite-volume explicit Euler scheme. Neighbor face fluxes cancel algebraically, so closed boundaries require integrated column energy change equal to volumetric Q * L * elapsed seconds.

Three refinement experiments share a fixed diffusion CFL about 0.06006, well under the 1D explicit stability ceiling 0.5:

| Cells | Spatial grid | Internal step | Number of 100-year steps |
|---:|---:|---:|---:|
| 50 | 20 m | 1 year | 100 |
| 100 | 10 m | 0.25 year | 400 |
| 200 | 5 m | 0.0625 year | 1600 |

Require an explicit source-drift and governance check, stability of each run, finite energy residual within declared numeric tolerance, **strictly decreasing** maximum absolute error versus the exact analytic synthetic solution, and error below 0.001 K at finest resolution. Failing the gate must stop generation of a successful report.

The report describes only a **synthetic experimental trajectory**. It preserves the authenticated source IDs, identifies all thermal coefficients as authorial reference values, writes a SHA-verified immutable evidence report to a NEW directory outside the repository, and always reports physical_T1 = null, zero HistoryStore writes, and zero natural ore/Deep/mineral assignments.

## 4. Distinction between short pilot and future world history

**100 years**: the current pilot may proceed as a synthetic numerical benchmark, provided FAIR tests and authentic original T0 source reader succeed. Its analytic solution validates a reduced algorithm, not the historical temperature, stress, landscape, groundwater, flora, fauna or resources.

**1000 years**: intentionally outside the current pilot's allowable configuration. It requires separate convergence and applicability qualification after the 100-year evidence. Even if later simulated, it remains noncanonical.

**Actual ARCANA T0→T1**: still fails the prior 100-/1000-year physical GO/NO-GO gate (no authorized T0 thermal profile / full evolution law / complete G2-G3 forces and material chemistry / boundary history). D-024 remains ACTIVE. Original physical_T1 remains null.

## 5. FAIR validation — pending

A fail-closed, evidence-preserving FAIR gate script is included at **scripts/r6_experimental_thermal_100y_fair_gate.sh**. It executes 34 targeted cases, 338 selected R6 regression cases, real source-verified synthetic 100-year numerical evolution and independent SHA/energy/analytic/no-canon assertions, in that order. Launch with **bash scripts/r6_experimental_thermal_100y_fair_gate.sh** from the checkout root in arcana-r6-linux. It refuses pre-existing log and report paths, without modifying or deleting earlier evidence. If a test fails, do not reinterpret a later result as qualified; create a distinct evidence name for any new FAIR attempt.


No new FAIR 100-year benchmark result is claimed in this development stage. A previously validated selected R6 suite of 304 tests is the parent baseline. New tests in tests/test_r6_experimental_thermal_column_100y.py are **34 expected pytest cases**, targeting governance source SHA, reference-coefficient identity, synthetic input authority, 1000-year rejection, CFL, exact analytical benchmark, convergence, energy conservation, source adapter no-T1 rule, write-once report and exclusion of repository output. Therefore selected extended suite expectation is 304+34 = **338**, contingent on unchanged collection.

After source/test checks PASS, execute this explicitly noncanonical experiment on FAIR:

    BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
    python -m arcana_worldsim.r6.experimental_thermal_column \
      --repo-root . \
      --config experiments/thermal_column_100y_v1/SYNTHETIC_OCEANIC_REFERENCE_COLUMN.json \
      --output "$BASE/R6_EXP_THERMAL_100Y_NONCANONICAL_NEW_01"

Only integrate the **engineering code** after the operator has provided successful evidence on the exact SHA, and main remains a fast-forward ancestor. The experiment's calculated temperature values are **never** integrated into canonical world history.

## 6. Next science after the pilot

Independently seek a source-supported or explicitly authorially hypothesized T0 temperature initial profile, physical ocean-surface/basal forcing, material property validity over temperature/pressure, sensitivity to spatial scale, and 100-year solution convergence. Once qualified, a *different* regional model may be tested at 1000 years. Do not confuse this with completion of the full planetary G2/G3 physical solver; no automatic canonical output is permitted in either case.

EXPERIMENTAL_AUTHORITY=EXPERIMENTAL_NONCANONICAL_ONLY  
AUTOMATIC_PROMOTION=FORBIDDEN_EVEN_AFTER_SIMULATOR_COMPLETION  
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false  
HISTORYSTORE_MUTATIONS=0  
NATURAL_MINERAL_ORE_DEEP_ASSIGNMENTS=0  
D_024=ACTIVE  
physical_T1=null
