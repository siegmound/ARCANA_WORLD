# F2B-N2C-W3-C-A — Runtime authority owners and coordinated-stop design

## Decision and scope

**Decision:** `W3C_A_DESIGN_COMPLETE__RUNTIME_AUTHORITY_AND_MPI_STOP_UNPROVEN`.

This is a source-grounded static audit and design contract. It neither changes
ShellSet nor demonstrates any MPI behavior. The W3-B/B1 validator remains a
synthetic evidence-join test; W2 remains a candidate overlay whose `CAPTURE_ONLY`
path rejects missing runtime authority. The source-locked ShellSet tree, W1/W2
capture components, source lock, canonical data, and historical evidence are
unchanged. No Fair, MPI, ShellSet, Solver, DGBSV, SI1 capture, or WORLD_HISTORY
operation was run for this audit.

The applicable R6 SI1 contract is
`contracts/R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json`. It defines the
engineering diagnostic's scope and safety gates, not an owner-backed ShellSet
run/attempt/assignment authority contract. No existing R6 contract located in
the cited ledger defines the complete owner chain below. Existing ARCANA
execution/evidence patterns elsewhere are engine-scoped: for example,
`contracts/R4_55_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_EVIDENCE_CAPTURE_CONTRACT.json`
specifies a fixed non-Geonomics job/seed cohort and explicitly disclaims
external-engine definition of the ARCANA target. It is not a ShellSet run or
assignment authority and is not transplanted as one. W3-B `Owned` envelopes and its
`MappingEvidenceResolver` are explicitly fixture-scoped, not a production
trust provider.

## Source-level authority ownership matrix

“Producer” below means the code that creates or observes a value. It does not
mean that the value is authoritative for ARCANA. A value becomes authoritative
only through the owner record and byte/content binding stated in the final
column. W2 local counters and caller-supplied hashes remain observations.

