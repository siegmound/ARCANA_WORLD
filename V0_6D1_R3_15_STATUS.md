# v0.6D1-R3.15 status

**CANONICAL RUN PASS — POST-RUN EVIDENCE PASS — LOCAL SEAL GATE READY**

Canonical result:

- 30.0 Ma -> 250 ka
- 238 fixed 125 kyr biology intervals
- 134 species
- 295 components
- population 1218.3485572325976
- 23 speciations, 126 fissions, 45 coalescences, 0 ordinary extinctions
- q peak 0.05161661899812446; final q max 0.04765910934404694; no clipping
- C2 bridge not crossed
- adaptive clock not promoted to biology cadence
- serialization identity exact

Evidence:

- focused regression: 31/31 PASS
- full inherited regression: 312/312 PASS
- independent post-run evidence audit: 234/234 PASS

R3.15 becomes SEALED only after `run_v0_6D1_R3_15_sealed_checks.ps1` re-validates the materialized R3.14 C1/C2/B1/B2/v0.6.1 authority on the user's machine and emits `R3_15_SEAL_SUMMARY.json`.
