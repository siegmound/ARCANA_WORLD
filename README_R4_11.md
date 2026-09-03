# v0.6D1-R4.11

Purpose: repair the CDMetaPOP population metric after R4.10 confirmed that `hindex` input files collided with the historical broad `ind` filename selector.

Run:

```powershell
.\run_v0_6D1_R4_11.ps1
```

R4.11 does **not** execute CDMetaPOP. It reuses retained `summary_popAllTime.csv` files from R4.7, R4.8 and R4.9, produces corrected evidence in `outputs/v0_6D1_R4_11`, recomputes the five affected CDMetaPOP rows under the frozen R4.4 policy, recomputes the 20-pair matched-control effect, and seals only if all retained evidence passes integrity checks.

### R4.11-R1 retained-runtime gate repair

If the initial R4.11 run blocks only on `all_reextracted_initials_match_configured_n0`, apply the R4.11-R1 repair. CDMetaPOP 3.08 zeroes configured N0 on non-natal patches before initialization; R4.11-R1 mirrors that pinned behavior and compares `summary_popAllTime.N_Initial` against the engine-effective N0 while preserving the raw PatchVars sum for provenance. No CDMetaPOP rerun is performed.
