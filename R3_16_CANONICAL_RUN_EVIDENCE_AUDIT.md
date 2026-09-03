# R3.16 Canonical Run Evidence Audit

Observed canonical execution:

- verdict: `PASS_CANONICAL_R316_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__125KA_PRE_120KA_RESTART_CHECKPOINT_READY`
- wall time: 13.488613367080688 s
- biology steps: 1
- endpoint: 0.125 Ma
- species: 134
- components: 295
- total population: 1217.8946033288662
- all discrete event deltas: 0
- peak q: 0.047631033446597144
- peak unclipped q: 0.047631033446597144
- clipping steps: 0
- C2 500-y substeps consumed: 150
- C2 500-y substeps remaining to 120 ka: 10
- adaptive clock used as biology timestep: false
- biology advanced to 120 ka: false
- serialization identity: true

Canonical artifact hashes:

- JSON: `aaf0bab510b4bcb5fbf77707ad66201515342cf8eb25b687e8f15952d2afca32`
- NPZ: `de0ef549d2fc74f1546e320b3fc3e0bc2f7ca7cbf5ebac464976494ad4055593`

Interpretation:

The result closes the 250->125 ka fixed-biology macrostep while preserving the 200->125 ka C2 environmental history as exposure quadrature. The remaining 125->120 ka environmental interval is exactly 5 kyr (10 x 500 y) and remains biologically unresolved for R3.17. No richness target, guild target, Deep coupling, or scientific parameter change is used.

Repairs encountered before the successful run are governance/integration repairs only:

1. R1: Windows nested pytest basetemp materialization.
2. R2: dedicated R3.16 bridge adapter scope 250->120 ka while preserving the sealed R3.15 guard.
3. R3: reopen the same sealed A1 NPZ as `NpzFile` for the inherited R3.8 `.files` container contract.
