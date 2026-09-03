# ARCANA WorldSim v0.6D1-R4.39-R2
## R3.33 Source-Semantic Dynamic Representability Repair + R4.39 Reseal

Live R4.39-R1 found one out-of-range canonical dynamic state:
`precipitation_factor` at 0 ka, max `1.0000001192092896`.

R4.39-R2 explicitly refuses an epsilon clamp.

The repair is instead grounded in the SEALED R3.33 source:
`src/arcana_worldsim/scientific_engines/r333_holocene_environment_domestication.py`
SHA256:
`c32d78efcffccf60dd0a70870dc6d9555a9eed823ec4fa5e7fb3c2e61705fc40`.

R3.33 directly interpolates and writes both:
- `precipitation_factor_relative_book`
- `npp_factor_relative_book`

without imposing a canonical `[0,1]` output bound. Broader clipping is used
only inside the derived `hydroclimate_resource_index`.

Therefore R4.39 full-trajectory dynamic authority is:

- 147 Geonomics-native dynamic layers;
- 4 canonical sidecars:
  - temperature_anomaly_c
  - precipitation_factor
  - npp_factor
  - sea_level_anomaly_m
- 1323 native anchor states;
- 1176 future exact change targets;
- 4704 compiled exact target closures across four frozen seeds.

R4.37's already-SEALED static 20 ka evidence remains unchanged:
149 native initial layers + 2 sidecars, 596 bindings.

The two R4.37-bound relative-factor layers are removed from R4.39 dynamic
parameter dictionaries before `make_model()`. No canonical value is changed.

No:
- epsilon tolerance;
- scaling;
- clipping;
- normalization;
- result-selected transform;
- changer execution;
- model run;
- scientific execution;
- readjudication;
- canonical-state write.

Run:

```powershell
.\run_v0_6D1_R4_39_R2_source_semantic_repair_and_reseal.ps1
```
