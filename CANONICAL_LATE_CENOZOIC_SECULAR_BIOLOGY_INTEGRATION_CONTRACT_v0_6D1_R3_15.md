# v0.6D1-R3.15 — Late-Cenozoic H0 Fixed-Biology / Adaptive-Environment Integration

## Canonical scope

R3.15 starts from the **R3.14 SEALED 30.0 Ma biology restart boundary** and advances ordinary H0 biology only to **0.25 Ma (250 ka)**.

- start: `30.0 Ma`
- end: `0.25 Ma`
- biology cadence: `125,000 yr` (unchanged R3.7I/R3.8 authority)
- canonical biology steps: `238`
- Deep biological coupling: OFF
- CHA-1 reapplication: forbidden
- second post-CHA1 lifecycle thaw: forbidden
- richness/guild targets: none
- cross-guild recreation operator: not activated

## Why 250 ka is the canonical R3.15 endpoint

R3.14 seals an environmental scheduler with a governed C2 bridge beginning at **200 ka** and a recent restart at **120 ka**. The fixed R3.7I/R3.8 biology grid reaches:

`... 375 ka -> 250 ka -> 125 ka -> 0`

Therefore the nominal step `250 ka -> 125 ka` would cross the 200 ka C2 bridge. Promoting C2's 500-year environmental checkpoints to biological steps would silently change the sealed 125 kyr biology cadence. Collapsing the full bridge into one endpoint sample would silently discard the reason the C2 bridge exists.

R3.15 consequently stops at 250 ka: the last ordinary 125 kyr biology boundary wholly older than the C2 bridge.

## Two-clock rule

The R3.14 adaptive clock is a **scheduler/environmental authority**, not a new biological timestep.

R3.15 MUST keep:

- `biology_cadence_years = 125000`
- `adaptive_clock_used_as_biology_timestep = false`
- `adaptive_clock_checkpoint_promoted_to_biology_step = false`

The C2 provider supplies the environmental state requested by the pre-existing R3.8 endpoint-sampling semantics at each 125 kyr biology boundary. No new averaging, interpolation, rate integration, or environmental-to-biological substep operator is introduced in R3.15.

## Environmental binding

R3.15 uses the existing `D3LateCenozoicSubstrateAdapter` over the R3.14 SEALED `IntegratedLateCenozoicProviderC2` stack.

At 30 Ma, the complete D3 substrate required by R3.8 must be exactly continuous for:

- land support
- accessibility
- temperature
- aridity
- browse forage
- low forage
- wetland forage
- total edible forage
- D3 reference-population/opportunity anchor

No scientific field is replaced by a target value.

## C2/non-claim guard

R3.15 does not enter the C2 200–120 ka bridge and does not cross the 120 ka recent restart. It preserves the R3.14 statements:

- `high_resolution_200ka_historical_paleoclimate_sealed = false`
- `c2_bridge_is_historical_glacial_chronology = false`

## Canonical PASS gates

A canonical 30 Ma -> 250 ka replay may PASS only if:

1. R3.14 seal and 129/129 formal audit are present and hash-consistent.
2. The five v0.6.1 SEALED payloads remain exact by SHA-256.
3. B1/B2 and the C2 provider rebuild successfully.
4. The stored R3.14 adaptive clock exactly matches the rebuilt clock.
5. Full D3 substrate identity at 30 Ma is exact.
6. Exactly 238 ordinary biology steps are executed.
7. No new CHA-1 extinction/bridge/thaw event is introduced.
8. Population remains non-negative and absent from inaccessible cells.
9. Reduced genetic S invariants remain finite/symmetric/zero-diagonal/non-negative within existing tolerances.
10. `q <= 0.08` with zero clipping.
11. The C2 bridge and recent restart are not crossed.
12. Checkpoint save/load is exact under the existing R3.8 comparison gate.

Species richness, diversification sign, guild recovery, or Earth-analogue values are descriptive outputs only and are not acceptance targets.

## Next boundary

R3.16 must begin from the R3.15 250 ka checkpoint and explicitly solve the **250 ka -> 125 ka step that intersects the 200 ka C2 bridge**. R3.16 may not simply promote 500-year environment checkpoints into biological updates or collapse the bridge without an audited coupling operator.
