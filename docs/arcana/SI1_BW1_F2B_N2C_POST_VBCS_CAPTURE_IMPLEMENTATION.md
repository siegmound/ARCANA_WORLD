# F2B-N2C — post-VBCs A0/b0 capture implementation review

## Result

**`BLOCKED_N2C_CAPTURE_IMPLEMENTATION__INVOCATION_AND_HASH_AUTHORITY_MISSING`**

This is a fail-closed implementation review, not a capture result. No code or
test was added: the current candidate hook cannot satisfy the mandatory
invocation-identity and in-process integrity contract without adding
unverified provenance or emitting a snapshot whose required N2A/N2B identity
fields cannot be verified. A hollow hook would overstate what it attests.

No source, source-lock, ledger, input, evidence, or canonical file was changed.
No ShellSet, SI1, compiler, Fair, MPI, Solver, factorization, or assembly was
run. The required scientific and execution gates remain unchanged.

## Baseline and source identity

- Repository branch: `r6/si1-bandwidth-f2av`.
- HEAD: `72fadca38482b4b4a4654f37d3e354b86d81b49e` (the requested baseline).
- Vendored `MOD_Shells.f90` remains byte-identical to the tracked source and
  source lock: Git blob `d036e5d2559738a83c0a42d6922bd457551012c8`, SHA256
  `860b1311e3e2f856b86c7e4f5e988d0591ddf95ff958add1753672dfa9c737f4`.
- `configs/r6_shells_si1/shellset_source_lock.json` was not changed.
- Neither `gfortran` nor `nvfortran` is available on this Windows PATH;
  compile/runtime validation is `COMPILE_NOT_TESTED`.

The worktree already contained unrelated untracked D3D/recovery outputs and a
D3D report at task start. They were preserved and not inspected as N2C inputs.

## Source trace and exact candidate point

In `external/ShellSet-v1.1.0/src/MOD_Shells.f90`, `FEM` begins at line 3630.
Its local `f(mxDOF,1)` and `k(nKRows,nRank)` are the active RHS and band matrix
(declarations at 3696–3701). The routine calls `BuildF` (3707), `BuildK`
(3716), `AddFSt` (3722), `VBCs` (3727), then `Solver` (3732). Thus the
candidate observation point is immediately after the `VBCs` call and before
the `Solver` call. `VBCs` modifies both `f` and `k`; earlier values are not the
system supplied to Solver. `Solver` passes those arrays as `INTENT(INOUT)` to
`DGBSV` (source around 8626–8692), which overwrites the matrix and RHS.

The `SHELLS` routine in `MOD_Shells.f90` invokes `FEM` from its iteration loop
at lines 6924 onward / call at 6996–7010. `SHELLS_v5.0.f90` calls `SHELLS` and
supplies `ThID`. The enclosing `SHELLS` routine has `iter` and `ThID`; `FEM`
currently receives neither as named arguments, and has no invocation ordinal
or state identifier. `ThID` is not proven to be an MPI rank or unique FEM-call
identifier. The visible `iter` could be passed through as one field, but doing
so alone does not identify one run/model/state.

## Contract feasibility findings

