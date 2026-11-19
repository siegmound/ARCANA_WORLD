# First physical inputs — preparation, not an evolution

`audit.py` reads and rehashes existing HR2-P0 inputs/contracts; no validated R1 or
other physical model is imported. It measures actual payload availability and
maps original/v2 elevations to the already numerically tested32x16 sphere.
`mapping.py` uses exact latitude/longitude overlap in spherical area coordinates,
with longdouble accumulation and explicit UNKNOWN intersection masks. Source
raster values are treated piecewise constant for this remap. Only the resulting
discrete area-elevation integral is conserved, NOT sediment volume or mass.
Full-cell means remain NaN if ANY supported source overlap is unknown; separate
conditional means and known fractions do not impute missing values. Original
source arrays, native dtypes and masks are unmodified.

The readiness diagnostic rejects mapped elevations as mobile-cover state. Missing
physical diffusivity/law/substrate/coverage bindings remain explicit. It is not a
complete hardened future admission API and does not create synthetic cover,
density or a substitute thermal/hydrology simulation. Unit fixtures are labeled
synthetic adapter checks; no physical steps are executed.

Explicit read/mapping run (new output directory required):

```bash
PYTHONPATH=experiments PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B -m r1_physical_inputs_v1.audit \
 --base /home/jlpfritas/HPC-POMDP/Arcana --output /NEW/EXCLUSIVE/INPUT_AUDIT
```

There is no execution mode for a falsely admitted physical state. Native R1 is
unchanged. A later real-input scenario needs actual cover stock/parameter law,
source meanings/units/epoch and boundary/mapping selection. Surface height,
crust thickness and thermal diffusivity must not be reused as these quantities.