| W3-B identity group / fields | Actual producer and boundary | Available source meaning | Required authoritative owner/evidence and binding | Current status |
|---|---|---|---|---|
| Run: `run_uuid`, `attempt_uuid`, `job_execution_id` | ARCANA launcher/job orchestrator must create before starting ShellSet; no such producer is in the audited ShellSet path. | The F2A-V contract identifies a diagnostic branch/case and historical source/run evidence; it is not a new capture run identity. | Owner-issued run and attempt record, unique execution ID, immutable job configuration and output root; signed or otherwise governed record digest passed to coordinator and bound to candidate executable. | `UNKNOWN`; no applicable ShellSet run contract/provider found. |
| Process: communicator UUID/epoch, host, PID, rank, role | `ShellSetMain.f90:88-90` calls `MPI_INIT`, `MPI_COMM_SIZE`, `MPI_COMM_RANK`; `:93-98` reserves rank 0 as coordinator in this flow; workers are the `ThID/=0` branch at `:553-575`. | `ThID` is the rank in `MPI_COMM_WORLD` for this program; rank 0 is valid MPI coordinator, not a worker FEM call. Size/rank are runtime observations. | Coordinator-owned communicator/run binding plus each process's rank/role acknowledgement in that communicator; host/PID and process launch identity tied to the job attempt. A rank number or environment label alone is insufficient. | Rank role semantics source-demonstrated; communicator UUID/epoch, host/PID and job binding `UNKNOWN`. |
| Assignment: sequence, sender/destination, MPI tag, `ModNum`, model ID and definition digest | Coordinator dispatches work (`ShellSetMain.f90:244-260`, `:427-433`); worker receives work/variables (`:567-575`) and sets `ModNum=msg_stat(MPI_TAG)` (`:575`). | `ModNum` is a local dispatch value derived from message tag. Coordinator generates `ListVarValues`; tag/ModNum are not stable model identity. | Master-owned immutable assignment ledger created before each dispatch, containing run/attempt, sequence, destination, tag, effective variable row and stable model-definition digest. Worker validates the exact received assignment against its coordinator-issued record before entering Shells. | Transport fields source-demonstrated; assignment sequence and stable model authority `UNKNOWN`. |
| Call: SH/SF, `rpeat`, Shells/Pure sequence, iteration, FEM ordinal | `ShellSetMain.f90:690-700`, `:783-794`; `SHELLS_v5.0.f90:735-759`; `MOD_Shells.f90:6940`, `:6996-7010`. W2 inserts the FEM ordinal per `Pure` call (`scripts/r6_si1_bandwidth_f2b_n2c_w2_overlay.py:121-143,172-192`). | `Pure` loops over `iter`; it calls FEM once within each iteration. `rpeat` counts SH calls, while final SF with `MaxIter=0` may validly use `rpeat=0`. A per-Pure FEM ordinal resets for each Pure call. | Candidate-generated hierarchical call trace bound to the immutable assignment: phase, Shells-call ordinal, `rpeat`, Pure-call ordinal, iteration, FEM ordinal, and an independently fixed target selector. Reject a selector that is ambiguous or not the first reachable FEM call in a capture-only job. | Local values/call edges source-demonstrated; globally unique owner-backed call trace and exact target `UNKNOWN`. |
| Effective state: input manifest, variable vector, state ID | Worker receives `ListVarValues` and reads model input after dispatch (`ShellSetMain.f90:569-589`); repeated calls may reload/update data (`:773-794`). Shells/Pure mutate iteration state. | Initial staged file hashes do not prove the effective in-memory vector at one FEM entry. Mutable state evolves across calls. | Governed input manifest and effective variable-vector digest; bind the exact input file set/version and state inputs to assignment and call. For any state transformed in memory, capture/compare its canonical field representation at the FEM boundary. | `UNKNOWN`; no owner-backed effective-state provider. |
| Constraints/forcing digest | `FEM` calls `BuildF`, `BuildK`, `AddFSt`, then `VBCs` (`MOD_Shells.f90:3707-3730`); `VBCs` modifies both `f` and `k`. | Only post-`VBCs` values are the candidate A0/b0 passed next to Solver. Constraint source records and final transformed arrays are distinct identities. | Bind original constraint/input records, resolved boundary-condition inputs and their mapping/order to the call; independently bind the actual post-VBCs A0/b0 snapshot. | Required point source-demonstrated; actual constraints and system `UNKNOWN`. |
| Implementation: source lock/tree, build record, executable SHA | Source-lock file and W2 overlay builder check candidate source inputs; W2-E1 is operator-reported compile-only, `LINK_PERFORMED=false` (`docs/arcana/SI1_BW1_F2B_N2C_W2_CANDIDATE_CAPTURE_INTEGRATION.md`). | Lock and candidate manifest identify source bytes / transformation claims; they do not identify a linked executable executing a capture. | Independently sealed candidate source manifest, compiler/link flags and library identities, build record, executable SHA; bind the executed process to that executable and run attempt. | Candidate source claims/compile-only record exist; linked/running executable identity `UNKNOWN`. |
| DOF: ordering ID, FEG/runtime/permutation digests | SI1 config names governed FEG/runtime artifacts; D1A attests nodal/index mapping only partially; W3-B accepts a typed DOF envelope. | D1A `DOF_MAPPING_PARTIAL` is not runtime proof that this invocation uses that ordering. D1B verifies ShellSet slot meaning in its source frame; ARCANA anomaly/geographic attribution remains unadjudicated. | Bind exact FEG, runtime package and permutation contents to candidate input staging, plus the runtime node/component ordering actually passed to FEM. Independent mapping validation must match matrix indices to this identity. | Static artifacts known; invocation-specific order `UNKNOWN`; preserve `DOF_MAPPING_PARTIAL` and geographic `DOF_MAPPING_UNVERIFIED`. |
| System: capture point, n/KL/KU, A0/b0 identity | `FEM` post-VBCs/pre-Solver boundary `MOD_Shells.f90:3727-3734`; Solver takes arrays `INTENT(INOUT)` and DGBSV overwrites them (`:8626-8673`). W2 bridge is called at the intended boundary in the candidate overlay. | A0/b0 means exact logical matrix and RHS immediately after VBCs for one FEM invocation; DGBSV fill rows are not logical operator entries. | Independently compute a canonical digest from captured original arrays before conversion/write; an independent verifier checks the payload, sidecar, dimensions, ordering and digest against an independently retained oracle. Writer-provided digest is not self-authenticating. | Boundary source-demonstrated; no real captured system, SI1-ready W1 codec, or independent runtime digest. `UNKNOWN`. |

### Existing contracts and provenance boundary

