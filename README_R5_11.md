# R5.11 — R3.30 Census / Weighted Group ABM Reconciliation

Overlay this patch on the post-R5.10 project and run:

```powershell
.\run_v0_6D1_R5_11.ps1
```

R5.11 performs no external-engine run and does not rerun R3.30. It independently revalidates the sealed R3.30 census-equivalent calibration and weighted-group conservation, then emits a reconciled 0 ka handoff. R3.31 remains non-authorized until a separate reconciliation.
