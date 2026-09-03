# ARCANA WorldSim v0.6D1-R4.39
## Geonomics Runtime Time Mapping, Nonliteral Carrier Dynamics & Dynamic Layer Change Preflight

Parent:
- R4.38 integrated 29/29 PASS;
- R4.38 final seal 21/21 SEALED.

R4.39 does not execute a scientific Geonomics timestep.

## 1. Exact ordinal time mapping

Canonical state index 0 is the already-installed state of the unrun model at `t=-1`.

Each following canonical state `i` maps to Geonomics main timestep `i-1`.

Therefore:

- J14: 141 canonical states -> `T=140`, timesteps `0..139`;
- J18: 15 canonical states -> `T=14`, timesteps `0..13`;
- J21: 9 canonical states -> `T=8`, timesteps `0..7`.

Physical interval lengths are retained in the mapping.

J14's 20 kyr spacing is uniform. J18/J21 are irregular, so their Geonomics
timesteps are explicitly **ordinal transition labels**, not equal-duration
physical-time units.

No generation time or physical rate is invented.

## 2. J21 dynamic layers

The R4.37 representability partition is preserved:

- 149 native `[0,1]` canonical fields;
- 2 physical-unit sidecars:
  - `temperature_anomaly_c`;
  - `sea_level_anomaly_m`.

Across all 9 anchors this gives:

- `149 × 9 = 1341` native canonical raster states;
- `149 × 8 = 1192` future exact change targets.

Every future transition is compiled as:

```python
start_t = t
end_t   = t
n_steps = 1
```

This is an exact jump to the next canonical anchor. It deliberately creates no
intermediate interpolated raster.

For each of four frozen J21 seeds, R4.39 constructs a Geonomics 1.4.9 model
and inspects the compiled `LandscapeChanger` without calling it.

Required per replicate:

- 149 initial canonical rasters exact;
- 1192 compiled change functions;
- exactly 149 change functions at each timestep 0..7;
- all 1192 compiled target arrays exact against ARCANA canonical arrays;
- changer `next_change` begins at t=0;
- model remains `t=burn_t=it=-1`.

Across four replicates: 4768 exact compiled change targets.

## 3. Nonliteral carrier dynamics

R4.39 explicitly does **not** authorize ordinary Geonomics autonomous carrier
dynamics.

Geonomics' main queue increments model/community/species time and then can
perform movement and population dynamics. The ARCANA carriers are not literal
census individuals, and `population_proxy` is not their count.

Until a pre-result authority maps those carrier semantics and physical interval
durations to a domain-specific execution queue:

- autonomous movement = NOT AUTHORIZED;
- autonomous population dynamics = NOT AUTHORIZED;
- autonomous ageing interpretation = NOT AUTHORIZED;
- default Geonomics main queue = NOT SCIENTIFICALLY AUTHORIZED.

This unresolved authority is a correct preflight result, not an error.

## Still forbidden

- `run()`
- `walk()`
- `run_default_model()`
- `LandscapeChanger._make_change()`
- numeric target execution
- readjudication
- canonical writes
- Deep biological coupling

`geonomics_execution_ready=false` remains mandatory.

## Run

```powershell
.\run_v0_6D1_R4_39.ps1
```

## Next if SEALED

`BUILD_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_AND_EXECUTION_QUEUE_PREFLIGHT`
