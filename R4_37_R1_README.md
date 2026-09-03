# ARCANA WorldSim v0.6D1-R4.37-R1
## Live Failure-Detail Diagnostic

R4.37 correctly BLOCKED with two unresolved native-compatibility questions:

1. J21 canonical payloads are hash-valid, but at least one canonical raster is
   outside Geonomics Layer's native `[0,1]` range. R4.37 correctly refused to
   normalize or clip it.
2. J14 and J18 each reached their four-replicate dry-run stage but 0/4 passed.
   The console summary does not contain the underlying native error.

R4.37-R1 is diagnostic-only and DOES NOT rerun Geonomics.

It reads the already-written R4.37 audit files and emits:

`outputs/v0_6D1_R4_37_R1/R4_37_R1_LIVE_FAILURE_DETAIL_DIAGNOSTIC.json`

The report contains:
- every J21 payload failing `[0,1]`, with min/max/hash status;
- every J14/J18 failed replicate with the exact stored error;
- failed branch summaries if the failure occurred after injection began.

No R4.37 output is modified. No scaling, model construction, scientific
execution, target execution, readjudication, or canonical-state change occurs.

Run:

```powershell
.\run_v0_6D1_R4_37_R1_live_failure_detail_diagnostic.ps1
```
