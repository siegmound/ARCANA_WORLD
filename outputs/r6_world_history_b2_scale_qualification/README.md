# R6 B2 synthetic scale qualification

This package records a synthetic-only WORLD_HISTORY scale run at 64,442 nodes and 128,880 generated triangles. It contains metrics and hashes, not the temporary store or payload.

Run from the repository root:

```powershell
$work = Join-Path $env:TEMP 'ARCANA_B2_WORK'
python scripts/r6_world_history_b2_scale_qualification.py --work-root $work --output outputs/r6_world_history_b2_scale_qualification/B2_SCALE_METRICS.json
```

The runner removes only its own uniquely named temporary directory under `--work-root`. The `--output` file is the machine-readable full measurement record. No real T0, production FEG, runtime package, ShellSet, or OrbData mechanics are used. Timings are environment-specific.
