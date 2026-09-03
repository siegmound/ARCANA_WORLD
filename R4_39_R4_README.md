# ARCANA WorldSim v0.6D1-R4.39-R4
## Geonomics `_make_lyr_series()` timestep/raster tuple repair

Live R4.39-R3 exposed that the adapter interpreted a `(timestep,raster)` tuple
as a bare raster.

R4 checks shape on tuple element 1 and verifies tuple element 0 is the exact
Geonomics timestep. Only returned dim metadata is repaired.

Expected across four frozen replicas:
- 4704 metadata repairs
- 4704 tuple validations
- 4704 timestep-label validations
- 4704 exact compiled canonical targets

No changer execution or model run occurs.

Run:
```powershell
.\run_v0_6D1_R4_39_R4_tuple_repair_and_reseal.ps1
```
