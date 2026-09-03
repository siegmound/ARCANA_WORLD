# v0.6D1-R4.0 — ARCANA Multi-Engine Scientific Revalidation & Orchestrator Consolidation

## Purpose
R4.0 restores the multi-engine architecture declared in R3.6A and makes ARCANA WorldSim the single orchestration and canonical-state authority.

R4.0 does **not** alter any SEALED biological, demographic, cultural, Deep/noetic, or historical result by itself. Existing R3.19–R3.39 outputs remain the `ARCANA_REDUCED_ORDER_BASELINE_A` until external evidence justifies a replay. Any revised canonical baseline must be produced by a later ARCANA-governed replay and reseal.

## Engine registry pinned for R4.0
- NEMO 2.4.2 — quantitative-genetics reference oracle.
- Geonomics 1.4.9 — spatial individual/genomic regional backend.
- MadingleyR 1.0.6 / Madingley C++ 2.02 — ecosystem/trophic-opportunity provider.
- CDMetaPOP 3.08 — secondary spatial demogenetic oracle, isolated Python 3.8 environment preferred.
- RangeShiftR / RangeShifter 3.0.1 — dispersal/range-dynamics specialist.
- SLiM 5.2 + tskit >=1.0.2 + msprime >=1.4.1 + pyslim >=1.1.1 — detailed genomic/admixture oracle added by R4.0.

## Governance invariants
1. ARCANA WorldSim is the sole canonical state owner.
2. External engines may never write canonical state directly.
3. External outputs are immutable evidence bundles keyed by executable/package identity, version, environment, source-state hashes, seed and requested outputs.
4. A disagreement between engines never auto-selects a winner. It opens an ARCANA calibration/replay decision.
5. Existing R3 seals are preserved as provenance even if a new baseline supersedes them.
6. Deep biological coupling remains OFF throughout H0 and all current R4 revalidation unless a later explicit historical Deep stage authorizes it.
7. No species, sapient lineage, domesticates, culture, language, religion, settlement, polity, or identity may be protected to preserve a previous narrative outcome.
8. NEMO 2.4.0/2.4.1 are forbidden for free-recombination quantitative-trait validation.
9. SLiM evidence is version-exact; 5.2 changes RNG relative to 5.1 and therefore engine version plus seed policy must be recorded.

## R4.0 phases
### Phase 1 — Parent/precedence binding
Validate R3.6A engine governance and the local R3.39 final seal. No parent file is rewritten.

### Phase 2 — Runtime capability inventory
Probe every engine through a governed adapter. `MISSING`, `VERSION_MISMATCH`, and `PROBE_FAILED` are valid inventory results but block the R4.0 full seal for required engines.

### Phase 3 — Revalidation experiment matrix
Materialize the cross-engine experiment plan before any result is inspected. Windows and metrics are frozen in the config.

### Phase 4 — Engine smoke readiness
A required engine is `READY` only if its exact runtime identity is confirmed. Runtime presence is not scientific agreement; it is only permission to start the revalidation jobs.

### Phase 5 — Replay decision policy
R4.0 maps future disagreements to the earliest affected ARCANA replay boundary. It does not pre-decide that R3.19–R3.39 must change.

## Revalidation domains
- H0 ecosystem/trophic structure: Madingley primary provider, ARCANA comparison.
- H0 dispersal/range dynamics: RangeShifter specialist, CDMetaPOP secondary cross-check.
- Quantitative genetics: NEMO reference oracle.
- Spatial genomics/demography: Geonomics primary regional backend, CDMetaPOP secondary.
- Detailed ancestry/admixture/selection: SLiM+tskit/msprime independent oracle.
- Recent producer managed/wild systems: Geonomics + SLiM, checked against R3.34–R3.36.

## Seal semantics
R4.0 may emit a `CANDIDATE` runtime inventory when engines are missing. The final `SEALED` verdict is fail-closed and requires all required runtime identities to be confirmed plus parent/governance/audit closure. Scientific agreement with R3 is not claimed by the R4.0 seal; R4.0 seals the governed revalidation infrastructure and frozen experiment matrix. Actual revalidation results are downstream R4 stages executed by this orchestrator.

### Governed local runtime bindings
The provisioner writes `set_r40_engine_env.local.ps1` with explicit `ARCANA_WSL_EXE`, `ARCANA_WSL_CONDA`, and engine-environment bindings. `run_v0_6D1_R4_0.ps1` auto-loads this local file before inventory so Python runtime discovery cannot silently diverge from the PowerShell provisioning path.

## Host Runtime Evidence Bridge
On Windows/WSL, runtime identity discovery is host-boundary work owned by PowerShell. `run_v0_6D1_R4_0.ps1` therefore generates a fresh `R4_0_HOST_RUNTIME_EVIDENCE.json` by executing the governed WSL/Conda/R probes directly through `wsl.exe`, then passes that evidence to the Python orchestrator. Python validates engine names and exact version pins before assigning `READY`; the bridge cannot promote scientific results or write canonical state.
