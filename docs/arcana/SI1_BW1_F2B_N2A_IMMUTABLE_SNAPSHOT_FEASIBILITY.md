# F2B-N2A — Immutable linear-system snapshot feasibility

## Decision and scope

**Recommendation: retain strategy C, a sparse binary immutable snapshot, as the preferred design candidate, but do not qualify or integrate it into ShellSet yet.** A bounded Python prototype passes only synthetic format, round-trip, identity, destructive-buffer-isolation, and diagnostic checks. It is not evidence that an SI1 snapshot has been captured, fits Fair resources, or is linked to any historical assembly.

The implementation at scripts/r6_si1_bandwidth_f2b_n2a_snapshot.py is synthetic-only and reuses the D3B-P0 diagnose_system routine. Five focused tests pass. It serializes bytes in memory; it does not implement durable file output, Fortran integration, or the 128,884-DOF case. No ShellSet, Solver, factorization, assembly, MPI, Fair, or canonical state operation was run.

Preserved gates: THRESHOLD_UNJUSTIFIED, OPERATOR_CLASS_UNVERIFIED, BLOCKED_F2AV_QUALIFICATION, F2B_SOLVER_EXECUTION_AUTHORIZED=false, ARCANA_SI1_MECHANICS_QUALIFIED=false, and WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.

## Source trace: one system boundary

The audited sources are the vendored ShellSet files as they exist in the checkout. Their Git blob identities match the historical ARCANA execution commit df670c8c4faaed641997f5c4bdb701e2ba0afc7d:

| File | Historical/current blob |
|---|---|
| external/ShellSet-v1.1.0/src/MOD_Shells.f90 | d036e5d2559738a83c0a42d6922bd457551012c8 |
| external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90 | 171a9284e5509da7b5a2db637df4af7fc19d8821 |

Within MOD_Shells.f90, FEM executes BuildF (3671–3715), BuildK (3716–3721), AddFSt (3722–3726), and VBCs (3727–3730), then immediately calls Solver (3732–3734). Thus the system relevant to a residual is the post-VBCs pair immediately before that call, not the pre-constraint assembly.

- BuildF initializes each RHS entry from fBase (approximately 1110–1120) before adding continuum and fault contributions. In SI1 nFl=0, so the fault loop has no entries.
- BuildK zeroes the whole band array at 1304–1306, then assembles continuum terms; its documentation identifies basal diagonal stiffening (1457 onward). AddFSt is the subsequent fault stiffness contribution; SI1's zero fault-element count makes that loop empty.
- VBCs changes both f and k (10012–10115). It replaces constrained equations and may rotate rows before rewriting them. An A0 snapshot taken before this routine would not identify the operator passed to DGBSV.
- Solver declares ab,b INTENT(INOUT), says the matrix is destroyed and the answer overwrites b (8626–8637), and calls dgbsv at 8672. The SI1 general-band shape is n=128884, kl=ku=727, LDAB=2182, iDiagonal=1455, one RHS, per N1/D3A.

Pure calls FEM within its iteration loop (around 6940 and 6996–7010). It updates the constitutive/strain-rate state between iterations; every later FEM invocation rebuilds the RHS and BuildK zeroes/rebuilds the matrix. The overwritten k/f of iteration q are therefore not a reusable A0/b0 for iteration q+1. A capture must identify exactly one invocation, including the iteration index and the state/configuration that fed it. A top-level model may also execute multiple independent calls; capture identity cannot be inferred from file name alone.

## Candidate representation

The prototype format is ARCANA_SPARSE_A0_B0_SNAPSHOT_V1:

- Fixed little-endian header records n, kl, ku, coefficient-record count and an A0/b0 identity digest.
- Canonically row-major (i,j,binary64-bits) records for every logical-band coefficient except positive zero.
- +0.0 is implicit; -0.0 is explicit. Every nonzero, including a binary64 subnormal, is stored as its raw 64-bit representation. RHS values are always stored as raw binary64 bits, including signed zeros.
- Logical coordinates are zero-based in the file and checked against the declared matrix and band; duplicates, noncanonical order, nonfinite values, invalid indices, unexpected length, nonzero padding, digest mismatch and missing/altered bytes fail closed.
- A source digest covers dimensions, every logical A0 coefficient bit pattern including zeros, and every b0 value bit pattern. A separate SHA256 covers the complete snapshot byte stream.

The matrix source digest is a consistency check, not an independent authority: it is generated from the same captured data. The complete snapshot SHA must be retained independently before Solver entry (and tied to the invocation/provenance record). To bind bytes to the actual assembled call, the future capture must read the post-VBC k/f values before mutation, include DOF ordering, source/build/input identity, invocation/iteration, constraints and dimensions, then finish and verify the snapshot before permitting DGBSV. A write, flush, reread, length, hash or provenance failure must stop before the Solver call. A digest alone cannot prove that the capture hook observed the intended point in the call graph.

