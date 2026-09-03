# R4.9 candidate

Purpose: resolve the R4.8 uncertainty-limited matched-control diagnosis with a single fixed expansion from 4 to 20 paired CDMetaPOP J09 replicates.

Run preparation only:

```powershell
.\run_v0_6D1_R4_9.ps1 -PrepareOnly
```

Run the fixed additional 16 dynamic + 16 neutral replicates and seal:

```powershell
.\run_v0_6D1_R4_9.ps1
```

Expected runtime is longer than R4.8 because 32 new CDMetaPOP executions are required. R4.7 and R4.8 outputs are preserved.
