# R5.3 quick run

Extract this overlay into the authoritative post-R5.2 project root.

Run the complete stage:

```powershell
.\run_v0_6D1_R5_3.ps1
```

Optional safe pilot only:

```powershell
.\run_v0_6D1_R5_3.ps1 -PilotOnly
```

Resume a preserved partial corpus:

```powershell
.\run_v0_6D1_R5_3.ps1 -Resume
```

If CDMetaPOP runtime discovery is ambiguous, set the historically governed conda environment explicitly:

```powershell
$env:ARCANA_CDMETAPOP_CONDA_ENV = '<environment-name>'
.\run_v0_6D1_R5_3.ps1 -Resume
```

Expected complete candidate lines:

```text
PASS_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_EVIDENCE_CANDIDATE_RUN
PASS_R53_INTEGRATED_CDMETAPOP_DEMOGRAPHIC_EVIDENCE_CANDIDATE_RUN
```

There is deliberately no R5.3 final seal.
