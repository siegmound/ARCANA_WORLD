# F2B-N2C-W3-A — authoritative invocation identity and provenance contract

## Decision

`W3A_IDENTITY_CONTRACT_DEFINED__RUNTIME_BINDING_AND_MPI_WIDE_STOP_UNPROVEN`

This source-grounded contract defines the identity required for a later
candidate capture. It does not implement or qualify runtime capture. The W2
overlay remains
`N2C_W2_CANDIDATE_OVERLAY_IMPLEMENTED__RUNTIME_CAPTURE_BLOCKED_BY_IDENTITY_AND_CODEC_BOUNDS`.
No ShellSet build, run, MPI, Solver, DGBSV, factorization, Fair job, or
WORLD_HISTORY access was performed for this audit.

Audit checkout: branch `r6/si1-bandwidth-f2av`, HEAD
`fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`. The vendored source lock records
source commit `9fef54f6cd17e6e756db3ec28bfc43ee0230fc27` as a lock claim; this
audit did not establish that claim by dereferencing that historical Git
object. The checked-in lock and member hashes identify the source contents
used for this static review. The expected remote baseline
`be89b9c899e54f2ac8c78587b22414f887b4350a` could not be fetched because
`github.com` name resolution failed. Therefore remote ancestry and publication
are unverified and no commit or push is claimed.

Locally checked SHA256 identities for the inspected source artifacts:

| Artifact | SHA256 | Authority scope |
|---|---|---|
| `configs/r6_shells_si1/shellset_source_lock.json` | `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2` | Current lock bytes; its historical commit field remains a claim |
| `external/ShellSet-v1.1.0/src/MOD_Shells.f90` | `860b1311e3e2f856b86c7e4f5e988d0591ddf95ff958add1753672dfa9c737f4` | Current vendored member matched to lock; no runtime binary identity |
| `scripts/r6_si1_bandwidth_f2b_n2c_w2_overlay.py` | `3c29bca5e28dc2d997d3edbcf06433e1469afd933acbde7596aacebc42972872` | Candidate overlay builder source at audit HEAD |
| `src/fortran/r6_n2c_shellset_capture_bridge.f90` | `6cb4879400ac425e334d19e771ecf10f68ed45418a1ce2712f42fe31cd3d6a85` | Candidate bridge source at audit HEAD |
| `src/fortran/r6_sparse_snapshot_writer.f90` | `243d698e6d180ebfa22448d88f37f21976be69fc1eeeac0506953192c74f3a32` | W1 writer source at audit HEAD; synthetic scope only |

## Scope and evidence boundaries

The source trace is limited to the vendored ShellSet call graph, the W2
candidate overlay/bridge, the W1 standalone writer contract, the N2A
feasibility report (`SI1_BW1_F2B_N2A_IMMUTABLE_SNAPSHOT_FEASIBILITY.md`),
the N2B wire-format report (`SI1_BW1_F2B_N2B_SNAPSHOT_INTEROPERABILITY.md`),
the checked-in source lock, and the previously recorded D1A scope. Source
lines below refer to `external/ShellSet-v1.1.0/src/` files in this checkout.
These establish code-level data flow, not the identity of a running process,
actual effective inputs, ABI, or a real FEM invocation.

The post-`VBCs`, pre-`Solver` point is appropriate for observing the system
that ShellSet would hand to Solver: `FEM` calls `BuildF`, `BuildK`, `AddFSt`,
and `VBCs`, then `Solver` (`MOD_Shells.f90:3707-3734`). `VBCs` modifies both
`f` and `k` (`3727-3730`); `Solver` receives them as modifiable arrays, and
the downstream DGBSV path is destructive. This ordering does not itself
provide an invocation identity or authorize continuing into Solver.

## Source-grounded identity findings

