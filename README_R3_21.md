# R3.21 candidate overlay REV4 — local use

Overlay these files onto the current ARCANA WorldSim working root.

REV4 is a **read-only extraction-geometry correction** after the canonical REV3 fail-closed exposed an invalid shape assumption. It does not change H0, CHA-2, Deep, biological dynamics, or any SEALED authority.

Corrections accumulated through REV4:

1. recognize the canonical R3.19 reduced-state NPZ keys:
   - `reduced_va_within`
   - `reduced_ancestry_covariance`
   - `reduced_neutral_segregation_potential`
   - `reduced_adaptive_coordinate`
2. preserve those four arrays into a derived read-only R3.21 reduced-state artifact;
3. fail closed if the canonical reduced state is missing or malformed;
4. read the historical event class from checkpoint field `event` as well as `event_type`/`type`;
5. therefore preserve real event classes such as `deme_fission`, `deme_coalescence`,
   `speciation`, `ordinary_background_extinction`, and `paleogeographic_support_loss_remap`;
6. include `event` in the extinction gate so ordinary background extinctions cannot be missed.


REV4-specific correction:

- restore the SEALED R3.7/R3.8 reduced-state geometry exactly:
  - `reduced_va_within[component, trait]`
  - `reduced_ancestry_covariance[component, trait]`
  - `reduced_neutral_segregation_potential[component, component, trait]`
  - `reduced_adaptive_coordinate[component, trait]`
- only the segregation-potential state is pairwise; ancestry/LD covariance is component-by-trait.

Run:

```powershell
.\run_v0_6D1_R3_21_checks.ps1
.\run_v0_6D1_R3_21_present_lineage_registry.ps1
```

Expected candidate status:

`PASS_R321_PRESENT_LINEAGE_REGISTRY_CLOSURE_CANDIDATE`

The run still accepts only the exact R3.19 SEALED checkpoint pair by SHA-256.

Additional REV3/REV4 outputs:

- `R3_21_REDUCED_GENETIC_STATE.npz`
- `R3_21_REDUCED_GENETIC_STATE_SUMMARY.json`

After the run, ZIP `outputs/v0_6D1_R3_21` and return it for final independent seal audit.
