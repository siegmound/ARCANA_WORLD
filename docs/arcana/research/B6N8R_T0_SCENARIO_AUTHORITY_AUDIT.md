# B6N8-R — T0 executable scenario roster authority audit

## Decision

**BLOCKED_B6N8R_SUPPORT_APPLICABILITY_INCOMPLETE.** Existing qualified authority defines a finite reduced-model sensitivity envelope, but it does not bind exact scenario-to-support membership. No executable roster, concrete scenario count, or numeric candidate cardinality is created here.

## Baseline and authority lineage

- Branch: `r6/b6n8r-t0-executable-scenario-roster`; HEAD and B6N8-Q attestation commit: `84d5fa48e6c68a690c0cc70807341bb60f8669f8`.
- B6N8-Q source: `7167f532b49a1430dbb99e8105365ff9dcfb67b0`; verdict: `PASS_B6N8Q_REAL_SUPPORT_EXECUTION_ADAPTER_QUALIFIED_REAL_RUN_STILL_BLOCKED_BY_SCENARIO_ROSTER`.
- B6N8-P historical decision remains `BLOCKED_B6N8P_EXECUTION_CONFIGURATION_INCOMPLETE`. Q closed the adapter/infrastructure blocker; the roster blocker remains open.
- Q reuses qualified B6N8-O source `73d98ee14f933622f0d3f18f66985b06f364abcd`. Neither provider nor Q adapter was changed.
- The exact J–Q attestation/source commit and artifact census is recorded in the [scenario dimension registry](B6N8R_SCENARIO_DIMENSION_REGISTRY.json). Direct model inputs include B6N8-I bindings, the material-reference and heat-flow configurations, transient-coupling authority, and B-v2 T0 manifest.

## Scenario dimensions

B6N8-J selects `R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING` for reduced T0 profile construction only. B6N8-L names `TSURF_LOW=250 K`, `TSURF_REFERENCE=280 K`, and `TSURF_HIGH=300 K`, and permits existing role/property/source reference-range endpoints as separately identified one-factor model sensitivity cases. Those values are model configurations, not climate or geologic history.

The registry records the role-scoped k/rho/Cp/alpha and A_C/A_M references/ranges, HWR-2 parameter ranges, fixed class-specific continental q and model-base geometry, derived kappa, and deterministic positive-age mapping. `kappa=k/(rho*Cp)` is not an independent axis; role identities are categorical and do not infer composition. HWR Fourier `N=256` is a numerical convergence setting, distinct from executable scenario count `N`.

B6N8-P says retain every applicable separately authorized scenario, with no convenience selection or unauthorized Cartesian product. Thus all applicable separately authorized one-factor members are retained; this does not require every cross-axis combination or identify one scenario as physical truth. The [compatibility matrix](B6N8R_SCENARIO_COMPATIBILITY_MATRIX.json) marks unsupported combinations UNKNOWN and automatic Cartesian construction PROHIBITED.

## Support applicability and cardinality

The support census is 64,800 native cells; 63,620 metadata-admitted (14,258 continental and 49,362 positive-age oceanic); 1,072 unresolved ocean cells and 108 age-zero ridge cells excluded. B6N8-L calls continental columns the minimum model support and eligible positive-age ocean columns optional/conditional. B6N8-Q's 63,620 preflight is metadata-only and does not establish per-scenario numerical feasibility or bind each roster entry's `support_ids`.

Therefore the P formula `63620 × N` is not verified as a global per-member product. It remains historical symbolic contract text, and P is not modified. A future explicit support-specific roster must count membership from its exact `support_ids`; if it differs from P's full-support product, a governed P contract correction is required before execution.

## Identity and unresolved choice

The deterministic identity format is specified without creating IDs: a scenario configuration digest binds initializer/version, T0, exact support IDs, source/boundary/material members and authority identities; a roster digest binds sorted explicit entries, support assignments, compatibility decisions and contract version.

The finite authorial decision is to select the T0 run support scope (continental minimum only or also eligible positive-age ocean), then bind each retained one-factor member to exact support IDs and configuration authorities. No external research is required for this model-policy choice. TSurf applicability remains conditional where the datum and physical boundary match. No scenario is called a reconstructed physical history.

Q's typed `ScenarioEntry`/`ScenarioRoster` can represent semantic IDs, configuration hashes, boundary/source identity, explicit support IDs, authority and provenance. Compatibility is validated at the interface level only; there is no real roster instance to validate, and real numerical execution remains unauthorized.

## Gates and readiness

R1 PASS; R2 PASS scoped to the committed J–Q census; R3 PASS with conditional dimensions; R4 BLOCKED; R5 matrix complete with UNKNOWN retained; R6 automatic Cartesian products not authorized; R7–R11 BLOCKED pending support/member binding; R12 PASS at interface level only; R13 PASS, WORLD_HISTORY not accessed; R14 decision recorded as `NO_SUPPORT_APPLICABILITY_INCOMPLETE`.

After any R attestation, real T0 execution remains not ready. `REAL_SCENARIO_ROSTER_BOUND=false`, `REAL_SCENARIO_COUNT_RESOLVED=false`, `N=null`, `REAL_RUN_AUTHORIZED=false`. Conduction remains `PARTIAL_IDENTIFIABILITY_PROFILE_REQUIRED_FOR_FINAL_DECISION`. No Buck section, Ux, Xe, XL, strain rate, or mechanics is selected.

## Preserved non-actions

No provider, adapter, thermal equation, parameter, initializer, or grid was changed or selected. The initializer/evaluator was not called; no candidate, T0/T1 profile or canonical state was generated. WORLD_HISTORY was not accessed or changed. No dt2, T2, Buck inputs, or forward evolution was selected or executed.
