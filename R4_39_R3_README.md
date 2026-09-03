# ARCANA WorldSim v0.6D1-R4.39-R3
## Geonomics 1.4.9 ndarray Change-Raster Dim Metadata Compatibility Repair

R4.39-R2 closed source-semantic dynamic representability. The remaining live failure is a metadata ordering mismatch inside Geonomics 1.4.9 LandscapeChanger construction.

Canonical raster arrays are `(y,x)=(90,180)`, while Geonomics `Layer.dim` / `Landscape.dim` are `(x,y)=(180,90)`. For ndarray `change_rast`, `_make_lyr_series()` reports `dim=change_rast.shape`, after which `_make_conglom_lyr_series()` compares that y,x tuple directly with land.dim x,y.

R4.39-R3 never transposes a raster. A temporary, source-audited wrapper calls original `_make_lyr_series()`, requires ndarray shape to be the exact reverse of Layer.dim, changes only returned dim metadata to `lyr.dim`, and restores the original function immediately after `make_model()`.

Required: 1176 metadata repairs per replica / 4704 total; 0 rejected shapes; 0 raster transposes/value modifications; Geonomics installation unchanged; 4704 compiled target arrays exact against ARCANA; 0 changer executions; 0 model runs.

Run:
```powershell
.\run_v0_6D1_R4_39_R3_ndarray_dim_metadata_repair_and_reseal.ps1
```
