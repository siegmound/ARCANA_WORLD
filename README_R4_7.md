# R4.7

Run from the WorldSim root:

```powershell
.\run_v0_6D1_R4_7.ps1 -PrepareOnly
.\run_v0_6D1_R4_7.ps1
```

The full run executes the five frozen CDMetaPOP jobs in a new `outputs/v0_6D1_R4_7` evidence namespace, normalizes them, and performs targeted readjudication using the unchanged R4.4 policy. Expect several minutes because CDMetaPOP is executed four replicates per job.

If one repaired job needs a technical rerun:

```powershell
.\run_v0_6D1_R4_7.ps1 -JobId R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP
```

Then run the full command to collect all five bundles and seal.
