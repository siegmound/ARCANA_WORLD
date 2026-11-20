# ARCANA R6 — One-model-year original shell gap sign event refinement, temporal rate coherence

**Date:** 2026-11-20. **ENGINEERING_ONLY; FAIR test and source run PENDING.**

## Source authority and scope

Source immutable FAIR 25-model-year shell differential kinematics report manifest SHA `29ce93ffed7dae94be7cff16f92b3bb8a4f82020140a2adc0d6056270f38c1d5`, source tested at `8a7a116a1ba0f1a045146120ed3c68d23b70dfe6`, operator 107/107 PASS, driver PASS. Report bytes *not yet independently SHA checked* in the assistant context. New driver requires exact prior SHA matching the report's manifest and status plus every original provider source SHA.

The previous 41 source original 25y samples produced 4 **sampled** sign brackets in the 16×16 original region, none for 8×8. Original 16×16: 36 source R6BND-T0 boundary edges, 39 plate-pair node links and triple parent 34587.

| R6BND-T0 ID | Prior interval model years | Original sign transition |
| --- | --- | --- |
| `R6BND-T0-f679f4c97f1e7445d8d9` | 175–200 | NEGATIVE→POSITIVE |
| `R6BND-T0-4d168aac7492e7c418de` | 475–500 | POSITIVE→NEGATIVE |
| `R6BND-T0-1569360d5844c75db0d3` | 625–650 | NEGATIVE→POSITIVE |
| `R6BND-T0-16d7dc72630ecb414c04` | 875–900 | NEGATIVE→POSITIVE |

## New experiment

Driver: `experiments/plate58_deforming_explore_v1/g2_source_shell_event_1y_refinement.py`; tests: `tests/test_r6_g2_source_shell_event_1y_refinement.py`.

1. **Fail-closed provenance**: require exact previous manifest SHA, physical T1 null, ACTIVE D-024; original plate owners/FEG/PRE and source R6BND-T0 IDs match. Source scope must still show region 8×8 12 edges and zero 25y sign brackets; 16×16 36 edges/39 links/triple 34587 and exactly the 4 expected original brackets.
2. Re-run the **same original fixed-T0 KKT 1-year stepping** for 16×16 only, capturing every old 25-year sample and **each integer year** in the four previously discovered 25y brackets. Do not recompute new nonlinear contact forces, do not mutate source evidence.
3. At ALL 41 previous 25y original-scope samples, reconstruct every source-edge material-midpoint matched shell gap from genuine paired owner triangles, demand ID-complete source agreement with existing prior report <1e-7m. For the 4 source events, record every integer year's mathematical shell gap and source reconstructed `gdot`.
4. Preserve the sign deadband ±1µm and classify all **consecutive integer year** definite opposite-sign brackets, plus near-zero sample timestamps separately. A one-year bracket does **NOT** give the exact zero-crossing time and does not prove the absence of additional sub-annual crossings. Multiple switches within an earlier 25-year interval are allowed and reported.
5. Compare at interior integer years the centered **actual reconstructed 1-year history** `[g(t+1)-g(t−1)]/(2 model-years)` with the same analytic/FD positional-direction `gdot` of the reconstructed source velocity. Report source time-discretization discrepancy, including maxima **without a false hard PASS threshold**: the old source KKT uses discrete endpoint velocities and may have activation changes. This rate comparison is observational and cannot certify a new physical solver.
6. Reconfirm original triple material vector-loop identity at T0,100,500,1000 (source 34587 three original plate-local views), not a force/moment KKT proof.

The positive manifest status **would qualify only source replay and bracket extraction**, not exact continuous-time event detection or temporal rate parity. Missing or ambiguous source branch, SHA drift, source face change or 25y gap mismatch must fail closed. `D-024=ACTIVE`, `physical_T1=null`, physical solver 0, canon/HistoryStore unchanged.

## FAIR verification

Run on clean detached checkout pinned to the new commit SHA, with environment `arcana-r6-linux`, `PYTHONPATH=src:.`, `PYTHONDONTWRITEBYTECODE=1`, BLAS/OMP/MKL threads=1. Run new pytest and all previous seven regression suites; run new driver only if all pass into exclusive `G2_SOURCE_SHELL_EVENT_1Y_REFINEMENT_NEW_01`. Do not write into previous evidence directories. Capture `REPORT.json` SHA in `MANIFEST.json`, independently reverify raw file hash.

Example driver arguments:

```bash
BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
python -m experiments.plate58_deforming_explore_v1.g2_source_shell_event_1y_refinement \
 --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
 --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
 --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
 --prior-differential "$BASE/G2_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_NEW_01" \
 --output "$BASE/G2_SOURCE_SHELL_EVENT_1Y_REFINEMENT_NEW_01"
```

After PASS, assess how many 1-year definite sign brackets and near-zero timestamps exist, whether there are multiple switches inside an original 25y interval, and whether temporal rate discrepancy indicates coarse-time reconstruction artifacts that require independent convergence testing. **Never infer geological plate collision or permit updated 3D Signorini/KKT solely from negative shell gaps.**
