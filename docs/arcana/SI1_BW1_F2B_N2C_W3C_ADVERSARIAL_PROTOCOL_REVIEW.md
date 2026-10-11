# F2B-N2C-W3-C-C — Independent adversarial offline protocol review

Date: 2026-10-11
Checkout: `r6/si1-bandwidth-f2av` at `68b423e96b95b2ccfbe769fcb6d635234616844e`
Remote status: `origin/r6/si1-bandwidth-f2av` could not be queried because DNS resolution for `github.com` failed. Findings apply to the checked-out W3-C-B implementation; the latest remote HEAD was not independently verified.

## Decision

`W3C_C_REVIEW_REQUIRES_TARGETED_CORRECTIONS`

The existing 21 W3-C tests and the combined W3-C/W3-B regression run pass, but reproducible counterexamples defeat the modeled first-reachable target and the claimed latch check. These are defects in the offline model's invariants, not evidence of an MPI or ShellSet runtime failure. No implementation was silently repaired in this review.

## Scope and evidence

Read `AGENTS.md`, the operational ledger in its prescribed order, W3-C-A, W3-C-B implementation/addendum, W3-B/B1 code and tests, and the source-locked ShellSet call-flow references. Source citations below refer to `external/ShellSet-v1.1.0/src/`.

Executed:

- `python -m pytest -q tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py` — **21 passed**.
- `python -m pytest -q tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py tests/test_r6_si1_bandwidth_f2b_n2c_w3b_provenance.py` — **43 passed**.
- Direct adversarial Python probes described below. They are reproductions, not added qualification tests.

No MPI, Fair, ShellSet executable, Solver, DGBSV, SI1, or WORLD_HISTORY operation was performed. No source, lock, or pre-existing output was modified.

## State machine inventory

| State | Entry condition | Success path | Failure/terminal behavior |
|---|---|---|---|
| `UNVALIDATED` | `ProtocolState(decision)` | `freeze()` validates decision and moves to `DECISION_FROZEN` | invalid decision becomes `GLOBAL_FAILURE` |
| `DECISION_FROZEN` | valid freeze, incomplete ACK set | matching unique ACKs; all ranks gives `ALL_RANKS_AGREED` | malformed, stale, duplicate, wrong-origin ACK becomes `GLOBAL_FAILURE` |
| `ALL_RANKS_AGREED` | ACK count equals fixed roster | `complete_acknowledgement()` -> `ACKNOWLEDGEMENT_COMPLETE` | incomplete set/local coordinator ACK fails |
| `ACKNOWLEDGEMENT_COMPLETE` | exact complete ACK set | exact assignment dispatch -> `ASSIGNMENT_DISPATCHED` | wrong/duplicate dispatch fails |
| `ASSIGNMENT_DISPATCHED` | one selected assignment | exact selected target -> `CAPTURE_WRITTEN` | wrong/duplicate/partial/premature verification fails |
| `CAPTURE_WRITTEN` | one complete target capture | unique per-rank terminal statuses -> `WORKER_TERMINALS_COLLECTED` | missing/duplicate/stale/solver-entered/unexpected status fails |
| `WORKER_TERMINALS_COLLECTED` | terminal record for each rank | `coordinate_stop()` -> `COORDINATED_TERMINAL` | invalid cardinality or Solver flag fails |
| `COORDINATED_TERMINAL` | all terminals and one capture | exit code 0 -> `JOB_TERMINATED` | nonzero/early exit fails |
| `JOB_TERMINATED` | modeled exit recorded | `verify_external(passed=True)` -> `CAPTURE_VERIFIED` | failed verification -> `GLOBAL_FAILURE` |
| `GLOBAL_FAILURE` / `UNKNOWN` | invalid protocol event / timeout / crash | none | no transition method provides recovery to success |

Intended invariants include immutable digest-bound fixture decision, fixed roster containing coordinator rank 0, exact per-rank ACK agreement, one dispatched assignment, one target capture, no Solver flags in terminal statuses, all-rank terminal collection before modeled exit, and external-verification phase only after modeled exit. Frozen dataclasses protect the decision/state values against ordinary mutation. This is a single-process event model; it does not model message transport, process scheduling, or MPI failure semantics.

## Findings, ordered by severity

### HIGH — later Pure-call coordinate is accepted as “first reachable”

**Location:** `scripts/r6_si1_bandwidth_f2b_n2c_w3c_protocol.py:142-150`; regression set at `tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py:154-160`.

