# ARCANA WorldSim v0.6D1-R4.37-R3
## Public-API Incompatibility & Coordinate Representability Closure

R4.37-R2 closed J21:
- 149 native identity payloads;
- 2 canonical physical-unit sidecars;
- 596 exact native bindings;
- no scaling or result-selected transform.

J14/J18 remained blocked because Geonomics 1.4.9's public
`Model.add_individuals(source_spp=...)` path is structurally incompatible with
the R4.36 construction probe:

- the public wrapper contains an undefined `species` reference;
- its source-Species implementation requires `source_gen_arch.L` and
  `self.gen_arch.L`;
- it proceeds through tskit TableCollection union;
- the R4.36 construction probe is intentionally nongenomic (`gen_arch=None`).

R4.37-R3 therefore removes the invalid mutation attempt. For every frozen
replicate it constructs the governed unrun model and validates all canonical
coordinates against the actual Geonomics landscape bounds. It also introspects
the live installed source and freezes the exact public-initializer
incompatibility.

A PASS means **validation closed**, not exact scientific state installed.

R4.38 remains mandatory:
`BUILD_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT`

Run:
```powershell
.\run_v0_6D1_R4_37_R3_validation_closure_and_reseal.ps1
```
