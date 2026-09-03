# ARCANA WorldSim v0.6D1-R4.54-R3

## NEMO explicit collector-Python + bridge diagnostic repair

After R4.54-R2:

- Madingley PASS
- RangeShifter PASS
- CDMetaPOP PASS
- SLiM PASS
- NEMO remained the only failure

The NEMO row was still a generic host fallback, meaning the NEMO wrapper did
not materialize even R2's failure-aware JSON.

### Baseline comparison

The already-validated R4.1 NEMO launcher executes:

```bash
conda run -n arcana-nemo242 bash run_nemo_r41.sh ...
```

and the R4.1 wrapper itself requires no Python command before starting NEMO.

R4.54 introduced new wrapper commands:

```bash
python -
python nemo_collect_r454.py ...
```

inside the NEMO conda execution context.

R4.0 runtime READY proves `nemo2.4.2` exists in `arcana-nemo242`; it does not
establish an unqualified `python` executable as part of that NEMO runtime
contract.

### Narrow repair

R4.54-R3 does not change NEMO itself.

The host bridge derives:

```bash
BASE_PY="${CONDA_EXE%/conda}/python"
```

from the already governed absolute Conda binding and verifies it is executable.

That explicit Python path is passed to `run_nemo_r454.sh`, which uses it for:

- isolated INI materialization;
- failure JSON materialization;
- the unchanged `nemo_collect_r454.py`.

The scientific NEMO collector from R2 is not modified.

### Stronger diagnostics

If the wrapper still fails before JSON materialization, the PowerShell fallback
now includes:

- exact probe job ID;
- exact frozen seed;
- seed-injection mode;
- runtime version;
- bridge exit code;
- timeout flag;
- bridge stdout tail;
- bridge stderr tail.

Thus another opaque NEMO failure is no longer possible.

### Governance

- R4.54-R2 blocked evidence preserved
- four prior PASS dry-run results preserved
- no historical scientific execution
- no metric ID changes
- no seed-semantic changes
- no numeric thresholds
- no canonical rewrite
- no gate weakening

Pre/post hashes:

```text
capture_v0_6D1_R4_54_dry_runs.ps1
9f8e09c2122b41cab224412b478adfd1e1e816122a2b2652a3c8668246feeaf8
→ cea5fbb81a92937e904d0d36acc6be8c826d169fa74c92e43903c6f7f0a81e9c

run_nemo_r454.sh
6b4cadda339c7c253a3bbde42fa45ad7a59173cb3284309c3691e2dbf7b3930c
→ 04ebb845d7c5f8c6678d5ac5028729fdd83e0146cdd433fa4de1c9c775843fa4
```

Run:

```powershell
.un_v0_6D1_R4_54_R3_nemo_explicit_python_repair_and_reseal.ps1
```

If NEMO still blocks, paste the resulting log: its NEMO result will now expose
the actual bridge stdout/stderr cause directly.
