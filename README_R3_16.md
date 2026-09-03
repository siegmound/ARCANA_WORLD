# R3.16 — C2 Bridge Exposure-Preserving Fixed Biology

R3.16 crosses the 200 ka C2 environmental boundary without turning the 500-y
environmental schedule into biological timesteps.

Canonical run:

```powershell
.\run_v0_6D1_R3_16_c2_bridge_fixed_biology.ps1
```

Expected endpoint: **125 ka**. The 125->120 ka five-kyr remainder is deliberately
left for the next governed stage.


### R3 runtime-A1 container-contract repair
R3.16 reopens the same sealed `FULL_A1_REFERENCE_210_0Ma.npz` as an `NpzFile` for the R3.8 runtime because R3.8 explicitly inspects `a1.files`. R3.14 provider construction continues to use its dict view. This is a container/binding repair only: no arrays, equations, scientific parameters, cadence, or parent authority changed.
