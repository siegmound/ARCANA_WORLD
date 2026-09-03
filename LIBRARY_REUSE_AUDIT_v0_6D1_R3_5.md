# Library / Source Reuse Audit — v0.6D1-R3.5

R3.5 introduces **no new scientific dependency** and no replacement numerical solver.

## Reused authorities
- `d3_additive_variance_v0_6_3D3_3A.py` — exact gene-flow moment mixing and Riccati homeostasis.
- `rebased_natural_control_runtime_v0_6D1_R3_4.py` — exact scientific trajectory authority.
- `rebased_deep_time_barrier_provider_v0_6D1_R3.py` — existing multi-bracket barrier-history adapter.
- SciPy/NumPy stack already present in the parent runtime.

## Instrumentation implementation choice
Instead of copying/reimplementing the R3.4 loop, R3.5 temporarily wraps the already imported D3.3A functions, records their inputs/outputs, then restores them. The parent `r34.run(...)` remains the only scientific evolution path.

A second diagnostic-only Riccati call with a very high cap is used solely to estimate the unclipped post-homeostasis value. This output is never fed back into population, traits, VA, RI, fission, coalescence, speciation, or demography.

## Rejected alternatives
- A custom VA integrator: rejected; D3.3A exact Riccati operator already exists and is validated.
- Re-running the entire scientific step in a second shadow simulation just for telemetry: rejected as unnecessary and expensive.
- Pandas/xarray for runtime telemetry: not required; 480 compact biology-step records over 210→150 Ma are trivially handled as JSONL and keep the production runner dependency surface unchanged.
- New genealogy/genome libraries: not relevant to this stage; the state remains quantitative-moment based.

## Verdict
`PASS_REUSE_FIRST__NO_NEW_SCIENTIFIC_SOLVER_OR_DEPENDENCY`
