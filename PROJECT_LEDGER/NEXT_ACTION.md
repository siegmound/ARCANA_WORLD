# NEXT: F2B-D3D — FAIR_EXISTING_EVIDENCE_ACQUISITION (proposta; read-only)

## F2B-D3C completato — ricognizione locale delle evidenze runtime/risorse
Decisione `D3C_RECONNAISSANCE_COMPLETE__EXECUTION_AUTHORITY_GAPS_REMAIN`; report `docs/arcana/SI1_BW1_F2B_D3C_FAIR_RUNTIME_RESOURCE_RECONNAISSANCE.md`, SHA256 `76a5a65adbbc7d6a9b6a64b35497ee9cd3f4642f286d672579d2779f7f53d058`.

Risultato: il runtime upstream qualificato non è il runtime F2A-V per identità dimostrata. L'eseguibile F2A-V non ha hash verificato; toolchain, ABI e linkage dinamico effettivi non sono attestati. Nessun eseguibile F2B è stato identificato. RSS/PSS/cgroup e limiti Fair effettivamente imposti restano sconosciuti; le formule D3A sono stime condizionali. I due test symlink sono ancora `NOT_TESTED_RUNTIME_WINDOWS`. D3C non ha acceduto a Fair né avviato job.

### F2B-D3D — acquisizione di evidenze Fair preesistenti
Proposta limitata a leggere e verificare artefatti già prodotti: identità/hash del binario F2A-V e build/link metadata, toolchain/librerie/ABI attestabili, scheduler/process/cgroup limit records, rank/PID e misure RSS/PSS già disponibili. Non avviare job o processi, non compilare, non eseguire MPI/ShellSet/Solver né diagnostici numerici. Se una prova non esiste negli artefatti preesistenti, registrarla come gap e richiedere un'autorizzazione separata per l'acquisizione necessaria. La verifica POSIX dei due casi symlink è requisito separato e non è prova Fair.

Questo next gate non autorizza build, job, Solver, diagnostici numerici, mechanics o evoluzione canonica.

## F2B-D3B-P0 completato — review circoscritta
Decisione: `D3B_P0_REVIEW_PASS_WITH_BOUNDED_SCOPE`; source baseline parent `f571516ce09c726bffd262d172a922968bdab944`; implementazione dei quattro validator/test inclusa nel commit documentale corrente. SHA256: resource validator `cae86cd5d16d3f4633d45a9ae4ffb6a9808838c41fd2c8ac6e3bf317f5c548ae`; numerical validator `275714d7615cffa062c8ac1d4a992edd5a2070744653a6b4cf0cfec914e7b46e`; resource tests `7e2ddf108836229e79475ffe47b2f2cd19d256beaa8459bd51451b93b1c2fec1`; numerical tests `5b00d4a6b4220b0675183e43a1f028572a437825bfc383ce55d3b9cd1a8ce8aa`.

Esito suite D3B-P0: 24 PASS, 2 SKIPPED, 0 FAIL. I rilievi della prima review e il TOCTOU HIGH sono chiusi nello scope offline. I due test symlink sono `NOT_TESTED_RUNTIME_WINDOWS` (creazione negata); WSL è risultato inaccessibile. La prova POSIX dir-fd/O_NOFOLLOW non è stata eseguita. Atomicità contro sostituzioni concorrenti Windows, ABI NVHPC, RSS/memoria ed enforcement Fair restano non attestati. Il validatore non autentica oggetti Git storici. Nessuna qualificazione del caso SI1 reale.

**Proposta storica D3C (completata; esito sopra), ricognizione read-only:** identità/hash dell'eseguibile e librerie collegate, ABI, richieste e enforcement scheduler, limiti memoria/tempo, evidenze RSS/PSS/cgroup. Se disponibile un ambiente POSIX appropriato, verificare separatamente i controlli runtime symlink. Non avviare job Fair, MPI, ShellSet o Solver.