The SI1 diagnostic contract's `mapping_policy` requires component-basis,
permutation and coordinate-mapping artifact links, rejects hashes as proof by
themselves, and falls back to `DOF_MAPPING_UNVERIFIED`. The engineering case
config binds the FEG/runtime and calls its parameter reference
`ENGINEERING_SOLVER_REFERENCE_NOT_ARCANA_GEOLOGY`; neither document identifies
a runtime invocation or an owner of a capture decision. D1A/D1B and W3-A are
reused only within their recorded scopes. W2-E1 is compile-only and
operator-reported; no linked executable was produced. Therefore a valid UUID,
SHA string, tag, PID, environment variable, sidecar, or worker report alone
cannot promote any `UNKNOWN` to verified authority.

## Job-scoped immutable capture decision

### Decision record

Before any ShellSet worker receives work, the run owner must issue one immutable
decision record. Its canonical bytes and digest are fixed before dispatch and
include at least:

1. run, attempt, job execution identity; communicator identity/epoch and exact
   membership/size;
2. `mode=CAPTURE_ONLY`, `solver_permitted=false`, exact candidate source/build/
   executable identity, source/input/DOF manifest digests and external output
   location policy;
3. eligible worker rank(s)/role(s), exactly one selected stable model and
   master-assignment sequence, plus the exact target FEM coordinate;
4. phase SH or SF, Shells/Pure call ordinals, `rpeat`, iteration, FEM ordinal,
   and the source-derived `MaxIter` condition; `rpeat=0` is accepted only for
   the source-valid final SF call when `MaxIter=0`;
5. per-rank assignment table and a uniqueness rule: no reused assignment
   sequence with a different destination/model/owner binding, and no duplicate
   target coordinate even if state or payload hashes differ;
6. fixed terminal outcome policy, time/launcher failure policy, and evidence
   expected from every rank.

The owner record must be produced by the ARCANA run/job authority and master
dispatch authority, not by the ShellSet worker. No such joined provider exists
in the audited R6 SI1 path; until it does, no authoritative decision can be
created.

### Distribution and state machine

The coordinator validates the record and its owner evidence, freezes the
canonical bytes, then distributes those bytes (or a content-addressed immutable
record) to every communicator member before worker assignments. Every rank
checks run/attempt, communicator membership, its own rank/role, the same
decision digest, and its assigned row, then acknowledges that digest. The
coordinator dispatches no model until it has exactly one matching acknowledgement
from rank 0 and every worker. A missing, duplicate, late, conflicting or invalid
acknowledgement fails the job before dispatch. Environment variables may select
the location of a decision but are not the decision or its authority.

```text
UNDECIDED
  -> OWNER_RECORD_VERIFIED
  -> FROZEN_CAPTURE_ONLY_DECISION
  -> BROADCAST_TO_ALL_RANKS
  -> ALL_RANKS_ACK_SAME_DIGEST
  -> TARGET_ASSIGNMENT_DISPATCHED
  -> FIRST_REACHABLE_FEM_POST_VBCS
  -> CAPTURE_VERIFIED | CAPTURE_FAILED
  -> ALL_RANKS_TERMINAL_ACK
  -> COORDINATOR_FINAL_RECORD
  -> JOB_TERMINATED_WITHOUT_SOLVER

Any missing/mismatched owner evidence, ACK, assignment, target coordinate,
payload check, worker status, or timeout -> GLOBAL_FAILURE / NO_SOLVER.
```

Capture-only must be a job-wide immutable mode: the gate denies Solver on every
participating worker for every FEM call, not merely the selected worker at the
selected coordinate. Otherwise another rank or an earlier FEM call could enter
Solver while the selected rank captures. Because `Pure` calls FEM inside
`DO iter=1,maxItr` and normal FEM proceeds directly to Solver, reaching a later
iteration would ordinarily require earlier solves. The first candidate must
therefore target the first reachable FEM boundary of a single selected worker
assignment (and reject any earlier FEM invocation); it cannot claim an arbitrary
later iteration without changing the scientific path or allowing Solver.
Other ranks must receive no scientific assignment in that bounded capture job
and remain in the coordination protocol. If the first reachable call cannot
be established from the frozen record, fail before dispatch.

Rank 0 is a valid coordinator participant and acknowledges the decision, but it
is not a FEM worker in the audited `ThID==0` / `ThID/=0` main-program split.
SH/SF is explicit in the selector. `rpeat=0` is not normalized to 1 and must
remain valid only for final SF with `MaxIter=0`. Dispatch tag/`ModNum` matching
is checked against the immutable assignment but never substitutes for stable
model identity.

