# R5.2 — Targeted Expansion Corridor Validation

R5.2 is the first post-R4 targeted new external-engine execution. It uses **RangeShiftR 3.0.1** because R5.1 has now supplied concrete model-derived cradle-opportunity origin families.

**R5.2-R1 repair:** the first live 80-stream attempt is preserved as blocked evidence because the adapter used RangeShiftR free initialisation (`InitType=0`) even though an ARCANA `SpDistFile` was supplied. R5.2-R1 uses `InitType=1, SpType=0` so engine-year-0 is bound to the frozen ARCANA source mask. No scientific sensitivity or target changed. Do not reuse the blocked pre-R1 streams. The patched `-Resume` logic refuses them automatically.

Run the repaired source-binding probe first, without launching the expensive corpus:

```powershell
.\run_v0_6D1_R5_2.ps1 -ProbeOnly
```

After `PASS_R52_R1_SOURCE_BINDING_PREFLIGHT_ONLY`, run the full scientific corpus:

```powershell
.\run_v0_6D1_R5_2.ps1
```

If an execution is interrupted after some groups completed, resume without discarding complete raw evidence:

```powershell
.\run_v0_6D1_R5_2.ps1 -Resume
```

The PowerShell runner owns the Windows→WSL boundary, performs a fresh exact RangeShiftR version check, prepares the ARCANA-derived dynamic landscapes, then executes a one-engine-year **R5.2-R1 source-binding preflight**. The full 80-stream corpus starts only if engine year 0 reconstructs the frozen ARCANA source mask exactly and uniquely. It then executes all applicable frozen groups, preserves failed evidence, and analyzes the corpus in Python.

Key outputs under `outputs/v0_6D1_R5_2/`:

- `R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json`
- `R5_2_RANGE_EXECUTION_PLAN.json`
- `R5_2_RANGE_EXECUTION_BRIDGE.json`
- `R5_2_RAW_EVIDENCE_MANIFEST.json`
- `R5_2_STREAM_EVIDENCE.json`
- `R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json`
- `R5_2_INTEGRATED_AUDIT.json`
- `R5_2_OUTPUT_MANIFEST.json`
- `rangeshifter_work/<group>/Evidence/STREAM_SUMMARY.tsv`
- `rangeshifter_work/<group>/Evidence/occupancy_*.tsv.gz`

A successful run should end with:

```text
PASS_R52_TARGETED_RANGESHIFTER_EXPANSION_CORRIDOR_EVIDENCE_CANDIDATE_RUN
PASS_R52_INTEGRATED_TARGETED_RANGESHIFTER_CORRIDOR_EVIDENCE_CANDIDATE_RUN
```

Do not call R5.2 SEALED from those lines alone. First inspect the fixed sensitivity evidence. Numeric RangeShiftR overlap is descriptive support and is not allowed to overwrite or vote on ARCANA canon.

### Final-seal closure
After a complete R5.2-R1 corpus, rerun `run_v0_6D1_R5_2.ps1 -Resume`. Complete R1 streams are reused; the runner recomputes the analysis, builds a descriptive non-voting evidence readout, verifies raw evidence hashes, and emits `R5_2_FINAL_SEAL.json`. Expected final line: `PASS_R52_INTEGRATED_AND_FINAL_SEAL_RUN`.
