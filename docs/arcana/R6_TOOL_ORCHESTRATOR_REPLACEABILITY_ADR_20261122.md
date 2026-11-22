# ARCANA WorldSim — ADR R6: replaceable scientific-tool orchestrator

**Date:** 2026-11-22  
**Decision:** `ARCANA_SCIENTIFIC_ORCHESTRATOR__PROVENANCE_PRESERVING_TOOL_REPLACEMENT_ALLOWED`  
**Status:** `ACCEPTED_ENGINEERING_ARCHITECTURE_DIRECTION__NO_NEW_PHYSICAL_RATIFICATION`  
**Basis:** explicit author instruction that ARCANA's purpose is orchestrating existing scientific tools, adding missing adapters/physics only when needed, and that *even previously FAIR-certified implementations may be replaced by demonstrably better or simpler solutions*.

## 1. Nonnegotiable separation of WHAT from HOW

ARCANA is not committed to an individual crust law, solver implementation, programming language, existing module or completed benchmark. It is committed to an original, historically queryable planet model whose physical and canon authority are explicit.

1. **Planet/canon constraints and original scientific inputs:** authoritative only at their designated scope, with a documented process for revision.
2. **Algorithms, tools, numerical implementations, parameterizations and provider choices:** replaceable without special legacy privilege. FAIR-tested means *qualified for its tested contract*, never scientifically optimal or irrevocable.
3. **Evidence and prior computation runs:** append-only/versioned, recoverable by original tool versions, source hashes, settings, scientific assumptions and output manifests; superseded runs must not be retroactively relabeled.
4. **Physical/canonical authorization:** independent of software acceptance. A replacement can be numerically superior and still be **UNRATIFIED** for natural ARCANA geology.

A candidate replacement may replace, simplify, remove, combine or bypass legacy code if it demonstrably meets the relevant scientific and provenance requirements. **Do not demand numerically identical output to an obsolete model** when changed equations are the intended scientific improvement. Instead document why the new model is more valid, quantify differences and requalify the *new* physical contract. Conversely, do not call a model better only because it is newer, faster or passes old tests.

## 2. Provider boundary rather than hardcoded end-to-end chain

The common interchange contract is versioned and implementation-independent; likely providers are **interchangeable only within genuinely compatible scientific domains**:

| Boundary | Inputs with authority metadata | Output contract | Candidate tools (evaluation only) |
|---|---|---|---|
| Original T0 state | source parent/plate IDs, geometry, epoch, field SHA, units | source-anchored physical/unknown state | existing authentic T0 FEG/PRE providers |
| Bulk chemistry | explicit oxide composition, stoichiometry/Fe redox/H2O, uncertainty | *hypothetical* bulk chemistry and completeness | existing ARCANA authorial composition provider; verified Earth databases as analogue |
| Phase thermodynamics | qualified bulk composition, P/T and fluid chemical constraints, thermodynamic data | assemblage, phase fractions, density and uncertainties | MAGEMin/MAGEMin_C.jl; Perple_X independent comparison |
| Constitutive laws | **phase/material identity**, independent lab source, P/T, fugacity, stress convention, strain rate, geometry | mechanism-scoped flow/yield data, *validity domain*, unresolved cells | GeoParams.jl; ASPECT rheology reference or replacement; explicit current G2 trial |
| Interfaces and forces | sourced plate-side identity, fault geometry/DOFs, genuine cut/basal tractions, mantle frame, GPE datum | compatible residual/tangent, force/energy/rank/restart audit | current R6 G2/G3, SHELLS/ShellSet, potentially specialized mechanics tools |
| Geological history | accepted source state, valid process model, time step, conservation budgets | time-indexed spatial provenance/replay/checkpoints | ARCANA WorldSim; GPlately-like geometry adapter where truly applicable |
| HistoryStore and science queries | ratified/run-qualified state with temporal/geographic provenance | immutable history, query/reconstruction/zoom with uncertainty | existing WorldSim provenance store; later resource/Deep/fauna/flora providers |

**Caution:** GPlately's Earth-specific plate rotation files cannot be treated as ARCANA original T0 plate motion. A 3D volumetric solver cannot simply replace a spherical thin-shell discretization without a validated transfer of geometry, BCs, dimensional reduction, force balance and contact mechanics.

## 3. Interface record required of every scientific adapter

Minimum provenance for each provider call:

```text
scientific_task, provider_id, version/commit/container_digest
input_artifact_sha256[], source_epoch, source_parent_ids/plate_ids
model_equations, geometry_dimension_and_reference_frame
input_units, output_units, invariant_and_stress_convention
material_or_phase_identity_and_authority
T/P/rate/water/fluid applicability_domain
thermodynamic_database_name_version_and_license (if applicable)
hypothesis_id, authorial_selection_state, calibration_or_test_dataset_sha256
uncertainty_and_known_missing_fields (null/UNKNOWN, never zero-filled)
execution_parameters, deterministic_seeds, output_sha256
validation_results, failure_codes, no_canonical_promotion
```

Provider outputs must distinguish: **original-source numeric**, **conditional derived**, **Earth experimental analogue**, **explicit authorial hypothesis**, **authorially accepted regional physics**, and **canon/history publication**. A component must never silently promote one classification into another.

## 4. Replacement/adoption decision protocol