Preservare: `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

## Storico workpack D3B-P0

**Completed D3A audit:** `docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md`, SHA256 `CA2FF09491BBDCB995FC79FB9E4CF66B461C519A2FC67F652E09099C70884989`; result `D3A_AUDIT_COMPLETE__SOLVER_PREFLIGHT_NOT_ATTESTABLE_FROM_CURRENT_EVIDENCE`. D3 report SHA256 `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF` and its contents remain unchanged.

**D3 arithmetic erratum:** historical A0/b0-copy estimate was about `4.82684 GiB`; corrected total is `5,183,806,076 bytes + 112 × (LRn+1)` (about `4.82780 GiB` plus LR term). The omitted `1,031,072 bytes` are the complete copied RHS b0. This is an arithmetic correction only; no copies were allocated and no strategy was selected.

Preserve `DOF_MAPPING_PARTIAL`; `DOF_COMPONENT_BASIS_SOURCE_VERIFIED__F2AV_GEOGRAPHIC_ATTRIBUTION_UNADJUDICATED`; `OPERATOR_CLASS_UNVERIFIED`; and original `BLOCKED_F2AV_QUALIFICATION`. `F2B_SOLVER_EXECUTION_AUTHORIZED=false`.

## D3B-P0 workpack

This is an offline Python validator task, not a qualification of the SI1 operator and not Solver authorization. Keep resource and numerical validators separate and use only small synthetic fixtures.

### Resource validator
- Inputs: SI1 dimensions from the engineering contract, explicit ABI widths, and an independently transcribed named-array inventory from D3A. Optional budget scenario is `NO_PRESERVATION`, `COPY_A0_B0`, or a separately specified replayable matvec representation.
- Compute element counts/bytes with checked integer multiplication and addition. Reject negative/invalid dimensions, overflow, missing/unsupported ABI sizes, duplicate/missing inventory rows, formula mismatch, incomplete budgets, or any request to certify peak/total process memory while overhead is UNKNOWN.
- Reconcile each array family independently against D3A; report matrix, fixed arrays, `112*(LRn+1)`, optional preservation increment, and excluded descriptors/compiler temporaries/stack/MPI/LAPACK/allocator/OS overhead separately. Never label a named-array subtotal as a peak or upper bound.
- Positive tests: known SI1 arithmetic; small alternate dimensions; ABI-width cases supported by an explicit schema; the independent A0 and b0 copy deltas. Negative tests: overflow boundaries, absent/mismatched dimension, unsupported ABI, duplicate or missing allocation family, arithmetic disagreement, and an incomplete/UNKNOWN total-memory budget. Acceptance is deterministic arithmetic plus explicit scope/UNKNOWN fields; incomplete required inputs fail closed.

### Numerical validator
- Build tiny general-band matrices in test code and encode LAPACK DGBSV storage: `LDAB=2*KL+KU+1`, diagonal at one-based row `KL+KU+1`. Implement band matrix-vector multiplication and original-matrix norms without invoking DGBSV or any solver. Ignore reserved factorization-fill rows as original coefficients.
- Keep immutable synthetic `A0,b0`; give a destructive mock disposable copies and verify the originals remain byte/value-identical. These fixtures validate arithmetic only and say nothing about SI1 symmetry/operator class.
- Compute `r=b0-A0*x`, `||r||∞`, normwise backward error `||r||∞/(||A0||∞||x||∞+||b0||∞)`, and componentwise backward error `max_i |r_i|/(sum_j |a_ij||x_j|+|b_i|)`. Use robust scaled products/sums or a declared extended/compensated accumulation strategy; report subnormal/underflow behavior and reject silent overflow/underflow or nonfinite operands/results.
- Positive tests: diagonal and off-diagonal bands with nonzero KL/KU, padded storage, exact solution and known nonzero residual; compare against an independent dense reference. Negative tests: shape/index errors; NaN and ±Inf in A0/b0/x; extreme large/small values; overflow/underflow; zero denominator with zero numerator; zero denominator with nonzero numerator. Define the latter as undefined/infinite and fail closed. Do not add an arbitrary pass/fail tolerance.
- Acceptance is only algorithm correctness on synthetic cases, complete special-value classification, and A0/b0 preservation. No synthetic test may qualify or accept the SI1 solve.

### Separate Fair read-only reconnaissance procedure
- Without submitting jobs or launching processes, record executable path/size/SHA256 and existing build identity; compiler, MPI and linked LAPACK identity from available metadata/read-only inspection; scheduler memory/wall-time request; process limits; job/cgroup memory limits and enforcement; rank mapping; and existing per-PID RSS/PSS/cgroup peak evidence.
- Distinguish operator-declared requests, scheduler configuration, enforced limits, and observed measurements. If a value or link identity requires job launch, mark `PENDING_HPC_MEASUREMENT`; do not infer it from upstream ShellSet benchmarks or F2A-V’s pre-Solver stop.

### Prohibitions and gates
- No Fair job, MPI, ShellSet, Solver, factorization, assembly, gauge, simulation, canonical change, or WORLD_HISTORY access.
- Preserve `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, original `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- D3B-P0 cannot establish numerical acceptance, resource sufficiency, or authority for execution. A later gate must separately close Fair resource enforcement, A0/b0 retention/reconstruction, numerical thresholds, operator/nullspace/gauge questions, and explicit execution authorization.

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
