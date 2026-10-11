# F2B-N2C-W2 — candidate ShellSet capture integration

## Checkpoint post-review e trasporto Fair (2026-10-11)
- Review Windows: 13 passed, 1 skipped (compilatore Fortran assente), py_compile/UTF-8-LF/whitespace/diff-check PASS riportati dall'operatore; commit `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`, parent `8645a48f7ca716c2e3c4b3cee087e7e6f7333262`, membership quattro file W2.
- GitHub HEAD e Fair detached HEAD `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e` verificati. Fair `arcana-r6-linux`, Python 3.12.14, GNU Fortran 13.3.0, NVFORTRAN 25.11-0; builder CLI `--source-package` opzionale e `--output` obbligatorio. Nessun candidate builder eseguito, nessuna compilazione W2 o run ShellSet.
- Builder: source-lock pinned SHA `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2`, 15 members e parametro verificati nel percorso di creazione candidata. Vendored commit lock = claim, non Git object attestato; correzione `Path.resolve(strict=True)` in controllo lessicale e symlink rejection non dimostra protezione TOCTOU generale.
- Stato `N2C_W2_CANDIDATE_OVERLAY_IMPLEMENTED__RUNTIME_CAPTURE_BLOCKED_BY_IDENTITY_AND_CODEC_BOUNDS`. `CAPTURE_ONLY` con provenance sconosciuta fallisce closed prima di Solver; `DEFAULT_OFF` non autorizza run. Compilazione e runtime bridge/call graph pendenti.
- W1 `n<=2048` / `MAX_STORAGE=2000000` elementi non sono un limite RAM 2 GB; `RESOURCE_2GB_SCOPE_UNRESOLVED`. SI1 `n=128884`, `KL=KU=727`, `LDAB=2182`, 281224888 elementi AB, 2249799104 bytes matrice. Nessuna quota memoria job Fair attestata.


## Result

`N2C_W2_CANDIDATE_OVERLAY_IMPLEMENTED__RUNTIME_CAPTURE_BLOCKED_BY_IDENTITY_AND_CODEC_BOUNDS`

This is an offline candidate-source integration. It does not build or run
ShellSet, execute MPI, capture the SI1 matrix, call DGBSV, or qualify the
operator. The source-locked `external/ShellSet-v1.1.0` tree and its source lock
remain unchanged. The reproducible overlay utility creates a new candidate
copy, checks the pinned source-lock digest and all 15 locked source members,
the separately locked parameter reference, the patch-target hashes, and the
W1 writer before applying only the candidate patch. Its manifest records the
source and post-patch hashes for each locked member; the vendored source commit
is labeled as a claim from the lock, not independently verified as a Git
object. The generated candidate itself is not a qualification artifact.

## Source trace and available identity

The main program calls `MPI_COMM_RANK(...,ThID,...)`. For each worker it
assigns `ModNum`, increments `rpeat`, and calls `Shells_v5p0`. That routine
calls `Pure` with the existing `ThID` and, in the candidate overlay, the
additional `ModNum` and `rpeat`. `Pure` owns `iter` and invokes `FEM` inside
its nonlinear loop. The overlay assigns a monotonic ordinal within each
`Pure` call and passes model number, communicator rank, `rpeat`, `iter`, and
that ordinal to the FEM capture gate. `FEM` then executes `BuildF`, `BuildK`,
`AddFSt`, `VBCs`, and `Solver` in that order. The overlay inserts the gate
between `VBCs` and `Solver`, where `k` and `f(:,1)` are the assembled,
boundary-conditioned candidate A0/b0 buffers.

The code shows that `ThID` is initialized by `MPI_COMM_RANK` at program start;
the candidate therefore propagates the communicator rank value, without
claiming a globally unique process/run identity. `ModNum` is propagated from
the main worker loop. `rpeat` is the existing Shells iteration argument,
`iter` is the `Pure` iteration variable, and the overlay increments a per-
`Pure` FEM-call ordinal immediately before each FEM invocation. The candidate
passes all five local fields through `Pure` and the FEM interface to the
bridge. They identify the
observed call coordinates in this code path, but do not establish run/model
authority or persisted provenance by themselves. No authoritative run ID,
input/state digest, constraint digest, or DOF-order identity is bound to a FEM
call. These remain `UNKNOWN`; labels supplied through the environment would
not establish their authority.

## Candidate gate behavior

The overlay adds a small bridge and a call immediately after VBCs. With
`ARCANA_N2C_CAPTURE_MODE` absent, it calls the W1 writer in `DEFAULT_OFF`; the
writer returns before reading array values or touching a file, and normal
ShellSet control flow continues. Tests do not run this candidate ShellSet
path, and default-off is not test authorization for Solver execution.

If the environment explicitly requests `CAPTURE_ONLY`, the bridge first
checks that the five propagated local fields are positive, then passes an
empty, default-initialized context to W1. W1 rejects it because only
`TEST_ONLY` context is currently supported. No payload path, source digest, or
synthetic identity is fabricated. The FEM gate maps that failure (and any
unexpected non-default status) to `ERROR STOP 86` before the Solver call. An
unknown or truncated mode also fails closed at the same boundary. Thus W2
establishes a candidate pre-Solver stop path, but it cannot produce a runtime
snapshot until an authoritative invocation/context contract and writer
runtime mode are separately implemented and reviewed.

`ERROR STOP` behavior across the MPI job, including peer-rank termination and
scheduler cleanup, has not been compiler/runtime tested. No claim of MPI-wide
abort semantics is made.

## Applicability and limits

W1 currently accepts only `n <= 2048` and band-storage element count at most
`2,000,000`. The recorded SI1 dimensions `n=128884`, `KL=KU=727` imply
`LDAB=2182` and `281,224,888` band-storage elements, exceeding both synthetic
limits. The candidate bridge derives KL/KU from the DGBSV row count and
diagonal index with consistency checks, but W1 rejects these SI1 dimensions.
These are codec/test bounds, not Fair RAM budgets. No arbitrary memory cap was
introduced. A streaming/scale-capable writer, checked allocation behavior,
file-size/I/O policy, and independently verified Fair resource limits remain
open.

The overlay Makefile updates object membership and module dependencies for
normal, debug, and optimized variants. Build ordering and source syntax have
only static checks here. GNU/NVHPC compilation, MPI behavior, real FEM binding,
sidecar generation, payload readback, independent payload SHA-256, durable
publication, and runtime provenance are all pending. The writer still accepts
source digest B as an unauthenticated value; its Python oracle verifier remains
the independent validation boundary for synthetic tests.

## Verification and status separation

- Candidate integration implemented: yes, as an isolated overlay plus
  fail-closed pre-Solver bridge.
- Compiled integration: no, `COMPILE_NOT_TESTED_WINDOWS` (no Fortran compiler
  is available on this Windows PATH).
- Integration tested on synthetic fixtures: structural/source-generation
  tests are run locally; compiler-backed bridge execution remains pending.
- Invocation provenance verified: no; only source-level propagation of
  selected local fields is established.
- SI1 capture qualified: no. W1 bounds reject SI1; identity, resource, and
  integrity gates remain open.

The next concrete closure is to define and bind an authoritative invocation
context from the run/model owner through `Shells_v5p0` to each `FEM`, then extend
the writer under a separately reviewed format/resource contract so SI1-sized
input is not rejected by synthetic fixture bounds. Only after offline
compiler-backed candidate tests should any separate authorization be
considered for a Fair diagnostic run.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