## Coordinated-stop protocol options

| Option | Advantages | Failure/race | Assessment |
|---|---|---|---|
| Local `ERROR STOP` at the W2 gate | Existing overlay places it textually before local `CALL Solver`. | Only local source control flow is known. A peer may still be in another FEM or waiting in the main worker protocol; coordinator may wait for normal misfit messages. No MPI-wide termination proof. | Reject as the coordination protocol. |
| Immediate `MPI_Abort` on first capture/failure | ShellSet already calls `MPI_Abort` in several failure paths (`ShellSetMain.f90:97-178,598-604`); avoids waiting forever for a peer that failed. | Existing call sites do not prove exact communicator behavior for the candidate/toolchain, stable exit code, complete evidence flush, or launcher cleanup. If a peer reached Solver earlier, abort is too late. | Emergency fail-stop candidate only after the global no-Solver gate is installed; exact runtime semantics require later evidence. |
| Coordinator-led terminal status/stop handshake | Can record one terminal status per rank, reject missing/duplicate acknowledgements, and send explicit stop to idle workers. Fits the existing master/worker message architecture. | Requires a dedicated capture-only dispatch/return protocol: workers currently send `allmisfits` then block on `MPI_Recv(Work)` (`ShellSetMain.f90:853-856`); master expects misfit records and sends work/stop (`:427-508`). A worker failing before status can leave the coordinator blocked unless there is a bounded timeout/failure handler. | Recommended normal success protocol, paired with an independent hard no-Solver gate on every rank and launcher-level timeout/fail-stop. Not implemented or runtime-tested. |
| Collective barrier/reduction from FEM | Appears to provide all-rank agreement. | Workers can execute different assignment/call counts and reach nested FEM at different times. A collective there is not a safe rendezvous unless the entire capture job is redesigned to ensure identical collective order; process failure can strand peers. | Do not add a collective inside the existing general FEM path. A bounded dedicated job protocol would need a proven collective schedule. |

### Recommended capture-only stop design

Use a dedicated coordinator/worker state protocol, not the current normal
misfit continuation:

1. Before dispatch, all ranks acknowledge the frozen capture decision and set
   a latched job-level `solver_permitted=false` state. This state cannot be
   cleared by later messages or default-off settings.
2. Dispatch exactly one target assignment to one eligible worker; other worker
   ranks are idle participants. At every FEM post-VBCs gate in the candidate,
   check the latch before any `CALL Solver`. Non-target/duplicate/earlier calls
   terminate as failure; no path falls through to Solver.
3. The target worker writes capture-only output and returns a typed terminal
   status up the call chain `FEM -> Pure -> Shells_v5p0 -> worker main`; each
   level must stop its local loops/continuation and bypass velocity scoring,
   ordinary model completion, and normal misfit reporting. Only then does the
   worker send a distinct terminal status to the coordinator. Returning from
   FEM alone is unsafe because the current callers would otherwise continue
   the Pure/Shells/main flow. This status alone is not payload qualification:
   an independent post-process checks payload length/hash, sidecar, owner
   bindings and independent A0/b0 identity after the diagnostic process has
   stopped.
4. The coordinator records only a provisional `CAPTURE_WRITTEN` outcome after
   one terminal ACK per rank and exactly one target writer-completion status.
   It sends a distinct stop message to idle workers; workers send final ACK and
   all ranks follow a defined finalize/exit path. Normal model outputs/misfits
   are not fabricated. After the MPI job has terminated, the independent
   verifier decides `CAPTURE_VERIFIED` or failure from payload, sidecar, owner
   bindings and oracle. A coordinator record or clean stop is not itself a
   successful capture qualification.
5. Any failure, unknown status, missing ACK or timeout moves monotonically to
   failure. The coordinator records known statuses, invokes the selected
   communicator-wide fail-stop mechanism, and the external launcher records
   process exit statuses. Partial files remain non-authoritative. No failure
   branch may reopen Solver permission.

