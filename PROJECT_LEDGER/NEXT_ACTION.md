# NEXT: F2B-D2 — operator semantics and asymmetry reconciliation (design/audit only)

**Completed gate:** F2B-D1B report docs/arcana/SI1_BW1_F2B_D1B_GEOGRAPHIC_BASIS_AUDIT.md, audited at checkout HEAD d539a9ffa281d3dac8489db4820715cb136e9ae6; report SHA256 baa9e450f866f29a42230ad01bd490de6ed6c96f02df3d901e6af77388a41546. The exact historical ShellSet source commit df670c8c4faaed641997f5c4bdb701e2ba0afc7d establishes slot 1 = +South/+theta and slot 2 = +East/+phi, with matching inspected assembly, forcing, boundary-condition and output paths. This does not adjudicate the ten asymmetry pairs or ARCANA frame authority. Preserve DOF_MAPPING_UNVERIFIED for anomaly-to-geography/plate/physical attribution and preserve BLOCKED_F2AV_QUALIFICATION.

## Next scope
F2B-D2 should examine expected operator semantics, assembly/linearization, boundary treatment, and the ten asymmetry records without inferring cause from their indices. F2B-D3 resource/residual design remains a separate gate. This is a recommendation only; it authorizes no Fair/MPI/Solver/factorization/gauge/simulation.

## D1B restrictions retained
- Audit was static/read-only. No Fair, MPI, Solver, factorization, gauge, assembly, simulation, or canonical/WORLD_HISTORY mutation.
- No plate/geographic attribution by index analogy and no solver authorization or scientific qualification.

---

## Historical D1A handoff and evidence publication (preserved)
D1A produced DOF_MAPPING_PARTIAL at checkout HEAD f7b66b2276ef9c33af7012f453b0f01902575cd6. Result: outputs/r6_si1_bandwidth_f2b_d1a_attestation/D1A_RESULT.json; manifest SHA256 5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a, result SHA256 74328b449f41fbf7b467582adb53715c518a09327807401a1dbb4a789aff07a9. Final review added protected output-root checks and independent original FEG/runtime hash plus Git-blob validation; revised attestor reproduced the same result and manifest hashes. It attests node permutation, FEG/runtime reordering, staged F2A-V pair and raw DOF-to-node/component-slot mapping; it does not establish geographic basis semantics.

D1A evidence Git LFS publication is recorded by commit c6bc94c0cac134146722b0c751f55255c68f03dc; archive SHA256 b9fc3a7053e5c18a3d38e67ae367f418e5041f018d3ac9eafe82fa3dce1e9f9d; manifest SHA256 5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a. The publication ledger update is preserved in remote commit bb529b32c4571241c90160423f277248bb9a35a7.

Original F2A-V historical decision remains BLOCKED_F2AV_QUALIFICATION; F2B_SOLVER_EXECUTION_AUTHORIZED=false. D1A geographic component meaning had remained DOF_MAPPING_UNVERIFIED until the bounded D1B source audit above; geographical attribution of the ten anomalies remains unverified.

## Historical design checkpoint
F2B-D1 design defined offline, read-only verification of the raw matrix DOF -> reordered node/component -> original node chain. D1A attests that nodal/index portion; D1B separately resolves ShellSet source component semantics. F2B-D2 operator semantics and F2B-D3 resource/residual design remain distinct.