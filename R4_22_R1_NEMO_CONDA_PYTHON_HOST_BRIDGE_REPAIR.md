# R4.22-R1 — NEMO Conda/Python Host-Bridge Repair

## Finding
The initial R4.22 authorized execution completed CDMetaPOP 5/5 and SLiM 3/3, while NEMO J10/J13/J17 all failed before adapter execution with bridge return code 127 and stderr `python: command not found`. Fresh runtime identity evidence still proved NEMO 2.4.2 READY in `arcana-nemo242`.

## Root cause
The R4.22 host bridge invoked `conda run -n arcana-nemo242 python benchmarks/r421/nemo_r421.py ...`. The native NEMO environment is sufficient to provide the pinned `nemo2.4.2` executable but is not required to contain a Python interpreter. Therefore the bridge incorrectly coupled adapter-host Python availability to the NEMO runtime environment.

## Repair
Only `capture_v0_6D1_R4_22_authorized_jobs.ps1` is changed. For NEMO jobs it derives the governed Miniforge base Python from the already-audited conda binding (`.../bin/conda` → `.../bin/python`) and runs that absolute interpreter inside the `arcana-nemo242` conda context. The R4.21-authorized `benchmarks/r421/nemo_r421.py` file is unchanged, so its frozen SHA256 authorization remains valid and its subprocess continues to resolve `nemo2.4.2` from the NEMO environment.

## Governance
- exact R4.21 authorized NEMO jobs only: J10, J13, J17;
- exact original R4.3 replicate indices and seeds;
- no rerun of the eight already-passing R4.22 jobs;
- no target-dependent configuration;
- no result-selected scientific tuning;
- no adapter semantic change;
- no canonical write/replay/parameter change;
- Deep biological coupling remains OFF;
- initial NEMO code-127 evidence is preserved before rerun.

## Recovery
Run each failed authorized NEMO job with `run_v0_6D1_R4_22.ps1 -JobId <id>`, then `run_v0_6D1_R4_22.ps1 -CollectOnly`. The final collect must recover 11/11 PASS and exact seed-ledger equality before R4.22 can seal.
