# ARCANA R6 — S2 native repeatability runner candidate V1

Date 2026-11-23. **Source published, FAIR execution of the new runner and tests PENDING.** No new S2 official evidence yet.

Existing candidate source:

- `experiments/r6_thermo_provider_pilot_v1/run_magemin_s2_native.jl`: two real upstream Earth `ig/tc_ds636` cases in one fresh Julia OS process; captures each native oxide `Comp_wt`, `bulk_wt`, `bulk_res_norm`, `G_system`, density, iterations, P/T, phase names, source Fe2O3→2FeO+O normalized mass-basis closure. Every output is Earth-only, no Arcana native geology.
- `experiments/r6_thermo_provider_pilot_v1/validate_s2_native.py`: independent Python native matrix reconstruction; original source mass-table map, source phase-set exactness, 5-run pairwise absolute+relative stability bounds, original Perple_X MEEMUM native printed-molar oxide table with Decimal token-precision interval overlap for all 10 components and per-run report consistency.
- `experiments/r6_thermo_provider_pilot_v1/run_s2_fair.py`: **explicit** `--phase preflight` (software test only) and `--phase run` (5 fresh Julia + 5 fresh MEEMUM OS processes); code/head/hash locked to preflight, runtime version and binary pins, write-once destinations and per-run raw native files, stdout/exit/PIDs and SHA256 manifest; failures preserved. Real run must **not** be executed before FAIR reviewed code/tests/smoke and scientific authorization in chat.
- `tests/test_r6_thermo_s2_native_v1.py`: synthetic/negative source contract tests; test signals are not real engine PASS.
- Earlier JSON source policy `s2_repeatability_protocol_v1.json` frozen before the five-run campaign: tolerances and authority unchanged. Read full numeric tolerances in `docs/arcana/R6_THERMO_S2_REPEATABILITY_PROTOCOL_V1_20261123.md`.

## Exact evidence destinations (do not create manually; do not execute yet)

- S2 software preflight write-once `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_S2_SOFTWARE_PREFLIGHT_NEW01`
- S2 real experiment write-once `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_S2_REPEATABILITY_NEW01`

Every failure is preserved, not overwritten. A re-attempt requires a newly versioned identifier. S1 `R6_THERMO_EXTERNAL_OFFICIAL_NEW02` and historical 17-file diagnostics are read-only provenance and must remain untouched.

## First next step on FAIR: **software tests only**

Do not update the earlier tested S2 protocol worktree `ARCANA_WORLD_R6_THERMO_S2_PROTOCOL_VERIFY` at `71e49c3bb7648211c9dbdfc6bc247307a1066ce8`. Make another separate linked detached worktree to verify the latest runner candidate source, using existing Python `arcana-r6-linux`:

```bash
OLD=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_THERMO_S2_PROTOCOL_VERIFY
NEW=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_THERMO_S2_RUNNER_VERIFY
BRANCH=r6/thermo-s2-repeatability-protocol-20261123
cd "$OLD"
git fetch origin "$BRANCH:refs/remotes/origin/$BRANCH"
test ! -e "$NEW" && git worktree add --detach "$NEW" "refs/remotes/origin/$BRANCH"
cd "$NEW"
git rev-parse HEAD
git status --short
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q -ra --tb=short \
  tests/test_r6_thermo_provider_pilot.py \
  tests/test_r6_thermo_s1_v2.py \
  tests/test_r6_thermo_s2_protocol_v1.py \
  tests/test_r6_thermo_s2_native_v1.py
```

Stop after result; provide exact tested HEAD, count, errors, exit. **Do not call `run_s2_fair.py --phase preflight` or `--phase run` yet.** Following a software PASS, review source science, smoke a single fresh native Julia diagnostic (outside evidence) and original PRN read-only validator; only then create versioned S2 write-once preflight and real engine campaign.

## Scientific limitations

- MAGEMin Fe2O3→FeO/O source convention reconciled numerically, but source molar mass rounding and any independent chemical/experimental truth remain separate.
- Perple_X printed oxide reconstruction certifies consistency with source rounding only; no high-precision Perple_X chemical closure.
- Native MAGEMin and Perple_X have **different oxide bases/datasets**, no common-composition cross-provider equivalence.
- MAGEMin illustrative CUSTOM_IG README numeric discrepancy remains **PENDING** independently.
- `D-024=ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
