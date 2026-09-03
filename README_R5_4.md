# R5.4

Run from the post-R5.3 repository root:

```powershell
.\run_v0_6D1_R5_4.ps1
```

If a real NEMO corpus is interrupted after preparation, continue without discarding completed streams:

```powershell
.\run_v0_6D1_R5_4.ps1 -Resume
```

Defaults:
- Conda environment: `arcana-nemo242`
- parallel NEMO workers: 6
- governed Conda executable: `/home/jose/miniforge3/bin/conda` (override with `ARCANA_CONDA_EXE` only when explicitly needed)

Expected substantive flow:
1. source/parent authority and project-local regression;
2. fresh WSL/Conda identity plus exact `nemo=2.4.2` package and `nemo2.4.2` executable binding;
3. 144-stream plan preparation;
4. two-stream FLOW/control pilot;
5. full corpus with resume support;
6. paired genetic robustness analysis;
7. candidate completion, no seal.