Exact coefficient bit preservation is distinct from replaying an identical floating-point matvec. A sparse traversal may accumulate products in a different order from a band traversal or an independent arithmetic oracle; the snapshot establishes the matrix entries, while the residual implementation separately defines and reports its accumulation strategy. It must exclude DGBSV fill rows from A0 while retaining the original kl/ku mapping.

## Storage and operational tradeoffs

N1/D3A gives the full AB copy cost at the stated assumptions as 2,249,799,104 bytes and b0 as 1,031,072 bytes, totaling 2,250,830,176 bytes for a full copy. This is conditional arithmetic, not Fair headroom or RSS.

The historical F2A-V evidence summarized by N1 reports 1,804,327 nonzero matrix coefficients. If that count and the same dimensions applied to a future exact snapshot, this prototype's 16-byte coordinate/value records plus raw RHS and 56-byte header would be about 29,900,360 bytes. This is an illustrative conditional size only: the count was not remeasured here, future A0 occupancy may differ, and format/index/metadata changes alter the result. With this encoding sparse records are smaller than 8-byte full-band values only below approximately 50% logical occupancy; disk I/O and snapshot integrity checks still need measurement. The prototype uses a Python record list and full byte buffer, so its memory behavior is explicitly not a production streaming implementation.

| Strategy | Benefit | Cost / principal risk | Assessment |
|---|---|---|---|
| A. Full AB + b0 RAM copies | Simplest direct identity and residual path; lowest format/integration ambiguity | Adds 2,250,830,176 explicit bytes under the D3A assumptions; Fair headroom and enforcement unknown | Safest semantically, not presently resource-attestable |
| B. Full band snapshot on disk | Preserves the exact band layout directly; easy to compare/restore independently | Approximately same byte volume as a full copy, plus I/O; requires durable completion and checked readback before Solver | Conservative fallback if sparse semantics/integration are not yet trusted |
| C. Sparse binary A0 + b0 snapshot | Potentially much smaller when occupancy is low; retains exact stored values and enough data for matvec/norms | Requires canonical indices, signed-zero policy, source binding, post-VBC insertion, streaming I/O and measured time/storage; sparse matvec order differs | Preferred design candidate, still unqualified |
| D. Deterministic reassembly | Avoids retaining a matrix snapshot | Iteration-dependent tangent/state, constraints, inputs, order and build/runtime must all be reproduced; matching summaries are insufficient | Not demonstrated and not a substitute for capture without exact equivalence proof |

The sparse matrix representation can compute A0*x, ||A0||∞, and rowwise sum_j |A0_ij||x_j| because it preserves every logical coefficient plus dimensions and ordering. No magnitude threshold or coefficient dropping is allowed. A pair of unsigned 32-bit indices and one 64-bit value is portable for this n, but a production Fortran writer must explicitly serialize little-endian integers/bits rather than assume compiler endianness or TRANSFER byte order. The existing Fair ABI and runtime identity gaps remain.

## Offline prototype evidence

The six tests in tests/test_r6_si1_bandwidth_f2b_n2a_snapshot.py cover:

1. Nonsymmetric KL=1, KU=2 synthetic matrix and known RHS/solution candidate; pre-operation snapshot; destructive mutation of separate work AB/RHS; D3B-P0 residual and both backward errors compared against a literal dense oracle.
2. Exact round-trip of a negative zero, smallest positive subnormal, and negative-zero RHS.
3. Truncation and externally retained snapshot-hash rejection.
4. Changed coefficient rejection even when the altered file's outer hash is recomputed, through the stored A0/b0 consistency digest.
5. Omitted nonzero record rejection even when the declared count and outer SHA are recomputed, because the captured source-identity digest no longer matches.
6. Invalid band index, duplicate record and nonzero DGBSV fill/padding rejection.

Result: 6 passed. These tests prove only the bounded synthetic Python contract. The source validator remains unchanged. There was no SI1 array allocation.

## Integration gaps and recommendation

Before ShellSet integration can be considered, a separate design/authorization must define a source-locked capture point after VBCs and before Solver; invocation/iteration identity; raw binary encoding and cross-platform byte order; one-pass or two-pass record count; streaming disk write and durable flush; independent pre-call SHA retention; post-write reread/verification; and fail-closed no-Solver behavior. Then test the instrumentation and file format on small synthetic matrices and a compile-only path. A later authorized SI1 preflight would need storage, I/O duration, resource enforcement and identity evidence before any Solver decision. No current test establishes those.

**Recommendation:** C is the most promising representation if the historical low occupancy applies, with B as the lower-complexity exact-format fallback. A is the simplest correctness reference but consumes substantial additional RAM; D is not presently credible as an identity substitute. Do not select or implement production storage from the conditional historical density estimate. No strategy is qualified for SI1; no Solver authorization follows.
