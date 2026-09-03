# v0.6D1-R4.3

First real execution stage for the 23 historical multi-engine revalidation jobs frozen by R4.2.

Workflow:

1. `run_v0_6D1_R4_3.ps1 -PrepareOnly`
2. inspect `outputs/v0_6D1_R4_3/R4_3_PREEXECUTION_AUDIT.json`
3. recommended plumbing smoke: `run_v0_6D1_R4_3.ps1 -Smoke` (one pre-declared frozen job per governed engine; no completeness seal and no scientific conclusion)
4. `run_v0_6D1_R4_3.ps1` to execute all exact 23 frozen jobs
5. R4.3 collects/normalizes evidence and runs the fail-closed completeness/final-seal audit.

For targeted adapter repair only, one exact frozen job can be executed with `-JobId <R42_JOB_ID>`; this never seals R4.3.

R4.3 uses **normalized boundary-response revalidation**: engine-native representative runtimes are explicit response scales, not literal calendar-equivalent replays of multi-Myr windows. ARCANA end states are comparison targets only and never engine inputs.

R4.3 does not adjudicate scientific discordance and does not modify canonical state.


## R4.3-R1 NEMO host-control repair

The first full historical execution exposed a host-control defect affecting only the three NEMO jobs: the R4.3 bridge attempted to run the Python adapter *inside* the `arcana-nemo242` engine environment. That environment is governed as a NEMO runtime and is not required to provide Python; the bridge therefore returned 127 before normal replicate evidence could be written. R4.1 had correctly invoked NEMO through a shell inside its engine environment.

R4.3-R1 keeps the exact R4.2 frozen jobs, seeds, semantic mappings, engine version and scientific configuration unchanged. A Miniforge/base control Python now drives `nemo_r43.py`, while each actual NEMO execution is still performed via the pinned engine environment using `conda run -n arcana-nemo242 nemo2.4.2 ...`.

Existing successful evidence for the other 20 jobs is preserved. Use:

`run_v0_6D1_R4_3.ps1 -RepairNemo`

This re-executes only J10/J13/J17, archives their pre-repair return-127 evidence under `outputs/v0_6D1_R4_3/repair_history/R43_R1_NEMO_RETURN127_PRE_REPAIR/`, then recollects all 23 bundles and runs the normal final seal if completeness passes.
