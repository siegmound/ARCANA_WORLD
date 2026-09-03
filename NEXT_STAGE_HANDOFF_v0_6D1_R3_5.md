# Handoff — v0.6D1-R3.5

## Immediate action
Run the paired dynamic ceiling sensitivity on the local machine:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_v0_6D1_R3_5_sensitivity_windows.ps1 -EndAgeMa 150 -Threads 12
```

This executes sequentially:
1. q=0.08, 210→150 Ma;
2. q=0.10, 210→150 Ma;
3. automatic comparison of endpoint and macro-event signatures.

Outputs are written under:

`local_runs\v0_6D1_R3_5\`

Key files:
- `210_to_150p0Ma_q0.08_summary.json`
- `210_to_150p0Ma_q0.08_va_telemetry.jsonl`
- `210_to_150p0Ma_q0.10_summary.json`
- `210_to_150p0Ma_q0.10_va_telemetry.jsonl`
- `210_to_150p0Ma_dynamic_ceiling_comparison.json`

## Audit after local execution
Check:
- number and duration of q=0.08 clipping episodes;
- event context of those episodes;
- whether q=0.10 has any clipping or ≥99% cap contact;
- peak unclipped q under both runs;
- recurrent root lineages / axes;
- population envelope at 150 Ma;
- fission/coalescence balance;
- species identities and speciation timing;
- gene-flow first/second moment closure.

## Decision tree
- **q=0.10 non-binding:** candidate production ceiling can be evaluated; optional q=0.12 confirmation only if needed.
- **q=0.10 binding:** do not raise again; open a homeostasis/admixture calibration stage.
- **chosen ceiling non-binding + endpoint audits pass:** promote 150 Ma and proceed to 150→90 Ma.