For the first bounded implementation, the run owner supplies the immutable
decision to rank 0 before launch (or via a governed immutable input record).
Rank 0 validates it, distributes one canonical byte sequence and digest to all
ranks before model dispatch, and gathers one ACK per communicator member in a
fixed rank roster. Only then may a specialized capture-only dispatch path send
one assignment to the selected worker and explicit idle/participation messages
to all other workers. The worker terminal status must be a separate message
kind from the ordinary `allmisfits` payload. The main loop must consume exactly
one capture terminal per participating worker and bypass its normal
misfit/next-model path. A missing participant must be detected by a bounded
coordinator wait; it must never be interpreted as success. This design calls
for a pre-dispatch broadcast/gather where all ranks follow the same schedule,
not a collective nested inside asynchronous FEM calls.

This is a design requirement, not a demonstrated MPI protocol. In particular,
the existing `MPI_Barrier` at `ShellSetMain.f90:860` occurs only after workers
exit their work loops; it cannot coordinate a worker stopped at FEM. No
synthetic W3-B state-machine test proves `MPI_Abort`, launcher termination,
or race-free multi-process behavior.

## Failure and race analysis

| Scenario | Required behavior | Why current path is insufficient / evidence required |
|---|---|---|
| Target worker reaches capture before peers | Worker latches no-Solver and waits only in the dedicated status protocol; it must not return through the normal model continuation. | Normal worker proceeds through Solver and later sends misfit; local `ERROR STOP 86` can strand coordinator/peers. Require a candidate call-stack return/status path and runtime evidence. |
| Another worker fails before FEM | Coordinator must not dispatch/continue a target capture and must prevent any worker Solver; terminal failure or timeout must close the job. | Current ShellSet error branches sometimes call `MPI_Abort`, but W2 gate itself is local and no global decision is present. Need fault injection at input read, dispatch, before FEM and before status. |
| Peer reaches another FEM first | Its gate must deny Solver; it reports unexpected/duplicate target/order and fails the job. | A worker-wide no-Solver latch and exact target assignment are absent from W2. |
| Coordinator dies after dispatch | Workers must not infer permission from silence; wait only boundedly, then fail-stop. | Existing worker waits on coordinator MPI messages; no capture decision lease/timeout protocol. Test coordinator termination and launcher cleanup. |
| Payload write/hash/sidecar fails | Target returns failure; no Solver; partial/temp files marked non-authoritative and preserved only under isolated output policy. | W1 writes no runtime SHA authority; W2 rejects CAPTURE_ONLY with empty context. Require external verifier and controlled output ownership. |
| Duplicate assignment or duplicate capture | Reject before model dispatch where detectable, and again at worker/aggregate record validation; never accept “last writer wins.” | Existing dispatch uses model tags and dynamic work scheduling, not an assignment ledger/target cardinality record. |
| One rank hangs / communication error | Bounded wait and launcher-level timeout/failure evidence; no peer may proceed to Solver while waiting. | MPI error handling, timeout enforcement, exit codes and scheduler cleanup were not tested or attested. |
| Normal termination race | Success requires terminal status from every rank and coordinator-issued stop; failure cannot be mistaken for success. | Existing `MPI_Barrier` is downstream of the normal work protocol and is not a capture stop handshake. |

## Independent evidence and authority separation

| Claim | Independent binding required | Integrity check is not enough because… |
|---|---|---|
| Effective input/state/constraints | Owner-approved input manifest; actual staged bytes; effective `ListVarValues`/runtime state at the selected call; constraint records and DOF mapping after resolution; call-bound canonical digests. | A worker-reported hash does not establish who selected the input or that it was the effective in-memory state. |
| Candidate source/build/executable | Source-lock and overlay manifest verified from exact bytes; build command/compiler/flags and library identities; linked executable SHA; process-to-executable/run binding. | A source hash or compile log does not identify a linked executable or the process running it. |
| Runtime DOF ordering | Exact FEG/runtime/permutation manifests and contents plus candidate runtime ordering identity; bind raw matrix indices to node/component slots. | A valid ordering SHA string does not prove the runtime used that permutation; geographic/plate meaning remains separately governed. |
| Post-VBCs A0/b0 | At the one identified call, capture exact logical band coefficients (excluding factorization fill padding) and complete RHS; an independent canonical A0/b0 digest/oracle tied to invocation and ordering. | Payload digest proves byte integrity only; writer self-digest is not independent and neither proves the correct source point was captured. |
| Payload/sidecar | Fresh isolated path; complete file length; externally computed SHA-256; schema/dimension/index checks; sidecar matches payload and all owner-bound context; independent decoder/oracle. | Payload and sidecar written by one untrusted producer can agree while both describe the wrong invocation. |
| MPI job outcome | Per-rank decision ACK, assignment/status sequence, no-Solver terminal record, process exit codes and launcher/accounting record tied to run/job. | A single rank's marker or a synthetic entry counter is not proof that all workers stopped before Solver. |