| Requirement | Evidence in current code | Status |
|---|---|---|
| Observe final post-BC matrix/RHS | Exact call order in `FEM`; `VBCs` receives and modifies `f,k` | Source point identified; no hook implemented |
| Do not mutate system | A read-only traversal of `k,f` is conceptually possible before `Solver` | Not implemented or tested |
| Default-off and capture-only stop | No existing capture mode/configuration or stop path at this call site | Requires candidate variant and guarded control flow |
| Capture one FEM call/iteration | Caller has `iter`; no call ordinal is passed; repeated FEM calls rebuild system | Incomplete identity |
| Execution/model/rank identity | Only `ThID` is visible at caller; no run/model identity or MPI-rank authority is bound here | `UNKNOWN`; cannot infer from names or `ThID` |
| Input/pre-state/constraint identity | FEM arguments contain arrays and BC data, but no authoritative IDs/digests; no supplied state identity contract is wired in | `UNKNOWN`; labels alone would not bind captured values |
| Source/build and DOF-order identity | External source lock records source blobs, but executable/build and runtime DOF identity are not supplied to `FEM` | Declared source identity does not prove running binary identity |
| N2A/N2B digest B | The N2B interoperability report states its Fortran fixture receives digest B from Python and does not compute SHA-256 | Required source-value digest unavailable in current Fortran path |
| Payload digest A and independent verification | Existing fixture verifies bytes through Python harness; no in-process Fortran SHA implementation or approved linked hash library is present in this source path | Cannot claim complete/verified capture in the Fortran call |
| Portable streaming output | N2B has a fixture wire format, but no production writer, file-collision policy, checked readback, or durability contract | Not implemented |
| Fail before Solver on all errors | `FEM` currently proceeds directly to `Solver`; no capture failure gate exists | Must be implemented and compile/runtime checked in a candidate build |

N2A/N2B format identity is suitable as a target: `ARCNSNP1`, 56-byte
little-endian header, canonical sparse records, raw binary64 bits, full RHS,
positive zero implicit, negative zero explicit, and no band fill/padding.
However, the fixture's Python oracle is not available as an in-process
verifier at the ShellSet call site, and the Fortran fixture explicitly does
not calculate either required SHA-256. Reusing its format does not close that
gap.

## Why no partial hook was installed

A Fortran routine that merely writes bytes then `STOP`s could demonstrate an
intentional stop, but it could not certify the N2A/N2B snapshot identities or
bind the file to the required execution/model/state/source/input identities.
Writing placeholder digests, accepting operator-supplied unverified labels,
or treating successful `CLOSE` as integrity verification would violate the
fail-closed contract. A Python postprocessor after process termination can
verify a payload, but it cannot make missing invocation provenance true after
the fact.

Likewise, directly editing the source-locked vendored file without a
reproducible candidate-source/build identity would blur the sealed F2A-V
identity. The original remains unchanged. Any eventual implementation must be
an explicit candidate variant with its own source/build identity; the existing
source lock must continue to describe the sealed source only.

## Minimum concrete closure needed

Before code can meet this contract, the candidate variant needs an explicit
context passed from the top-level model/run owner into each `FEM` call, with
authoritative values for execution ID, model ID, relevant rank/process,
monotonic FEM-call ordinal, iteration, input-state identity, input/constraint
identity, source/build identity, and DOF ordering. The context must not infer
rank from `ThID` or invent state IDs. The capture implementation also needs a
reviewed SHA-256 implementation or a specifically authorized, identity-bound
hash provider usable at the pre-Solver boundary, plus a bounded streaming
writer/readback protocol for the unchanged N2A/N2B format. These must be
integrated as one candidate variant so `CAPTURE_ONLY` always stops before
`Solver`, including all failures.

Then run only small synthetic Fortran fixtures against that candidate on a
compiler-equipped environment: default-off has no file/control-flow effect;
capture-only writes and independently verifies the fixture then emits the
pre-DGBSV stop marker; missing context, collision, short write, close/readback
failure and digest mismatch all stop before Solver. No SI1 matrix is required
for these tests. Compiler-backed validation remains pending because no
supported compiler is available in this Windows execution environment.

## Preserved gates

`THRESHOLD_UNJUSTIFIED`; `OPERATOR_CLASS_UNVERIFIED`;
`BLOCKED_F2AV_QUALIFICATION`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No ledger update, commit, push, canonical access, or execution authorization
was made.

## W1 bounded standalone capture foundation

**Current workpack result:**
`N2C_W1_CAPTURE_FOUNDATION_IMPLEMENTED__FORTRAN_EXECUTION_PENDING`.

