# Handoff — v0.6D1-R3.4

Run the full Natural-Control replay from the R1 common state:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_v0_6D1_R3_4_windows.ps1 -EndAgeMa 150 -Threads 12
```

Audit the resulting endpoint for:
1. `q_max <= 0.08` and fraction `q >= 0.0792` approximately zero;
2. population envelope against A1 150 Ma;
3. species richness, speciation identities/timing;
4. fission/coalescence balance and micro-deme tail;
5. gene-flow first/second moment closure.

If the rerun passes, promote 150 Ma as the first rebased H0 production checkpoint and proceed to the 150→90 Ma segment with checkpoint/resume.
