# ARCANA R6 — S2 numerical repeatability protocol V1

Date: 2026-11-23. Status: CANDIDATE_SOURCE_ONLY; no S2 process repetitions or FAIR regression checks performed on this branch.

Machine-readable authority: `experiments/r6_thermo_provider_pilot_v1/s2_repeatability_protocol_v1.json`.
Guard module: `experiments/r6_thermo_provider_pilot_v1/s2_repro_protocol.py`.
Fail-closed contract tests: `tests/test_r6_thermo_s2_protocol_v1.py`.

## Upstream S1 baseline (sealed, not rerun)

Historic tested R6 SHA: `f8d659042a739789e7a131dfc926cda1ceca30a4`. Official S1 two real-engine NEW02 archive MANIFEST SHA256 `538c1b61f801c9902f8aa9b1b189b07ba38357eec339eb2b0211713f83299227` (13 files rehashed on FAIR).
Independent MAGEMin CUSTOM_IG native oxide phase-weight reconstruction max abs discrepancy `1.9984014443252818e-15`, source Fe2O3 to FeO + O molar-mass basis match 11/11 max `5.551115123125783e-17`; source molar mass rounding implies bookkeeping equivalent mass 99.75010269897928 g before normalizing original 99.75 g input. Perple_X BL691 source reference native printed mole reconstruction compatible with decimal rounding for 10/10 oxide components. These are not cross-tool chemistry comparisons.

## Exact S2 case plan

- Five *fresh OS-level Julia processes*; each process solves both original MAGEMin Earth ig cases: KLB1 8 kbar / 800 Celsius and CUSTOM_IG 10 kbar / 1100 Celsius (the latter retains the exact original 99.75 weight input before internal normalization). Julia 1.10.4, MAGEMin_C.jl 2.4.5 / MAGEMin_jll 2.1.0+0, reported dataset tc_ds636, one thread.
- Five *fresh OS-level Perple_X meemum processes*, each running its original v7.3.3 BL691 input at 4000 bar / 1050 Kelvin; pinned source commit and release binary. One thread.
- New output directories must be write-once and source/manifest bound. All raw native and derived outputs, full stdout/stderr, shell commands, environment details, timestamps/durations, exit codes and hashes must be recorded. Preserve failure evidence and use a new attempt ID for any retry.
- Compare MAGEMin stable phase fractions by exact phase name, not array position. No aliases without reviewed crosswalk; phase disappearance/addition stops the stability PASS. Perple_X phase identities likewise.

## Predeclared numeric stability screens

| Observable | Absolute limit | Relative limit |
|---|---:|---:|
| MAGEMin G_system | 0.001 kJ/mol | 1e-6 |
| MAGEMin density | 0.01 kg/m3 | 1e-6 |
| MAGEMin phase mass fraction | 1e-4 fraction | 1e-3 |
| MAGEMin phase to native-bulk oxide-weight closure | 1e-10 | none |
| MAGEMin input to native-bulk source-basis closure, CUSTOM_IG | 1e-12 | none |
| MAGEMin provider bulk_res_norm upper bound | 1e-9 | none |
| MAGEMin phase-weight-sum error from unity | 1e-8 | none |
| Perple_X phase wt fraction | 0.02 percentage points | 1e-3 |
| Perple_X P/T from fixed input | 0.1 bar / 0.1 Kelvin | none |

Scalar repeatability screen: `abs(a-b) <= abs_limit + rel_limit*max(abs(a),abs(b))`; record BOTH absolute and relative observed differences, including worst case. The threshold is an engineering repeatability screen, not a physical uncertainty/experimental calibration. Record runtime descriptively, not an acceptance threshold. Do not adjust thresholds after seeing the 5-run results. If unexpected differences arise, record a failed attempt and adjudicate without overwriting evidence.

## Mandatory chemistry

MAGEMin new native per-run report must include oxides, each phase Comp_wt, phase mass shares, native normalized bulk_wt, source-to-native mass-basis accounting for CUSTOM_IG, native bulk_res_norm, solver status and iterations, P/T, Gibbs and density. The old S1 TOML does NOT contain these native chemical fields. Do not treat old S1 runner output as sufficient for S2 mass closure.
Perple_X per-run output must include its source-native `.prn`, stdout and exact source/bin provenance; read the native printed phase mol × oxide molar coefficients and compare to bulk mol with source-token precision intervals. That supports only print-resolution closure, not high-precision conservation.

## Software-only next step

Create a clean separate FAIR worktree from this *S2 branch*, activate existing Python `arcana-r6-linux` and run `python -m pytest -q -ra --tb=short tests/test_r6_thermo_provider_pilot.py tests/test_r6_thermo_s1_v2.py tests/test_r6_thermo_s2_protocol_v1.py`. Record exact commit SHA and test results; do not start S2 real runs yet. The 5-run engine campaign requires a separate real S2 runner and validator that implement ALL mandatory per-run chemistry fields and the code-SHA-bound new write-once evidence gate.

## Authority

`D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. No ARCANA materials assigned, no same-chemistry cross-provider ranking; current provider fixtures remain terrestrial. The MAGEMin CUSTOM_IG README illustrative numeric mismatch remains a distinct open issue.