The initial blocked N2C finding above is retained as the historical result
for the proposed ShellSet capture. W1 addresses the concerns in a deliberately
separate scope: it implements a bounded, standalone synthetic writer for the
existing `ARCNSNP1` wire format and an offline Python verifier that compares
the decoded payload with an independent A0/b0 oracle. It does not close the
real invocation identity or runtime-integrity gaps that blocked ShellSet
capture.

### W1 artifacts and behavior

- `src/fortran/r6_sparse_snapshot_writer.f90`: standalone general-band writer
  with variable `n`, `KL`, and `KU`, bounded at `n <= 2048` and at most
  2,000,000 band-storage entries, matching the existing N2A bounded codec
  contract; these are format/workload bounds, not estimates or guarantees of
  RAM availability. It traverses only band entries in its count/write passes,
  reads the original DGBSV storage directly, and does not allocate a second
  matrix or accept noncontiguous arrays that could require hidden copy-in
  temporaries. It emits the N2A/N2B
  56-byte `ARCNSNP1` header, canonical row-major sparse records, and full RHS
  in explicit little-endian bytes. Positive zero matrix coefficients are
  implicit; negative zero and every other nonzero finite binary64 bit pattern
  are explicit; the RHS is fully recorded.
- `capture_config` and `capture_context` define explicit mode and invocation
  context fields. W1 accepts only context marked `TEST_ONLY` with all required
  fields populated. This is synthetic fixture validation, not an authoritative
  runtime identity.
- `DEFAULT_OFF` returns before reading arrays or examining/creating a path.
  `CAPTURE_ONLY` writes only to a caller-supplied new `.tmp` path and returns
  `CAPTURE_ONLY_STOP_REQUIRED`. `CAPTURE_FAILED` reports rejected input or
  I/O/serialization failure. There is no solve-capable mode or DGBSV call.
  The fixture harness treats all three defined statuses as a terminal gate;
  no production ShellSet caller has been integrated or tested.
- The writer accepts the source-value digest B from its harness but does not
  authenticate it or compute SHA-256. The Python verifier independently
  decodes the payload, checks an externally supplied payload digest, computes
  canonical A0/b0 identity from the independent oracle, and compares all
  coefficient/RHS bits. A digest supplied by the writer alone is not proof.

### Validation performed

The Windows Python suite for the new W1 tests returned **4 passed, 1 skipped**.
The skipped test is the compiler-backed Fortran execution because neither
`gfortran` nor `nvfortran` is available in this environment; status:
`COMPILE_NOT_TESTED_WINDOWS`. Static tests cover source line-length limits,
the no-allocation/no-solver structure, default-off/capture-only/failure gate
shape, Python oracle checking, and fixture cases including variable bands,
incomplete shape, nonfinite input, context rejection, collision, and a missing
parent directory representing an I/O failure. The latter compiled-path cases
remain unexecuted until a supported compiler runs the fixture. No mock is
reported as a Fortran execution pass.

### Authority and durability limits still open

The in-memory context is not serialized into the N2A/N2B payload, and the
writer has not bound its fields to ShellSet `ThID`, `ModNum`, rank, `rpeat`,
FEM iteration/call identity, source/build identity, input identity, or DOF
ordering. Those runtime bindings remain unimplemented. The writer also does
not calculate a payload SHA, reopen/read back its output, or establish atomic
publication or durable storage. A successful `FLUSH` and `CLOSE` only produce
a candidate temporary payload; the independent Python verifier must check
the payload and oracle after the diagnostic process terminates. Partial files
may remain with `.tmp` names and are non-authoritative. No SI1 capture, ShellSet
integration, Fair execution, Solver entry, or canonical action occurred.

The next technical phase remains N2C-W2: a separately reviewed development
overlay that binds this writer to the post-VBCs/pre-Solver point, supplies
authoritative invocation context, and gates every outcome before Solver.
W1 completion does not authorize W2 execution on Fair or a real SI1 run.

## Gates preserved after W1

`THRESHOLD_UNJUSTIFIED`; `OPERATOR_CLASS_UNVERIFIED`;
`BLOCKED_F2AV_QUALIFICATION`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
