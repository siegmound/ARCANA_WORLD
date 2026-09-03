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


## R4.39-R2 source-semantic dynamic representability refinement

Live R4.39-R1 found exactly one out-of-range dynamic state:
`precipitation_factor` at 0 ka with max `1.0000001192092896`.

R4.39-R2 does NOT treat that live value as permission for epsilon clipping.

Instead it binds the repair to the SEALED R3.33 source file
`r333_holocene_environment_domestication.py`,
SHA256 `c32d78efcffccf60dd0a70870dc6d9555a9eed823ec4fa5e7fb3c2e61705fc40`.

That source:
- reads `precipitation_factor_relative_book` and `npp_factor_relative_book`;
- temporally interpolates them as `P` and `N`;
- writes `P` and `N` directly into canonical fields;
- only clips P to 1.5 and N to 1.2 inside the separately derived
  `hydroclimate_resource_index`.

Therefore neither relative factor has a SEALED canonical `[0,1]` domain
guarantee suitable for Geonomics `Layer.rast`.

Dynamic authority is refined to:

- 147 native dynamic Geonomics layers;
- 4 canonical sidecars:
  - temperature_anomaly_c
  - precipitation_factor
  - npp_factor
  - sea_level_anomaly_m
- 1323 native anchor states (`147 × 9`);
- 1176 exact future change targets (`147 × 8`);
- 4704 exact compiled targets across four frozen replicates.

R4.37's 149+2 static initial evidence is preserved and not rewritten.
The two relative-factor layers that were representable at 20 ka are simply
removed from the R4.39 dynamic model before changer construction.

No canonical value is changed. No epsilon tolerance, scaling, clipping, or
result-selected transform is introduced.


## R4.39-R3 Geonomics ndarray change-raster dim metadata repair

R4.39-R2 closed dynamic representability. The remaining live failure is an
upstream Geonomics 1.4.9 metadata ordering mismatch during LandscapeChanger
construction: canonical numpy rasters are `(y,x)=(90,180)`, while
`Layer.dim`/`Landscape.dim` are `(x,y)=(180,90)`. For ndarray changes,
`_make_lyr_series()` reports `dim=change_rast.shape`, then
`_make_conglom_lyr_series()` compares that directly with `land.dim`.

R4.39-R3 never transposes a canonical raster. A temporary source-audited
wrapper calls the original `_make_lyr_series()`, verifies the ndarray shape is
exactly the reverse of `Layer.dim`, and changes only the returned metadata dim
to `lyr.dim`. The original Geonomics function is restored immediately after
`make_model()`. Required evidence is 1176 metadata repairs per replica, 4704
total, zero rejected shapes, zero raster transposes/value modifications, and
4704 compiled changer targets still exact against ARCANA canonical arrays.


## R4.39-R4 `_make_lyr_series()` tuple-return compatibility repair

Live R4.39-R3 reached the dim-metadata adapter but failed because the wrapper
treated each Geonomics series item as a bare raster. Geonomics 1.4.9 actually
returns `list[(timestep, raster)]`.

R4 validates both tuple elements and checks raster shape on `step[1]`, while
verifying `step[0]` keeps the exact Geonomics timestep label.

Only returned `dim` metadata is repaired. No timestep, tuple, raster, raster
shape, raster value, canonical value, or installed Geonomics file is modified.

Required across four replicas:
- 4704 metadata repairs;
- 4704 tuple-structure validations;
- 4704 timestep-label validations;
- 4704 exact compiled canonical targets.
