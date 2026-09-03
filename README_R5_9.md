# R5.9 — R5.8 ↔ R3.28 High-Resolution Reconciliation

R5.9 discovers that the high-resolution 200 ka→0 replay already exists and is SEALED as R3.28. It therefore does not duplicate that simulation.

Run from the ARCANA WorldSim root:

```powershell
.\run_v0_6D1_R5_9.ps1
```

Workflow:
1. exact source authority;
2. regression;
3. validate R5.8 candidate outputs and inherited R5.7/R3.27 bindings;
4. validate exact sealed R3.28 outputs;
5. independently reconstruct the R3.27→R3.28 200 ka initialization boundary;
6. preserve R3.28 forcing/contact semantics;
7. emit a reconciled two-lineage 0 ka handoff;
8. leave R5.9 CANDIDATE and require explicit R3.29 reconciliation next.

No external engine is executed and R3.28 is not rerun.
