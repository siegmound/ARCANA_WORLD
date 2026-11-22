# ARCANA R6 — FAIR 640 upstream thermodynamics provider *preflight*, NOT scientific execution

**Operator reported on 2026-11-22**  
**Exact tested Git SHA:** `393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2`  
**Branch:** `r6/thermo-providers-official-pilot-20261122`  
**Integration base:** `97fcf1f6d04690784bd70367323eb52b66518630`  
**Decision:** `FAIR_640_THERMO_PROVIDER_SOURCE_AND_CONTRACT_PASS__EXTERNAL_SCIENCE_NOT_RUN`  
**Evidence:** FAIR terminal pasted by operator; raw remote evidence bytes not independently downloaded.

## Exact reported terminal summary

```text
THERMO_PILOT_CODE_HEAD=393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2
THERMO_PILOT_AUTHORITY=OFFICIAL_EARTH_FIXTURE_ONLY__NO_EXTERNAL_ENGINE_RUN_YET
35 passed in 0.12s
640 passed in 4.49s
{"status":"SOURCE_REGISTER_PINNED__EXTERNAL_RUNTIME_NOT_YET_QUALIFIED",
 "sha256":"1cdfa4b3e361e5398ebba4c07a9516995ee04f419e6ce365c3b07c91e1cd8948",
 "official_engine_executions":0,"physical_T1":null}
FAIR_THERMO_PROVIDER_PILOT_TARGET_35=PASS
FAIR_THERMO_PROVIDER_PILOT_SELECTED_640=PASS
FAIR_THERMO_PROVIDER_REGISTRY_PINNED=PASS
FAIR_THERMO_EXTERNAL_MAGEMIN_EXECUTIONS=NOT_RUN
FAIR_THERMO_EXTERNAL_PERPLEX_EXECUTIONS=NOT_RUN
FAIR_THERMO_CROSS_PROVIDER_SCIENCE=NOT_AUTHORIZED
FAIR_THERMO_PHYSICAL_T1=NULL
```

35 new targeted tests **included in** the 640 selected R6 cases; not 675 tests. This qualifies source pinning, provider DTO/guards and selected software regression only; it **does not** certify MAGEMin, Perple_X or GeoParams scientific execution.

## Release-pinned engines (not yet executed)

- MAGEMin_C.jl `v2.4.5` upstream commit `f4fd5ce3670b73693d046e65585e2b79d45c8e3a`, exact Julia Project.toml git blob `d75b3a13e95e217ddff656dce2a0e26cda6e0db3`; `ig` database for official README examples.
- Perple_X `v7.3.3` upstream commit `950d882bb6a9325a627109aa7154f7b526aa3087`, Linux release SHA256 `ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7`; fast source `test/bl691_MEEMUM` fixture `hp62ver.dat` and official reference report.
- GeoParams `v0.10.0` pinned but not part of this stage.

Current preflight write-once FAIR evidence paths:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_THERMO_PROVIDER_PILOT_TARGET_35_NEW01.log
  R6_THERMO_PROVIDER_PILOT_SELECTED_640_NEW01.log
  R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01/PREFLIGHT.json
  R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01/MANIFEST.json
```

The printed source register SHA256 was `1cdfa4b3e361e5398ebba4c07a9516995ee04f419e6ce365c3b07c91e1cd8948`. The user did not provide raw bytes of remote evidence or confirm any external engine installation.

## Required real scientific stage

Only the next independent FAIR stage can demonstrate actual calculations: install pinned Julia and MAGEMin outside `arcana-r6-linux`, install the pinned Perple_X binary/source with the published asset digest, verify their real package/data versions and execute two upstream MAGEMin examples and the official Perple_X fast single-point MEEMUM case. Compare each provider to **its own official reference**, including P/T/chemistry, phase fractions and mass balance. The three initial fixtures have different P/T/chemical systems, so their numerical outputs are **not yet a valid cross-provider accuracy comparison**.

On successful official fixtures, the next more computationally expensive stage is an independent same-composition, same P/T/redox/H2O thermodynamic database-crosswalk experiment with repeated runs, perturbation and numerical checks. More computational load alone does not fix incompatible thermodynamic reference models. No Earth analogue is automatically natural ARCANA T0 geology, and the canonical/historical simulation remains blocked.

```text
FAIR_SOFTWARE_PREFLIGHT = PASS 35/35; PASS 640/640 inclusive
EXTERNAL_MAGEMIN = NOT_RUN
EXTERNAL_PERPLE_X = NOT_RUN
SCIENTIFIC_CROSS_ENGINE_COMPARISON = NOT_AUTHORIZED
G2_ROCK_AND_WATER_SOURCE_RATIFIED = false
MECHANICAL_SOLVE_AUTHORIZED = false
D_024 = ACTIVE
PHYSICAL_T1 = null
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```
