# Next-stage handoff after R3.8 SEALED

R3.8 has established the canonical World-1 H0 restart boundary at exactly 150 Ma. The checkpoint contains full demographic/spatial state, lineage/lifecycle persistence state and the complete R3.7I reduced genetic state. Direct/reloaded 150→149 continuation is exact.

## Next natural stage

`v0.6D1-R3.9 — Canonical 150→66 Ma H0 Continuation & Pre-CHA1 Arrival Checkpoint`

Start from the sealed R3.8 checkpoint; do not replay 210→150 in the normal path.

CHA-1 has exact event time 66.0 Ma and the existing pulse audit explicitly prefers exact event-relative time. R3.9 must therefore produce the **66.0 Ma pre-impact (66.0−) state without applying CHA-1**. Reaching 66.0 on the 125 kyr ordinary biology cadence is allowed because 150→66 is exactly 672 cadence steps; the CHA-1 pulse itself belongs exclusively to the following high-resolution event stage.

R3.9 should:
- load and hash-validate the sealed 150 Ma checkpoint;
- execute exactly 672 ordinary H0 biology steps to 66.0 Ma;
- apply no CHA-1 pulse or Deep biological coupling;
- save a restartable 66.0 Ma **PRE_CHA1** JSON+NPZ checkpoint using the R3.8 serialization schema/mechanics;
- perform an immediate serialization identity gate and a short audit-only continuation on a branch that does not cross the CHA-1 event;
- preserve R3.7I production authority and K_CENTER operational-reference semantics.

The next stage after R3.9 should be a dedicated CHA-1 high-resolution event bridge beginning from this exact 66.0− state. It must not fold the pulse into the ordinary 125 kyr loop.
