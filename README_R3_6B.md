# ARCANA WorldSim v0.6D1-R3.6B

**NEMO 2.4.2 Governed QTL-Ensemble Reference Benchmark**

This stage extends R3.6A without changing ARCANA biological authorities.

## Implemented
- reproducible diploid additive QTL ensemble generator;
- exact expected-moment matching for normalized trait mean and `V_A`;
- four canonical controlled metapopulation scenarios;
- explicit fragmentation/reconnection phase manifests;
- ARCANA exchange -> NEMO forward row-stochastic dispersal conversion;
- preparation of per-replicate experiments/evidence/QTL manifests;
- no guessed NEMO `.ini` semantics;
- Windows/WSL2 preflight helper;
- formal audit and regression tests.

## Prepare a reference suite
PowerShell from package root:

```powershell
$env:PYTHONPATH = "$PWD\src"
python scripts\prepare_nemo_qtl_ensemble_v0_6D1_R3_6B.py local_runs\R3_6B_NEMO --replicates 8 --individuals 2000 --loci-per-trait 64
```

Without a validated NEMO 2.4.2 template this intentionally stops at `PREPARED_REFERENCE_INPUTS`.

## NEMO on Windows
NEMO upstream recommends WSL2 on Windows. Check an existing installation with:

```powershell
.\check_nemo_242_wsl.ps1
```

Inside WSL2, upstream currently documents installation with conda from `conda-forge` + `ecoevo`.

## Next gate
R3.6C must run the three-way comparison:

`ARCANA 125 kyr <-> ARCANA 5x25 kyr <-> NEMO 2.4.2 ensemble`

No calibration parameter is changed in R3.6B.