`validate_decision()` requires `first_pure_call=True`, and requires positive `target.pure_call_sequence`, but never requires that sequence to equal 1. The separately supplied Boolean is not reconciled with the hierarchical coordinate.

**Reproduction:** take the ordinary valid fixture decision, set `target.pure_call_sequence=2`, recompute the decision digest with `freeze_decision()`, and call `ProtocolState(decision).freeze()`. Observed result: `DECISION_FROZEN`, not `GLOBAL_FAILURE`. The current parametrized first-target test varies FEM ordinal, Pure iteration, and Shells-call sequence, but omits Pure-call sequence.

**Impact:** a later `Pure` call can be selected while the record asserts it is the first Pure call. That violates the stated deterministic first-reachable target invariant. The static ShellSet audit identifies `Pure`/FEM call coordinates (`MOD_Shells.f90:6940, 6996-7010`); the fixture decision does not independently establish runtime reachability.

**Minimum correction proposal:** require `pure_call_sequence == 1` for this capture-only first-call contract, and add negative fixtures for sequence 2 and inconsistent “first” flags. If future scope permits a different earlier coordinate, model and justify its complete no-Solver reachability rather than relying on a Boolean assertion.

### HIGH — Solver-boundary test is a constant rejection, not a latch/FEM dispatch proof

**Location:** `scripts/r6_si1_bandwidth_f2b_n2c_w3c_protocol.py:332-338`; tests at `tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py:217-232`.

`solver_dispatch_boundary()` checks rank/callback shape and then unconditionally calls `fail()`. It never reads `no_solver_ranks`, `decision.solver_permitted`, protocol phase, target status, or a modeled FEM dispatch event. Both tests pass because the callback is never invoked even before the decision is frozen. A direct probe replacing `no_solver_ranks` with `()` produces the same blocking result. The counter `solver_mock_entries` is never incremented by this method.

**Reproduction:** call the boundary on a frozen state after replacing `no_solver_ranks` with `()`. Observed result remains `GLOBAL_FAILURE` with “Solver entry attempt blocked by monotonic no-Solver latch”; callback count and `solver_mock_entries` remain zero. This confirms that the latch value is not consulted.

**Impact:** the test verifies that this one function always refuses to call the callback; it does not demonstrate that each modeled target/non-target FEM route consults the monotonic latch, nor that capture/failure paths are connected to the Solver boundary. In particular, the implementation has no transition representing a FEM arrival/gate. The test cannot falsify bypasses in a caller because no caller is modeled.

**Minimum correction proposal:** introduce a small modeled FEM-boundary transition used for both target and non-target invocations. It should validate the frozen capture-only decision and rank membership in the intact latch, fail closed before the callback if either is absent/inconsistent, and model capture/failure terminal return without exposing a success route to Solver. Tests should route target, non-target, earlier-call, capture-failure, and latch-corruption events through that boundary and inspect the callback counter. Keep any permissive Solver branch outside this capture-only model. This still would be synthetic evidence only.

### MEDIUM — rank type accepts Python booleans as worker ranks

**Location:** `scripts/r6_si1_bandwidth_f2b_n2c_w3c_protocol.py:128-129`.

`worker_rank` is compared with rank 0 and membership in the roster but is not checked with `type(worker_rank) is int`, unlike ACK, dispatch, and call-coordinate rank checks. Python treats `True == 1`.

**Reproduction:** replace the valid decision's `worker_rank` with `True`, recompute its digest, and freeze. Observed result: `DECISION_FROZEN` for roster `(0,1,2)`.

**Impact:** malformed typed decision data is admitted as rank 1. Subsequent typed dispatch uses integer rank 1 and therefore hides that the decision itself had a Boolean rank representation. This does not demonstrate production authority, but it weakens fail-closed schema validation.

**Minimum correction proposal:** require exact integer type and roster membership for `worker_rank`; add bool and non-integer negative cases.

## Invariant classification