| Field | Source evidence | Established meaning | Authority still missing |
|---|---|---|---|
| MPI rank and process role | `ShellSetMain.f90:88-98` initializes MPI and branches `ThID == 0` into coordinator; `:567-575` workers receive work and set `ModNum` from `MPI_TAG` | `ThID` is the communicator rank in this program; rank 0 is coordinator in this flow, and workers are nonzero ranks | Run/job identity, communicator generation, PID/host binding and durable rank record |
| Model dispatch | `ShellSetMain.f90:567-575` obtains `ModNum=msg_stat(MPI_TAG)`; master dispatch is in the send paths around `:244-261` and `:429-447` | MPI message tag is used as the local model-number dispatch value | Stable model identity/content digest and a master-owned dispatch ledger binding sender, destination, tag and assignment generation |
| Outer repetition | `ShellSetMain.f90:690-700`, `:783-794` | `rpeat` counts SH calls from 1; it is incremented before each SH call. On an SF final call, it is incremented only if `MaxIter /= 0`; therefore a valid SF call can have `rpeat=0` when `MaxIter=0` | W2 bridge rejects `rpeat<1` (`r6_n2c_shellset_capture_bridge.f90:65-66`), so W2's current validation rejects that valid zero-repeat case. W3-B must model SH/SF phase and permit zero where source semantics require it |
| Pure iteration | `SHELLS_v5.0.f90:736-755` calls `Pure`; `MOD_Shells.f90:6940` owns `iter` in `DO 1000 iter=1,maxItr` | `iter` is local to a `Pure` call | `iter` alone is not unique across `Pure` or Shells calls |
| FEM call ordinal | `MOD_Shells.f90:6996-7010` invokes FEM from the Pure loop; W2 inserts a counter initialized at the Pure scope and increments before FEM (`scripts/r6_si1_bandwidth_f2b_n2c_w2_overlay.py:121-143,172-192`) | Candidate ordinal is monotonic only within one Pure invocation | It restarts for another Pure invocation. Needs a parent Shells-call/phase sequence and Pure-call ordinal in the key |
| Effective model inputs/state | `ShellSetMain.f90:577-585`, `:694-700`, `:788-794`; input files and `ListVarValues` flow into Shells/Pure and may be updated between outer iterations | Initial staged files and local model number do not uniquely identify the values effective at one FEM call | Digest/version for the exact effective variable vector, input records and relevant state on this invocation |
| Boundary/forcing state | `MOD_Shells.f90:3707-3730` assembles then applies `AddFSt` and `VBCs` to `f,k` | A0/b0 identity must be taken after these operations | Digest of resolved constraints/forcing and direct binding of final matrix/RHS values to the invocation |
| Source/build identity | Source lock lists source member hashes; W2 overlay manifest records candidate source transformations/hashes | Candidate source tree identity can be declared and checked against files | Executable hash, compiler/flags, linked runtime identities, and proof that this build is the process executing the capture |
| DOF ordering | D1A established `DOF_MAPPING_PARTIAL` for its audited permutation and staged F2A-V inputs | The prior nodal permutation scope is useful provenance | It does not prove the ordering used by a candidate FEM process. Bind FEG/runtime/permutation identities and ordering ID; retain geography as `DOF_MAPPING_UNVERIFIED` |
| Snapshot payload | W1 emits ARCNSNP1 under synthetic bounds and accepts a caller-supplied source-value digest | Format/fixture behavior has synthetic cross-compiler evidence | W1 does not compute SHA-256 or establish that the supplied digest describes the arrays. SI1 dimensions exceed W1 caps |

### Rank and dispatch semantics

Do not encode `rank > 0` as the general definition of a valid MPI rank.
For this particular ShellSet call path, rank 0 is the master/coordinator and
does not enter the worker model loop, while nonzero ranks are workers. W1's
`rank > 0` requirement belongs to its TEST_ONLY fixture context. A production
context needs an explicit role field (`COORDINATOR`, `WORKER`, or an
enumerated future role) and must validate the role/rank pair against an
authoritative dispatch record. The tag-derived `ModNum` is a transport value,
not a globally stable model identity. Tag reuse, model reuse, communicator
restarts, and run boundaries require an assignment sequence and run scope.

### Invocation key

The candidate identity must be a typed, versioned record rather than a set of
free-form labels. Minimum fields:

1. `schema_version`, `run_uuid`, `run_attempt_uuid`, `job_execution_id`,
   communicator identity/epoch, host/process identity, numeric MPI rank and
   explicit process role.
2. Master-issued `assignment_sequence`, sender rank, received MPI tag, local
   `ModNum`, stable model identity, and digest/version of the model definition.
3. Shells call: phase (`SH` or `SF`), monotonically assigned Shells-call
   sequence, `rpeat` (nonnegative; phase-aware), `Pure` call sequence, `iter`,
   and FEM ordinal within that Pure call.
4. Exact effective input/state identity at the call: input manifest digest,
   effective variable-vector digest, state/version identifier, and resolved
   forcing/constraint digest after `AddFSt`/`VBCs`.
