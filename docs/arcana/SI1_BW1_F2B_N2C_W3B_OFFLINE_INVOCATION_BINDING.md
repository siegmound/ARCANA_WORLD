# F2B-N2C-W3-B — Offline owner-backed invocation binding

Date: 2026-10-11
Repository branch at start: `r6/si1-bandwidth-f2av`
Baseline: `db517147e4980bac5227ffd89d09710b3324746e`

## Decision

`W3B_SYNTHETIC_OWNER_BINDING_VALIDATOR_PASS__RUNTIME_AUTHORITY_UNKNOWN`

The implementation validates typed, fixture-scoped provenance joins, unique
physical FEM invocation coordinates, immutable assignment bindings, the
source-valid phase-dependent `rpeat` cases, and a
synthetic capture-only stop using the existing N2A codec and N2C independent
oracle. Its evidence resolver accepts only `SYNTHETIC_FIXTURE_ONLY` records.
It has no production trust store and never returns production authority.

## Reused authority and scope

The W3-A contract is the design reference:
`SI1_BW1_F2B_N2C_W3A_IDENTITY_PROVENANCE_CONTRACT.md` (SHA256
`6f94d4cbcda52eab351e1aa106bcd7d2c1c25f00b78834d2b2b7f3f8d41e2df9`). The
source lock was checked at this checkout; its SHA256 remains
`8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2`.
No locked source or lock file was modified.

The validator delegates ARCNSNP1 decoding and the exact A0/b0 comparison to
`scripts/r6_si1_bandwidth_f2b_n2c_capture_verify.py`, which in turn uses the
existing N2A decoder. The synthetic oracle digest is independently computed
from fixture arrays and compared with the typed system identity and payload.
The snapshot sidecar binds payload length/SHA, source-value digest, dimensions,
bandwidth, invocation key, and DOF ordering identifier.

Typed groups cover run/attempt/job, communicator/process/role/rank,
master-assignment/model, SH/SF and Shells/Pure/iteration/FEM sequence,
effective input/state/constraints, source/build/executable, DOF ordering,
and post-VBCs/pre-Solver system dimensions and A0/b0 identity. Each group
must resolve to a matching fixture evidence envelope with an expected owner
and subject. Envelope bytes are SHA-checked against their declared fixture
digest and their value digest must bind the supplied typed record. These
fixture owner labels are test data, not proof of real owner authority.

## Behavioral checks

- MPI rank 0 is accepted as a `COORDINATOR` process role, but rejected as a
  worker FEM invocation; coordinator validity is not confused with worker
  eligibility.
- `rpeat=0` is accepted only for the fixture's source-valid SF call with
  `MaxIter=0`; SH rejects zero and SF with positive `MaxIter` requires a
  positive repeat.
- The source call graph in `external/ShellSet-v1.1.0/src/MOD_Shells.f90`
  shows `Pure` iterating `iter=1..maxItr` and calling FEM within that loop
  (around lines 6940 and 6996). Accordingly, multiple distinct FEM calls may
  belong to one master-issued assignment. The ledger now permits them while
  freezing the assignment-sequence binding `(run_uuid, attempt_uuid,
  sequence)` to the same assignment values and synthetic owner-evidence
  identity. Reusing that sequence with another model or worker/owner binding
  fails closed.
- Physical invocation uniqueness is checked separately using run/attempt,
  communicator epoch, process/rank, assignment sequence, phase, Shells/Pure
  call sequence, repeat, Pure iteration, and FEM ordinal. Effective state,
  A0/b0 system digest, payload and sidecar contents are excluded from this
  coordinate key: changing them cannot disguise a repeated physical FEM
  invocation. They remain independently validated as capture content.
  `invocation_key` remains the full typed capture identity, not the ledger's
  physical-coordinate uniqueness key. The local ModNum/MPI tag match is
  checked but the tag is not treated as stable model identity.
- Payload/sidecar verification uses the existing independent decoder/oracle;
  altered context/evidence, mismatched assignment, invalid DOF, corrupted or
  truncated payload, inconsistent/incomplete sidecar, writer exception, and
  verification errors fail closed.
- The capture gate returns `CAPTURE_ONLY_STOP_REQUIRED` or `CAPTURE_FAILED`.
  `require_capture_terminal` accepts only those typed, non-entered terminal
  outcomes and rejects unknown dispositions or an outcome marked as having
  entered Solver. A synthetic FEM-caller harness consumes that transition
  before Solver dispatch and checks an entry counter remains zero on both
  successful capture-only and failed capture paths. This is an offline
  control-flow model, not ShellSet runtime or MPI-wide proof.
- A deterministic coordinator models two synthetic workers. Any failed or
  non-stop worker outcome yields failure. This is not MPI execution or proof
  of an MPI-wide stop.

## Remaining UNKNOWN

No actual owner/trust provider is implemented for run/job, master assignment,
stable model definition, communicator/PID/host, effective input/state and
constraints, source/build/executable, runtime DOF order, or captured A0/b0.
The positive fixture therefore reports `UNKNOWN_AUTHORITY`. Existing W2
compile-only evidence does not supply these bindings. The source-grounded W3-A
facts about rank roles and `rpeat` do not identify a runtime invocation.

The implementation does not modify or call the W1/W2 ShellSet path; it does
not create sidecar files, perform durable/atomic publication, or establish
coordinated MPI failure. W1's synthetic format limits remain: SI1 dimensions
`n=128884`, `KL=KU=727`, `LDAB=2182` exceed the synthetic codec bounds. W4
scaling, streaming, resource quotas, and large-file qualification remain
separate.

## Verification record

Focused W3-B, N2A, N2C-W1 writer, and W2 overlay regressions after the B1
reconciliation completed with 41 passed, 1 skipped, and 0 failed. The skip is the existing Fortran writer
execution test because the default `gfortran` compiler is unavailable on
Windows. `py_compile`, UTF-8/LF checks, and `git diff --check` are recorded in
the accompanying ledger entry. These are Windows-local offline checks only. No Fair, MPI,
ShellSet, DGBSV, Solver, assembly, factorization, or canonical-data operation
was performed.

## Gates preserved

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`;
`THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`;
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Next bounded step

W3-B implementation is complete only for synthetic offline validation. Any
W3-C work must first specify how a candidate obtains and binds real owner
records and how all workers receive one capture-mode/abort decision. Until
that authority and a separately authorized candidate integration exist,
runtime capture remains blocked. W4 remains independent; no Solver or Fair
execution is authorized by this result.
