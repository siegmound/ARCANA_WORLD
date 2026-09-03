# R4.15

Run from the WorldSim root:

```powershell
.\run_v0_6D1_R4_15.ps1
```

Expected scope: 4 retained-runtime P0 cells + 59 ARCANA-target P1 cells. No engine is launched. R4.15 intentionally does not readjudicate the matrix and does not promote candidate metrics or targets; it prepares the fail-closed R4.16 promotion gate.

## R4.15-R1

If the initial R4.15 stopped at `all_four_p0_have_retained_recovery_evidence`, apply the R4.15-R1 overlay and run the same command again. The runner preserves the blocked evidence, scopes each P0 recovery to the engine frozen in the R4.14 closure action, and explicitly reclassifies any genuinely unrecoverable candidate to the P2 backlog rather than fabricating evidence or rerunning an engine.

The repaired PowerShell wrapper also exits non-zero on blocked Python stages; `PASS_R415_INTEGRATED_AND_FINAL_SEAL_RUN` is printed only after the final seal succeeds.