5. Candidate source-overlay manifest digest, complete candidate source-tree
   digest, compiler and compile/link flags, linked library identities, and
   executable SHA256 tied to the launched process. A source-lock claim alone
   is insufficient.
6. DOF ordering identity tied to the exact FEG, runtime, and permutation
   evidence used by this candidate. Preserve
   `DOF_MAPPING_PARTIAL`; geographic/plate interpretation remains
   `DOF_MAPPING_UNVERIFIED`.
7. Capture point identifier (`POST_VBCS_PRE_SOLVER`), matrix dimensions/band,
   canonical matrix/RHS digest recomputed independently from the exact arrays,
   payload byte count and SHA256 calculated by an independent verifier, and
   the verifier result identity.

The invocation key must be the canonical encoding of these owner-backed
fields, including a uniqueness domain. Duplicate keys, duplicate assignment
sequences, a tag/source mismatch, missing fields, inconsistent role/rank, or
an invocation with ambiguous ordering is a hard failure. File names and
environment variables may carry a key but cannot be its authority.

An implementation should encode the following typed shape (illustrative
contract, not a claim that these values are currently available):

```text
InvocationContextV1 {
  schema_version: uint32
  authority: { status: VERIFIED | UNKNOWN, owner: enum, evidence_ref: string }
  run: { run_uuid: UUID, attempt_uuid: UUID, job_execution_id: string }
  process: { communicator_uuid: UUID, epoch: uint64, host_id: string,
             pid: uint64, rank: int32, role: COORDINATOR | WORKER }
  assignment: { sequence: uint64, sender_rank: int32, mpi_tag: int32,
                local_modnum: int32, model_id: string,
                model_definition_sha256: SHA256 }
  call: { shells_phase: SH | SF, shells_call_sequence: uint64,
          rpeat: uint32, pure_call_sequence: uint64,
          pure_iteration: uint32, fem_ordinal: uint32 }
  effective_state: { input_manifest_sha256: SHA256,
                      variable_vector_sha256: SHA256,
                      state_id: string, constraints_sha256: SHA256 }
  implementation: { source_lock_sha256: SHA256,
                    candidate_tree_sha256: SHA256,
                    build_record_sha256: SHA256,
                    executable_sha256: SHA256 }
  dof: { ordering_id: string, feg_sha256: SHA256,
         runtime_sha256: SHA256, permutation_manifest_sha256: SHA256 }
  system: { capture_point: POST_VBCS_PRE_SOLVER, n: uint32,
            kl: uint32, ku: uint32, a0b0_sha256: SHA256 }
  payload: { relative_path: string, byte_count: uint64,
             payload_sha256: SHA256, verifier_result_sha256: SHA256 }
}
```

The final `authority` status is VERIFIED only if every required value has an
appropriate owner and evidence reference and all joins have been checked;
otherwise the context remains UNKNOWN and cannot authorize an authoritative
snapshot. UUID/hash syntax validation is only a format check. The schema must
also encode source-valid `rpeat=0` for the SF case, so `rpeat` is unsigned and
its validity is conditional on `shells_phase` and the model's `MaxIter`
authority. Implementations may use the repository's existing contract types
and ARCNSNP1 schema rather than introduce a general identity framework.

## Ownership and verification contract

| Identity layer | Authoritative owner/evidence required | Verification rule | Failure result |
|---|---|---|---|
| Run/job | Run orchestrator and scheduler/job record | Bind immutable UUID to job attempt and candidate executable | UNKNOWN; no authoritative snapshot |
| Assignment/model | Master dispatch record plus model-definition digest | Verify destination rank, sequence, tag and model digest together | Reject unbound/reused assignment |
| Worker/rank | MPI communicator and process-role record | Verify actual rank and role; rank 0 coordinator is not a worker invocation in this flow | Reject role/rank inconsistency |
| Call/iteration | Shells/Pure/FEM call counters under one run assignment | Unique hierarchical sequence including SH/SF, Pure call, rpeat, iter, FEM ordinal | Reject duplicate/ambiguous key; allow source-valid `rpeat=0` for SF |
| Inputs/state/constraints | Exact effective in-memory values or independently sealed input/state records | Hash effective call inputs and resolved constraints; staged file hashes alone are insufficient | Keep UNKNOWN; do not call payload authoritative |
| Source/build | Candidate source manifest and reproducible build/runtime record | Bind source tree, toolchain/link set and executable hash to process | Candidate/build identity unverified |
| DOFs | FEG/runtime/permutation evidence and runtime ordering token | Match node/component mapping to exact captured matrix ordering | Keep `DOF_MAPPING_PARTIAL`; geography UNKNOWN |
| A0/b0 and payload | Independent canonical hash path and external decoder/verifier | Hash the exact post-VBCs arrays before writing; after process exit recompute payload SHA, decode and compare all bits to an independently retained/reference digest | Any mismatch, missing digest or incomplete file is non-authoritative |

