# EXPLORE-DT — compensated Euler and compact quartic cache

This is a new namespace. Frozen V1, R1 and hr2_p1_explore are read-only dependencies.
Old sealed EXPLORE results are unchanged. No formal moment-certificate prerequisite
is reintroduced; this is practical manufactured EXPLORE, not scientific VALIDATE.

- `study.py`: fixed archived geometry/initial volume timestep sweep, original/full
  FCT versus smooth plain/Kahan/extended accumulation. All longitude Fourier modes
  give an independent latitude-block semidiscrete reference. Extended Taylor and
  SciPy expm crosscheck; no interval certificate or exact real-arithmetic claim.
- `compensated.py`: full low/high/FCT kernel with Kahan volume accumulation. Native
  state is **volume_hi - correction**. Both arrays MUST be checkpointed. The physical
  height is computed using the available extended accumulator before binary64 flux
  evaluation; matrices/parameters/initial volumes stay unchanged. No stock clipping,
  global normalization or timestep/CFL relaxation. Roundoff budget guards remain.
- `compact.py`: preallocated CSR and complete `CompactOperator`, using identical
  original generic quartic packet calculations. CSR data/indices/pointers match the
  archived256x128 matrix bit for bit; Python object lists are avoided.
- `checks.py`: short corrected sweeps/regressions, full-FCT positivity/random/spike,
  constants, negatives, source-bound checkpoint and separate-child continuation.
- `memory.py`, `service.py`: comparable template-to-CSR and complete construction,
  fixed64step kernel service, rowwise CFL analysis. No annual run is executed.

The original R=6371000m,kappa=R²*0.01/year and T=0.0001year are artificial.
At256x128 the corrected main128/half256 pair is below5% for x,y,z,q. Smaller Euler
steps alone do not help the old large-stock summation: its error grows at512steps.
Kahan and extended-state diagnostic sweeps agree and show first-order time error.
The actual spatial error remains; it must not be tuned away. On x, continuum error
can INCREASE as time error decreases because the two signed errors partly cancel.

Example short full check (output must not exist):

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK
PYTHONPATH=experiments PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B -m hr2_p1_explore_dt.checks \
  --archive ../ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_EXPLORE_20261031_01 \
  --output /NEW/EXCLUSIVE/EXPLORE_DT
```

The compact operator can instead be constructed afresh using an original `sphere`
and `CompactOperator(mesh)`. Advance with `compensated.advance(op,V0,steps,end)`;
interpret returned state with `physical(hi,correction)`. Full new geometry synthesis
and field admission are outside this tiny manufactured example.

Remaining limits: narrow harmonic/regression scope, standard-numeric reference
rather than a proof, platform extended precision (64mantissa bits on this FAIR
runtime), unchanged highly conservative polar low-flux CFL, incomplete hardened
native/journal/B0 recovery and nonharmonic coupled validation. A reduced VALIDATE
is PROPOSED, not executed. Do not discard compensation or reuse old native schema.

For corrected evolution, use `compensated.advance` / `compensated.step`, NOT
the baseline methods inherited by CompactOperator. The latter class provides
geometry/cache construction; its historical stepping methods remain unchanged.
