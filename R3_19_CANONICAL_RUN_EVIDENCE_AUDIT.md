# R3.19 Canonical Run Evidence Audit

Canonical local run verdict:

`PASS_CANONICAL_R319_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_CHECKPOINT_READY`

Observed canonical result:
- biology steps: 1
- biology endpoint: 0 ka
- species: 134
- components: 295
- population: 1217.2506240828814
- event delta: exactly one `paleogeographic_support_loss_remap`; all other governed discrete-event deltas zero
- peak q / peak unclipped q: 0.047601695825828454
- clipping steps: 0
- transport: exactly 2 x 62.5 kyr
- phase-aware transport: true
- constant-forcing R3.8 equivalence: bit-exact true
- old single-environment shadow is not identical; shadow population 1217.241447649682
- exact 0 ka inaccessible population mass: 0.0
- checkpoint serialization identity: true

Canonical checkpoint SHA-256:
- JSON: `658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71`
- NPZ: `f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406`

Interpretation: the R3.19-R2 endpoint reconciliation is active and conservative. It resolves the discrete topology mismatch detected by the previous fail-closed run without altering continuous phase forcing, scientific parameters, or cadence. The 0 ka checkpoint is eligible for independent replay sealing.