| Invariant / claim | Classification | Evidence and limit |
|---|---|---|
| Fixed immutable decision value and digest checked at freeze | `SYNTHETIC_TEST_EVIDENCED` | Frozen dataclass and digest tests; self-computed fixture digest is not owner authority. |
| Every roster member, including rank 0 local coordinator, must ACK same run/attempt/communicator epoch and decision digest before dispatch | `SYNTHETIC_TEST_EVIDENCED` | ACK tests and `complete_acknowledgement()`; no actual broadcast/receive or rank agreement. |
| Exact one assignment dispatch and one capture event | `SYNTHETIC_TEST_EVIDENCED` | State transition tests; events are caller-supplied values, not dispatch/FEM observations. |
| First-reachable target across Shells and Pure hierarchy | `UNKNOWN / NOT_EVIDENCED` | Counterexample: `pure_call_sequence=2` freezes. Source call graph is described in W3-C-A; booleans/selector are not bound to source/runtime trace. |
| SH first call, `rpeat=1`, positive outer MaxIter; SF `rpeat=0`, `MaxIter=0` with explicit guard | `SYNTHETIC_TEST_EVIDENCED` | Synthetic predicate tests only; SF guard remains an asserted fixture field, not independently sourced authority. |
| Failure state cannot return to protocol success | `SYNTHETIC_TEST_EVIDENCED` | Methods gate on phase; tests cover refreeze and timeout/crash. This is object-level model behavior, not process recovery behavior. |
| No success before every terminal and modeled exit | `SYNTHETIC_TEST_EVIDENCED` | Terminal cardinality and early-exit tests; zero exit is a supplied model event, not observed job exit. |
| External verification is a separate later state | `SYNTHETIC_TEST_EVIDENCED` | `CAPTURE_WRITTEN`, `JOB_TERMINATED`, `CAPTURE_VERIFIED` are distinct; `passed=True` is a Boolean model input, not an independently verified payload proof. |
| No Solver invocation on any target/non-target/failure FEM path | `DESIGN_ONLY` | Boundary callback is always refused, but not connected to modeled FEM-arrival/control-flow routes; latch is not read there. No ShellSet integration tested. |
| MPI-wide stop, peer failure handling, coordinator loss, timeout enforcement, launcher cleanup | `UNKNOWN / NOT_EVIDENCED` | Static design only. No MPI execution or scheduler/launcher evidence. |
| Owner-backed production run/assignment/model/input/state/build/DOF/A0-b0 provenance | `UNKNOWN / NOT_EVIDENCED` | Authority scope is explicitly synthetic; W3-A gaps remain. |

## Coordination, stale events, and terminal claims

The linear state object rejects duplicate/mismatched ACKs, exact-assignment violations, stale capture/terminal identity fields, duplicate rank terminals, missing terminal ranks before `coordinate_stop()`, partial payload flag, and a terminal status claiming Solver entry. Timeout/crash transitions move to `UNKNOWN`; malformed transitions move to `GLOBAL_FAILURE`; neither has a success transition. A delayed or out-of-order event is rejected by phase checks when passed to the model.

These checks do not model event queues, retries, network duplication, rank process disappearance, coordinator execution, time progression, or independent observation of process exit. `capture()` trusts `payload_complete=True`; `verify_external()` trusts `passed=True`. Those are modeled inputs, not verified artifacts. The phase labels separate capture-written, job-terminated, and capture-verified claims, while the verifier state deliberately remains `SYNTHETIC_PASS` and runtime authority `UNKNOWN`.

## Test evidence and coverage gaps

Named tests exercise decision/digest validation, roster mutability, ACK errors, exact dispatch, target matching, SH/SF constraints, crash/timeout, stale attempt/epoch, missing/duplicate terminals, partial payload, verification failure, callback refusal, latch-clear refusal, and refreeze. Results on this checkout: W3-C **21 passed**; W3-C + W3-B **43 passed**; zero skips/failures in those commands.

Missing adversarial cases include `pure_call_sequence > 1`; Boolean `worker_rank`; state-bound FEM-arrival dispatch; latch removal/corruption at an actual modeled gate; reordered real message delivery; event replay across process restart; and a verifier result tied to concrete payload/sidecar bytes. The two reproductions above are independent of the existing assertions and show current acceptance, not hypothetical risk.

## Next bounded gate

`W3-C-B-R1 — target-coordinate and FEM-boundary invariant correction/review`.

1. Reject inconsistent hierarchical coordinates (`pure_call_sequence != 1`) and non-integer Boolean worker rank.
2. Add one small FEM-boundary transition integrated with modeled target/non-target arrivals and the no-Solver latch; adversarial tests must demonstrate the callback remains at zero because the modeled call routes are blocked, including malformed/lost latch state.
3. Keep payload completion and external verification labeled as assertions unless concrete synthetic artifact digests are verified by the existing decoder/oracle.
4. Re-run W3-C/W3-B and relevant N2 regressions. No MPI, Fair, ShellSet, Solver, DGBSV, SI1, or WORLD_HISTORY.

The current checked-out HEAD's remote ancestry could not be refreshed because GitHub DNS was unavailable. No commit or push is made by this review. All execution/scientific gates remain unchanged, including `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
