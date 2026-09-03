# v0.6D1-R3.9 — Canonical 150→66 Ma H0 Continuation & Pre-CHA1 Arrival Contract

## Purpose
Continue World-1 H0 from the sealed R3.8 150 Ma restart boundary to the exact CHA-1 event time, while remaining strictly on the pre-impact side of the discontinuity.

## Time semantics
The existing CHA-1 pulse audit seals `exact_event_time_preferred=true`, an exactly zero pulse before impact, and a positive pulse at impact. Therefore R3.9 defines its terminal state as **66.0 Ma PRE_IMPACT (66.0−)**. The ordinary 125 kyr biology loop may evolve the state through the interval ending at 66.0 Ma, but it must not apply the CHA-1 event operator.

150→66 Ma is exactly 84 Myr = **672 biology cadences** of 125 kyr.

## Input authority
R3.9 must load the R3.8 sealed JSON+NPZ checkpoint and verify both hashes against `SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_8.json`. Historical 210→150 replay is not part of the normal R3.9 path.

## Output
A JSON+NPZ pair named `WORLD1_H0_66Ma_PRE_CHA1_CANONICAL_CHECKPOINT_v0_6D1_R3_9` containing the complete R3.8 restartable state, explicitly marked `PRE_IMPACT_66P0_MINUS` and `cha1_applied=false`.

## Gates
- exactly 672 ordinary biology steps;
- terminal age exactly 66.0 Ma;
- no CHA-1 event in ordinary event history;
- full save/reload identity of the 66.0− checkpoint;
- Deep biological coupling remains OFF;
- no new K, mu, b, ceiling, migration, selection, RI/speciation or paleogeographic calibration.

No ordinary continuation younger than 66.0 Ma is authorized by R3.9. The next operator must be the dedicated CHA-1 high-resolution event stage.
