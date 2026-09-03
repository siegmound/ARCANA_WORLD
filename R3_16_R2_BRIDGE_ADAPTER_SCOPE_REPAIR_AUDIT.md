# R3.16-R2 — C2 Bridge Adapter Scope Repair Audit

## Trigger
The canonical R3.16 run failed before exposure integration because `run_bridge_macrostep()` instantiated the sealed R3.15 environment adapter. R3.15 deliberately rejects ages below 250 ka, so the first R3.16 exposure sample inside the 250→125 ka macro-step failed with:

`ValueError: R3.15 adapter is scoped to 30 Ma -> 250 ka only`

## Root cause
This was an authority/scope binding defect, not a scientific-model failure. R3.16 owns a new sampling scope across the C2 bridge, while R3.15 must remain fail-closed at 250 ka.

## Repair
- Added `R316C2BridgeEnvironmentAdapter`, derived from the R3.15 adapter but with an R3.16-only 250→120 ka environmental sampling guard.
- The inherited D3/C2 substrate conversion is reused unchanged.
- `run_bridge_macrostep`, quadrature refinement, endpoint-only shadow, 125 ka diagnostics, and exact 120 ka environmental diagnostics now instantiate the R3.16 adapter.
- R3.15 source is unchanged and still rejects 200 ka.

## Scientific impact
NONE.

No change to:
- C2 provider equations or payloads;
- 125 kyr biology cadence;
- gene-flow cadence/cap;
- lifecycle/speciation/extinction/fission/coalescence cadence;
- quantitative-genetic parameters;
- Deep coupling;
- canonical parent R3.15 checkpoint.

## Regression evidence
- R3.16 tests: 10/10 PASS.
- R3.15 tests: 12/12 PASS.
- R3.14 tests: 13/13 PASS.
- Focused regression: 35/35 PASS.
- R3.16 formal candidate audit: 314/314 PASS.

A new regression test and four formal-audit checks prove that R3.16 accepts 125/120 ka environmental samples while R3.15 remains fail-closed inside the C2 bridge.