The writer's `source_value_sha256` is caller input, not authentication. A
production proof needs a separately implemented digest over the same live
arrays (or another independently justified binding), followed by an external
reader that verifies payload length, payload SHA256, invocation sidecar, and
canonical A0/b0 identity. The digest must not be generated solely from the
payload writer's own traversal and then treated as independent evidence.
Successful `FLUSH`/`CLOSE` does not establish durability or atomic publication;
`.tmp` files and partial writes remain non-authoritative. The verifier may run
after a diagnostic process terminates because capture mode must stop before
Solver; there is no capture-and-solve mode.

## Fail-closed execution boundary

W2 inserts a per-process gate immediately after VBCs. In `DEFAULT_OFF`, the
bridge calls W1's no-op mode and permits that process's original control flow.
In non-default mode, W1 currently rejects the empty, non-TEST_ONLY context;
the FEM branch raises `ERROR STOP 86` before the local Solver. This establishes
only source-level local control flow. No compiler/runtime proof was performed
here, and no MPI-wide stop is established. Another worker may be at a
different invocation or retain default-off state; an uncoordinated local stop
can leave peers running. W3-B must prove one job-scoped capture-mode decision
and a coordinated pre-Solver stop across the communicator (or demonstrate a
single-worker execution contract), including failure propagation and absence
of Solver entry on every participating worker. This is a precondition, not an
authorization to execute a job.

## W3-B acceptance tests (offline/candidate only)

- Positive synthetic invocation: owner-issued run/assignment/model records
  bind to worker rank and a unique SH/SF → Pure → iter → FEM key; `rpeat=0`
  succeeds only in its source-valid phase.
- Duplicate/reused tag, duplicate assignment sequence, wrong worker rank,
  role/rank mismatch, repeated Pure ordinal, missing run/input/state/source/
  executable/DOF identity, and altered effective variables/constraints all
  fail closed.
- Candidate source patch is reproducible from locked inputs into a new tree;
  output manifest distinctly hashes original locked files, patch, candidate
  sources, and build inputs.
- Snapshot payload and sidecar are externally verified against exact fixture
  arrays; alter, truncate, collide, or leave partial `.tmp` files and verify
  none can be promoted to authoritative status.
- Inject writer and verifier failures and prove the capture process cannot
  enter Solver. Test coordinated multi-worker abort semantics in a synthetic
  harness, without invoking ShellSet or DGBSV.
- Validate candidate dimensions and checked arithmetic separately from Fair
  memory/I/O authority. Current W1 caps `n<=2048` and storage `<=2,000,000`;
  SI1 `n=128884`, `KL=KU=727`, `LDAB=2182`, `LDAB*n=281,224,888`, so current
  codec rejects the SI1 shape. Do not present codec caps as RAM limits.

## Verification performed and required next gate

Static audit only: repository/source and call-flow inspection; no tests,
compiler, Fortran execution, Fair access or HPC job was used for this W3-A
contract. The source-grounded findings are not a runtime provenance
attestation. `W3A_IDENTITY_CONTRACT_DEFINED__RUNTIME_BINDING_AND_MPI_WIDE_STOP_UNPROVEN`
is the bounded decision.

Next technical work: **F2B-N2C-W3-B — candidate invocation-context and
process-wide capture-stop implementation**, limited first to synthetic
fixtures and isolated overlay. W3-B must close authoritative assignment and
effective-state ownership, phase-aware invocation uniqueness, independent
snapshot validation, and communicator-wide fail-before-Solver behavior. Codec
scale and Fair resource/I/O constraints remain separate and open. These are
the distinct **W4 scale/I/O** workstream: remove or revise W1 fixture bounds
only under a separately reviewed streaming/size contract, then establish
file-system capacity, throughput, failure recovery, and Fair resource
authority. W3-B must not treat closing identity as closing W4. No W3-B
implementation, Fair job, Solver, factorization or canonical action is
authorized by this contract.

## Preserved gates

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`;
`THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`;
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
