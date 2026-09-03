# v0.6D1-R3.14 — Late-Cenozoic H0 Environmental Provider Binding & Adaptive-Clock Restart

## Status

`CANDIDATE — LOCAL EXACT v0.6.1 REHYDRATION REQUIRED`

## Parent boundary

Authoritative parent: **v0.6D1-R3.13 SEALED**, exactly **30.0 Ma**.

R3.14 is a binding/restart stage only. It does **not** advance biology beyond 30 Ma.

## Purpose

R3.13 established exact field identity between the ordinary R3 environment and the existing late-Cenozoic provider at 30 Ma. R3.14 converts that endpoint compatibility into an executable production binding by:

1. validating the sealed R3.13 30 Ma checkpoint and hashes;
2. locating the exact v0.6.1 sealed paleoclimate payload by SHA-256, including inside historical ZIP archives;
3. rehydrating only the five required v0.6.1 artifacts into a local minimal root;
4. rematerializing the exact 120 ka B1 A1 boundary from the already-authorized sealed equations;
5. rematerializing the B2 relative-eustatic effective-land boundary;
6. constructing the existing C1 nested CHA-2 provider and C2 200→120 ka replay-safe boundary continuation;
7. constructing and validating the existing C2 adaptive clock from 30 Ma to book era;
8. requiring `production_replay_ready = true` before any later biological replay may start.

## Hard fail-closed rule

The non-authoritative `preview_boundary_from_book_reference` is forbidden for production binding. If the exact v0.6.1 payload cannot be found with the frozen hashes below, R3.14 must stop with:

`BLOCKED_R314_EXACT_V061_SEALED_PAYLOAD_NOT_FOUND`

This is a valid evidence outcome and must not be repaired by inventing or approximating the missing historical payload.

## Frozen v0.6.1 payload hashes

- `AUTHORIAL_SEAL_v0_6_1.json`: `d097f83ce53fb298689c63458dfa1012d26b3983254ccf25085b91f882e55a2a`
- `src/arcana_worldsim/paleoclimate/model.py`: `de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f`
- `recent_paleoclimate_history.npz`: `be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1`
- `paleoclimate_spatial_snapshots.npz`: `a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd`
- `shoreline_state_I.npz`: `f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85`

## Scientific authorities reused unchanged

R3.14 reuses, without calibration changes:

- `late_cenozoic.environment` — 30 Ma→120 ka secular provider;
- `sealed_120ka_boundary` — exact v0.6.1 equation reconstruction and conservative remap;
- `eustatic_land_bridge` — relative eustatic anomaly only;
- `IntegratedLateCenozoicProviderC1` — authorized nested CHA-2 50-y states;
- `IntegratedLateCenozoicProviderC2` — replay-safe 200→120 ka boundary continuation;
- `build_adaptive_late_cenozoic_clock_c2` — adaptive scheduler;
- R3.13 SEALED 30 Ma biological state.

The adaptive clock is a scheduler, not new physics.

## Explicit non-actions

R3.14 does **not**:

- advance population, trait, VA, RI, founder, vicariance, reconnection, or extinction state;
- reactivate CHA-1;
- reactivate the post-CHA1 lifecycle thaw;
- enable Deep;
- introduce richness/guild/population targets;
- activate cross-guild reassignment;
- reinterpret A1 reference population as carrying capacity;
- authorize the v0.6.1 preview/book-era proxy.

## PASS condition

The binding may report:

`PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__BIOLOGY_REPLAY_NOT_STARTED`

only if all of the following hold:

- parent R3.13 seal/checkpoint hashes are valid;
- all five v0.6.1 artifacts match frozen SHA-256 values;
- the v0.6.1 spatial generalizer is bit-exact against a materialized sealed checkpoint;
- B1 and B2 materialize and reload exactly;
- C1 and C2 providers instantiate successfully;
- the bound C2 state at 30 Ma remains exactly identical to the R3.13 handoff fields;
- the C2 adaptive clock begins at 30 Ma, ends at book era, contains 200 ka and 120 ka boundaries, and validates `production_replay_ready=true`;
- biology remains untouched at 30 Ma.

## Output boundary

A successful R3.14 is **not a new biological-time checkpoint**. The authoritative biological state remains R3.13 at 30 Ma. R3.14 adds a sealed environmental/scheduling binding that the next stage may consume.

## Next stage after PASS

`v0.6D1-R3.15 — Late-Cenozoic H0 Adaptive Biological Replay Integration`

R3.15 must still audit how the currently fixed 125 kyr R3.7I/R3.8 biological cadence is coupled to the variable C2 environmental clock; R3.14 does not silently redefine biological timestep semantics.
