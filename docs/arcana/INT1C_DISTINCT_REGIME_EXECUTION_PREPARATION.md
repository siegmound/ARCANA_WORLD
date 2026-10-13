# INT-1C — Distinct-Regime Execution Preparation

Date: 2026-10-13

Source branch/HEAD at preparation: `r6/si1-bandwidth-f2av` / `8585d4fdd29ba5f1019421bf8310ef06883fb78b`
Decision: `INT1C_DISTINCT_REGIME_CODE_READY__EXECUTION_PENDING_AUTHORIZATION`

## Scope and authority

This is an offline implementation and readiness check for the INT-1B distinct pair-5:11 engineering case. No provider-backed evolution, Fair, MPI, ShellSet, Solver, or WORLD_HISTORY operation was performed. The experiment remains unauthorized. The previously verified R4 bundle is the source for the candidate edge evidence: manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; `EDGE_AUDIT_MATRIX.json` SHA256 `d89bd4d9cca8928f8e6b913ad6bf1955c429ac2e2e1bb4dc6b6263f7165a59c7`; source-composite identity at the R4 source commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8` was `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`. These identities describe that historical evidence, not the modified candidate source.

The current `ARCANA_EXTERNAL_ROOT` is unset and the external provider payloads needed by `audit_pair_5_11` are unavailable in this Windows environment. Therefore the complete provider audit and a HEAD-specific source-composite identity were not recalculated. The previously manifested edge record was read locally, and both T0 profiles were independently re-materialized through the in-repository B6N8-N binding implementation and its hash checks. A fresh provider-backed audit remains a mandatory pre-execution check.

## Selected edge and profiles

The exact requested edge is `R6BND-T0-27e4d497530e681071fb`, ordered pair `[5, 11]`, parent grid edge row 94 / column 25 / EAST. The preserved R4 edge audit marks it `ELIGIBLE`, `EXTENSION`, nonjunction, and reports Euler/census difference `1.3877787807814457e-17 m/year` and signed opening `0.10694074272424924 m/year`. Its ordered supports are plate 5 `R6G1D-R094-C026` and plate 11 `R6G1D-R094-C025`.

Both profiles were re-materialized at current HEAD using the admitted-support authority and native field package. Each has 73 nodes spanning 0–135,000 m; 35,000 m crust; 135,000 m reference lithosphere; surface heat flow 0.06 W/m²; material roles `CONTINENTAL_CRUST_REFERENCE` and `LITHOSPHERIC_MANTLE_REFERENCE`; matching property tuple identities `5e4c9bfc4bea016068b5c19f9a078f2a1c638d2455f56780a64618a8cf1488df` and `2150afd0405fc6929a643f14d401818adf3c76c0e722d2d376903deb9fa9a225`. Both materialized profiles span 280–1694.4975960996167 K. The binding implementation checked the attestation and authority hashes, field-package hash and admitted-support preflight. This verifies materialization under the local qualified binding contract; it does not replace the unavailable full forcing/provider audit.

The candidate remains an `ELIGIBLE_QUIESCENT` engineering section. It is not event, activation, physical-section, or causal attribution authority. Relative to R4, edge support, thermal/geometric inputs, and edge-specific forcing vary together.

## Implementation

The provider audit now accepts an optional exact boundary ID. With no ID, the prior sorted lower-median selection remains the default. An explicit ID must be unique in the verified edge matrix and pass pair, plate order, two distinct admitted continental supports, positive finite extension, material/thermal eligibility and junction checks. The existing profile materializer is used for both supports; the result is checked against support ID, geometry, heat flow, class, grid cardinality and depth endpoints. Selection mode and requested ID flow into the integration configuration and candidate manifest.

The runner adds optional `--boundary-id`, `--additional-resolution-factor`, and `--diagnostic-resolution-factor`. Resolution overrides require an explicit boundary ID. If an additional factor is supplied, a diagnostic factor must also be supplied and must equal that added factor; this prevents silently sampling the old 0.0005 rung. With no overrides, the old three factors and middle-factor diagnostic behavior remain unchanged. The prepared command for a future, separately authorized run is:

```text
python scripts/r6_functional_development_t_f2b.py --repository-root . --expected-branch r6/si1-bandwidth-f2av --boundary-id R6BND-T0-27e4d497530e681071fb --additional-resolution-factor 0.000125 --diagnostic-resolution-factor 0.000125 --output-relative outputs/r6_functional_development/INT1C_TF2B_5_11_R094C025_C026_20261013_01
```

The original factor ladder remains `0.001`, `0.0005`, `0.00025`; `0.000125` is appended. Every substep is recorded only for the explicitly selected `0.000125` run. The original `0.0005` rung remains the candidate checkpoint/trajectory and replay/restart reference, and the `0.00025` rung remains available for a same-resolution comparison with R4. Output metadata labels these roles separately. Existing kernel, equations, boundary conditions, duration, and physics are unchanged.

## Timestep and cost estimate

Read-only materialized-profile calculation gives the explicit thermal stability limit `0.8 × dt_diff = 952,777,777,777.7762 s` on both supports. At initial width `110,852.14113381179 m` and edge velocity `0.10694074272424924 m/year` (`3.3887476463434874e-9 m/s`), the initial kinematic bounds are:

| Factor | Initial kinematic step | Approximate substeps over 1,000 years |
|---:|---:|---:|
| 0.001 | 32,711,831,243.45 s | 1 |
| 0.0005 | 16,355,915,621.72 s | 2 |
| 0.00025 | 8,177,957,810.86 s | 4 |
| 0.000125 | 4,088,978,905.43 s | 8 |

The substep projection uses the candidate's initial width/velocity and multiplicative width update; it is a deterministic estimate from the configured kinematic rule, not a run result. The new rung is expected to be kinematic-limited and to add temporal observations. At the finest rung the projection is 9 records/support (initial plus eight completed substeps), 18 records total. Exact substeps, timestamps and serialized bytes remain unobserved. At 0.000125, the initial kinematic bound is about 233 times smaller than the thermal bound.

R4 measured 20.633493 s, a sampled process-tree working-set peak of 164,384,768 bytes, and 691,140 cumulative output bytes under its supervisor. R4 used observed substeps 2/3/5 at its three factors. The new candidate's projected 1/2/4/8 is 15 versus 10 summed substeps per support across the ladder, about 1.5× that portion of integration work; finer sample records add output. This is only a planning comparison, not a runtime/RSS/output guarantee. The 900 s, 2 GiB monitored working-set and 512 MiB output limits remain operational thresholds, not hard OS quotas; `RESOURCE_2GB_SCOPE_UNRESOLVED` remains open. The candidate output and proposed supervisor evidence directories were both absent at this check:

- `outputs/r6_functional_development/INT1C_TF2B_5_11_R094C025_C026_20261013_01`
- `outputs/r6_functional_development/INT1C_SUPERVISION_20261013_01`

## Offline verification and remaining gates

The focused offline suite passed **87 tests**; two provider-backed tests were deselected because their governed external payloads are unavailable here. The passing suite covered the explicit/default selector, invalid IDs and support mismatches, synthetic integration, sampling at the configured fine rung, endpoint validation, deterministic output/manifest behavior, existing replay/restart contracts, and INT-1A retention checks. Python 3.12.14 and NumPy 2.3.5 were used through the bundled runtime; pytest 8.4.2 came from an already installed local environment. No dependency was installed. No numerical evolution was run.

Before any separately authorized execution: restore the configured external provider root; run the provider-backed audit on the final committed source; verify all source-composite and provider payload hashes, both exact profiles, edge identity and environment; validate the established process supervisor and fresh output/evidence destinations. B0 HistoryStore remains `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`; it is not a prerequisite for preparing this engineering run, and no executable B0 replay claim is made here.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. Next action is independent review and local publication of this code-ready preparation, then a separate bounded execution authorization and immediate provider/supervisor preflight. No evolution is authorized by this report.