Use the W3-B `EvidenceResolver` shape only as a possible interface pattern.
Production verification needs explicit owner roots/keys, evidence schemas,
revocation/version policy and a trust bootstrap. Do not call a syntactically
valid UUID/SHA, unverified environment value, or self-authored sidecar an
owner-backed record. Keep data-integrity PASS and scientific/operational
authority decisions separate.

## Minimal follow-on candidate implementation scope

Proposed next bounded task: **F2B-N2C-W3-C-B — offline capture-decision and
coordinator protocol model**. It is not permission for ShellSet/MPI runtime.

### Exact first-scope files/interfaces

1. Proposed new small typed contract module (not created by this design), e.g.
   `scripts/r6_si1_bandwidth_f2b_n2c_w3c_protocol.py`, reusing W3-B dataclasses
   and canonicalization where practical. Define immutable `CaptureDecision`,
   rank acknowledgement, assignment dispatch, terminal worker status, and
   coordinator states. Do not implement a production trust store; authority
   stays UNKNOWN unless a governed evidence resolver is supplied.
2. Proposed new focused test file (not created by this design)
   `tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py`. Test exact all-rank
   decision digest agreement, valid coordinator rank 0/no FEM, one worker/one
   first-reachable target, source-valid SF `rpeat=0`, and multiple unique
   assignments/call coordinates only where the decision permits them.
3. Negative tests: missing/duplicate/mismatched ACK; wrong communicator/run;
   duplicate assignment sequence or target; wrong worker role; rank 0 target;
   invalid SH/SF/`rpeat`/MaxIter combination; target not first reachable FEM;
   capture/write/verification failure; missing worker terminal status;
   coordinator/worker failure or timeout; unexpected status; any Solver-entered
   flag; no-Solver latch cleared or bypassed. All must end `GLOBAL_FAILURE` and
   assert a modeled Solver-entry count of zero, without calling Solver.
4. Extend only the W3-C design report with test results after that offline
   model passes. Ledger update and review remain required before a separate
   source overlay proposal.

### Acceptance gates before any production overlay proposal

- Owner-authority interface is pinned to actual ARCANA job/run, model and
  assignment authority; otherwise keep `UNKNOWN` and stop at design/model only.
- Freeze and validate one job-scoped decision on coordinator and every rank;
  demonstrate exact acknowledgement/uniqueness/error transitions in synthetic
  tests.
- Static proof that every candidate FEM path in capture mode is barred from
  Solver, including failures and non-target calls; W2's local environment
  switch/`ERROR STOP 86` is not enough.
- A separate MPI/runtime authorization and candidate-specific compile/runtime
  plan must precede MPI evidence. Runtime proof must cover target-first path,
  delayed rank, failure before FEM, coordinator loss, timeout, partial output,
  exit status, and launcher cleanup. MPI_Abort/ERROR STOP semantics remain
  unverified until tested on the exact supported stack.
- Independent post-run payload/sidecar/oracle verifier must bind the exact
  capture to owner evidence. W1's `n<=2048` and band-storage test cap still
  excludes SI1 (`n=128884`, `LDAB=2182`); W4 scaling/streaming/resource scope
  is separate and unresolved.

No acceptance gate here grants Solver, factorization, mechanics, Fair job,
canonical publication, or WORLD_HISTORY authority.

## Verification boundary and preserved gates

Source references were inspected read-only in the locked ShellSet source and
candidate W2 overlay. W3-A/W3-B/B1, SI1 contract/config, D1A/D1B, N2A/N2B/W1/W2
evidence were read for scope reconciliation. This task performed no new test,
compile, job, MPI operation, input mutation or evidence acquisition. The
document and ledger update require only UTF-8/LF, local-reference and
`git diff --check` checks; those checks do not verify MPI behavior.

Preserved without change: `BLOCKED_F2AV_QUALIFICATION`,
`OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`,
`RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
