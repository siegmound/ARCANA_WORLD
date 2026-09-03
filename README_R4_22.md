# R4.22

Runs the exact 11 P2 jobs authorized by sealed R4.21 (5 CDMetaPOP, 3 NEMO, 3 SLiM), with exact R4.3 seeds and exact R4.21 adapter hashes. Geonomics remains non-executing while its canonical spatial binding is audited fail-closed. No readjudication or canonical change occurs in this stage.

Run: `./run_v0_6D1_R4_22.ps1`

Useful recovery modes: `-PrepareOnly`, `-JobId <id>`, and `-CollectOnly`.


## R4.22-R1 — NEMO Conda/Python host-bridge repair
The initial authorized R4.22 execution preserved 8/11 PASS: CDMetaPOP 5/5 and SLiM 3/3 passed, while all three NEMO jobs returned bridge code 127 before adapter execution because `arcana-nemo242` exposed the native `nemo2.4.2` executable but did not expose a `python` command. R4.22-R1 changes only the PowerShell→WSL execution bridge: the unchanged R4.21-hash-authorized `benchmarks/r421/nemo_r421.py` is executed with the governed Miniforge base Python *inside* the `arcana-nemo242` conda context, preserving NEMO 2.4.2 resolution and all frozen job/seed semantics. No adapter source, scientific metric, target, seed, job scope, or canonical state is changed. Initial code-127 evidence is preserved under `outputs/v0_6D1_R4_22/repair_history/R422_INITIAL_NEMO_CONDA_PYTHON_BINDING_FAILURE/` before rerun.

Recovery sequence: rerun only J10, J13, J17 with `-JobId`, then run `-CollectOnly` to recompute exact 11-job completeness and the final fail-closed seal. Do not rerun the eight already-successful authorized jobs.
