# ARCANA WorldSim v0.6D1-R4.39-R1
## Dynamic Representability Failure Diagnostic

R4.39 correctly BLOCKED after all time mapping and carrier-dynamics governance
checks passed. The live failure is localized to J21 dynamic representability:
one or more fields classified as native `[0,1]` at the 20 ka initial anchor
leave the native Geonomics Layer domain at later canonical anchors.

R4.39-R1 is diagnostic-only and does NOT rerun Geonomics.

It reads:
- `R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json`
- `R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json`
- `R4_39_INTEGRATED_AUDIT.json`
- time-mapping and carrier-dynamics gate evidence

and emits:

`outputs/v0_6D1_R4_39_R1/R4_39_R1_DYNAMIC_REPRESENTABILITY_FAILURE_DIAGNOSTIC.json`

The report includes every offending canonical anchor state with:
- layer family
- variable
- taxon
- age
- min/max
- SHA256
- finite/range status

No canonical value, R4.39 output, Geonomics model, changer, or gate is modified.

Run:
```powershell
.\run_v0_6D1_R4_39_R1_dynamic_representability_failure_diagnostic.ps1
```
