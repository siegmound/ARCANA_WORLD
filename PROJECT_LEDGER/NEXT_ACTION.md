# NEXT: F2B-D3A — preliminary resource and numerical attestation (non-executing)

**Completed gate:** F2B-D3 design, `docs/arcana/SI1_BW1_F2B_D3_RESOURCE_RESIDUAL_PREFLIGHT_DESIGN.md`, status `D3_DESIGN_COMPLETE_PENDING_RESOURCE_AND_NUMERICAL_ATTESTATION`. Report SHA256: `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF`. The design is source-derived and does not claim new measurements. It estimates the general-band matrix as `8*nKRows*nRank = 2,249,799,104` bytes under the documented dimensions and ABI assumptions; total memory/RSS, Fair enforcement limits, linked runtime identity, and numerical thresholds remain unattested. `THRESHOLD_UNJUSTIFIED` remains open.

Preserve `DOF_MAPPING_PARTIAL`; `DOF_COMPONENT_BASIS_SOURCE_VERIFIED__F2AV_GEOGRAPHIC_ATTRIBUTION_UNADJUDICATED`; `OPERATOR_CLASS_UNVERIFIED`; and original `BLOCKED_F2AV_QUALIFICATION`. `F2B_SOLVER_EXECUTION_AUTHORIZED=false`.

## Next scope
F2B-D3A is a new, preliminary, non-executing attestation gate. It may verify exact source/input identities, perform overflow-safe static arithmetic/ABI checks, inspect Fair resource-limit mechanisms without launching ShellSet, and validate preflight controls without assembly or Solver. It is not Solver authorization. Do not run Fair MPI/ShellSet, Solver, factorization, new assembly, mechanics, gauge, simulation, or canonical evolution. Do not select residual thresholds without authority; absent a justified numerical acceptance rule, retain `THRESHOLD_UNJUSTIFIED` and fail closed.

## Prior D2 handoff (preserved)
F2B-D2 static operator classification audit: `docs/arcana/SI1_BW1_F2B_D2_OPERATOR_CLASSIFICATION_AUDIT.md`. Result `OPERATOR_CLASS_UNVERIFIED`; theoretical SI1 symmetry is `INDETERMINATE`. Active pointwise alpha values are not retained and the ten global asymmetries remain unexplained. Geographic/plate attribution remains `DOF_MAPPING_UNVERIFIED`; original F2A-V remains `BLOCKED_F2AV_QUALIFICATION`. Do not symmetrize the matrix or infer nullspace from diagonal dominance.

## D2 restrictions retained
- Static source/evidence audit only; no Fair, MPI, Solver, factorization, assembly, simulation, gauge change, or canonical/WORLD_HISTORY access or mutation.
- No solver selection, solver authorization, geographic attribution of anomaly indices, conditioning/singularity claim, or scientific qualification.

---
# PRIOR HANDOFF: F2B-D2 — operator semantics and asymmetry reconciliation (design/audit only)

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