1. **Problem selection:** name the *physical* gap and target precision/resolution. Avoid writing an adapter before confirming the candidate tool fills that gap.
2. **Reproduction:** pin exact tool release/commit, environment, compiler, license, model/database versions and run a documented official sample/fixture. Prioritize provenance, not a mere successful installation.
3. **One-domain scientific benchmark:** compare a few clearly scoped original-geometry-compatible P/T/composition cases against theoretical checks, measured reference experiments, and where meaningful an independent implementation (e.g. MAGEMin vs Perple_X). Do **not** substitute a conditional lithostatic increment for true thermodynamic pressure.
4. **Quantified improvement:** assess applicable domain coverage, physical fidelity, uncertainty, correct units/conventions, conservation/invariants, stability, failure detection, resource use, maintenance, portability and interface complexity. Report numerical tradeoffs without arbitrary single weighted scores or ungrounded superiority claims.
5. **Adapter and dual-run:** implement a thin versioned adapter, run both old and new providers on the same *qualified* cases, quantify differences, and validate against evidence. No requirement to preserve old numeric output if the old method was deficient; record model-form change and retain rollback.
6. **Scoped promotion:** approve a replacement only for the specific operation/region/material/epoch it covers. Retire superseded implementation if justified; **retain** old code tags, tested SHA, immutable manifests and scientific receipts for historical reproduction. Engineering replacement is not automatic D-024/canon authorization.
7. **Source incompatibility:** any missing oxide/redox/H2O, fluid chemical state, phase database coverage, true fault-sidedness or mantle force remains `null` and is a scientific stop condition rather than silently receiving a terrestrial default.

The preferred outcome is often **less ARCANA-written solver code** and more robust scientific-tool integration. The adapter is warranted only for unit and geometry translation, provenance, missing physics, cross-tool checks or historical query compatibility.

## 5. First bounded evaluation — G2 original T0 8×8 (NOT a mechanical solve)

**Pilot A: thermodynamic phase provider.** Test MAGEMin via its documented Julia interface `MAGEMin_C.jl`, first on its own official examples and a published *Earth-only* complete chemical composition at an independently chosen physically supported P/T/fluid state; cross-check one *compatible* case in Perple_X. **Do not** fill omitted original ARCANA oxide components to 100%, assume Fe oxidation or H2O, or assume original source PRE code implies actual rock. Inspect database equation/chemical-system coverage before calling any code.

**Pilot B: constitutive-property provider.** Evaluate the same *explicitly hypothetical* and lab-provenanced rock conditions in GeoParams.jl; use ASPECT reference formulations as necessary to check invariant and flow law conventions. Build a mechanism-scoped validity map: **UNKNOWN** where measured T/P/stress/rate/fluid coverage fails. Retain brittle, semibrittle, dislocation, diffusion and gouge-slip distinctions. The existing G2 trial is a comparison baseline, not mandatory final solver.

**Pilot C: integration contract for the source 8×8.** Use SHA-verified original T0 81 parent nodes, 128 original basal triangles, 32 external cut edges, true two-plate interface, full prior 605 FAIR G2 source evidence. **Do not assign** any tested Earth-only rock as natural ARCANA geology. Report which material hypotheses are *conditionally evaluable* and which fail because of phase or source gaps. The 16×16 domain is sensitivity, not automatic mesh convergence.

**Progression only after validated conditions:** original rock/phase authorial choice, pore/fault effective pressure, mechanical LAB, mantle flow/tractions (all basal incl. eight core), correct GPE datum/no double count, genuine sided fault laws and solver force/work/energy/rank/restart. Only then propose a physically meaningful T0→T1.

## 6. Candidate reference sources (no integration or accuracy ranking yet)

- MAGEMin core: https://github.com/ComputationalThermodynamics/MAGEMin  
- MAGEMin_C.jl provider interface: https://github.com/ComputationalThermodynamics/MAGEMin_C.jl  
- Perple_X: https://github.com/jadconnolly/Perple_X ; scientific documentation https://www.perplex.ethz.ch/  
- GeoParams.jl: https://github.com/JuliaGeodynamics/GeoParams.jl  
- ASPECT constitutive documentation: https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html  
- GPlately (future Earth-specific historical geometry reference only): https://github.com/GPlates/gplately

The above are **verified available software/doc references**, not installed in FAIR, not yet run against ARCANA, and not certified equivalent to existing modules. Tool version/license compatibility and material-domain physical suitability are explicit future checks.

## 7. Governance and immediate continuation

Previous FAIR material trial `67/67 targeted`, `605/605 selected`, at exactly `1ce49decda12fe3d57eb66f097b482d27edcdc10` remains valid as numerical **software evidence**, not planet materials. See `docs/arcana/R6_G2_MATERIAL_TRIAL_FAIR_605_RECEIPT_20261122.md`.

```text
architectural_direction = ACCEPTED_ENGINEERING_ONLY
all_existing_modules_replaceable = true
old_SHA_evidence_and_history_immutable = true
hypothesis_experiment_allowed = true
natural_rock_phase_assignments = 0
natural_pore_fluid_pressures = 0
physical_T1 = null
mechanical_solve_authorized = false
D_024 = ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```

This ADR does **not** modify the canon, authorize T1, or invalidate previous receipts. It governs how ARCANA evaluates and replaces engineering implementations in pursuit of better scientific results.
