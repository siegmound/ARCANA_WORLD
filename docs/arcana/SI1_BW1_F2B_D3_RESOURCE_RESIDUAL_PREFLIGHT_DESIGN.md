# SI1/BW1 F2B-D3 — resource and residual preflight design

## Decision

**D3_DESIGN_COMPLETE_PENDING_RESOURCE_AND_NUMERICAL_ATTESTATION**

This is an engineering design only. It does not authorize Fair execution, MPI, Solver, factorization, assembly, mechanics, gauge, or canonical evolution. F2A-V remains `BLOCKED_F2AV_QUALIFICATION`; F2B-D2 remains `OPERATOR_CLASS_UNVERIFIED`; no symmetry or positive-definiteness assumption is made. No Solver, factorization, or new assembly was run while preparing this report.

The historical source basis is ShellSet commit `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`, principally `SHELLS_v5.0.f90` and `MOD_Shells.f90`. The SI1 engineering case is explicitly noncanonical and its ShellSet parameter file is an engineering solver reference, not ARCANA geology or physical authority.

## Inputs and fixed dimensions

The case contract records 64,442 nodes, 128,880 triangles, zero fault elements, one model, two MPI ranks, zero velocity-BC records, `trHMax=0`, `iConve=0`, and no gauge in the initial run. F2A-V recovery records the band values `nRank=128884`, `kl=ku=727`, `nKRows=2182`, `iDiagonal=1455`, with one RHS. These dimensions are evidence for the stopped-before-Solver assembly diagnostic, not a Solver qualification.

From `KSize` the storage formula is:

- `nRank = 2 * 64,442 = 128,884`;
- `nCodiagonals = max(2*nLB+1, 2*nUB+1) = 727` for the recorded BW1 ordering;
- `nKRows = 3*nCodiagonals + 1 = 2,182`;
- allocated REAL*8 entries = `nKRows * nRank = 281,224,888`;
- matrix bytes = `8 * 281,224,888 = 2,249,799,104` bytes = 2.09529 GiB (2.24980 decimal GB).

The recovered diagnostic reports 186,996,964 valid band positions. LAPACK general-band LU reserves the first `kl=727` rows in each column for pivot-generated fill; the original band occupies the remaining `kl+ku+1=1,455` rows. The extra fill capacity is already inside the 2,182-row `stiff` array, not a second matrix allocation.

## Allocation and lifetime reconstruction

`SHELLS_v5.0.f90` sets `mxNode=numNod`, `mxDOF=2*mxNode`, `mxBn=numNod`, `mxEl=numEl`, `mxFEl=nFl`, `mxStar=20`, and `nPBnd=1250` (326–365). It allocates node, DOF, boundary, element, fault, region, plate, and matrix arrays (381–453, 671). The runtime package is loaded before these allocations; `runtime_nodes` is then saved in `MOD_ArcanaRuntime` for the worker model lifecycle (runtime source 52–56, 79–89).

At the model call, the one main `stiff` allocation is passed as `k` through `Pure` and `FEM` into `Solver`: main 735–759; `Pure` dummy/work declaration and dimensions 6738–6762, 6801, 6836; `FEM` dimensions and call to Solver 3630–3701, 3732–3734. These are argument aliases, not separate matrix allocations. `FEM` calls BuildF, BuildK, AddFSt, and VBCs in sequence (3707–3730). The matrix remains allocated until main deallocates `stiff` at 818. Solver's `ab` dummy aliases this same matrix and is overwritten by DGBSV.

### Explicit source-visible storage estimate for the SI1 model worker

The following subtotal counts the explicit arrays allocated in the main ShellSet worker and the ARCANA runtime node table. It assumes 8-byte REAL*8/DOUBLE PRECISION, 4-byte default INTEGER and LOGICAL, and one byte per default CHARACTER. The REAL array and matrix terms are dimensioned directly by source. The non-real ABI sizes must be confirmed against the exact Fair executable/compiler flags before using this as a hard limit. Region/LR arrays are expressed parametrically because their allocated extent is `LRn+1`.

| Array family | Source dimensions in this case | Byte formula / estimate |
|---|---:|---:|
| `stiff` general-band matrix | 2,182 × 128,884 | 2,249,799,104 |
| `alpha`, `dXS`, `dYS`, `fPSfer`, other element REAL arrays | 603 REAL*8 values per element × 128,880 | 621,717,120 |
| Node REAL arrays (`atNode`, `dQdTdA`, `elev`, thermal/density and velocity arrays) | 20 REAL*8 values per node × 64,442 | 10,310,720 |
| Node connectivity/flags | 3 INTEGER + 1 LOGICAL per node | 1,031,072 under stated ABI |
| DOF arrays (`comp`, `fBase`, `force`, `ipiv`) | 8 REAL*8 + 1 INTEGER per rank × 128,884 | 8,764,112 |
| Boundary arrays | 5 REAL*8 + 3 INTEGER + two-character tag per node | 3,479,868 under stated ABI |
| Element identifiers/flags | 4 INTEGER + 18 LOGICAL per element | 11,341,440 under stated ABI |
| Plate arrays | `pLat`, `pLon`: 12 × 1,250 REAL*8; `nDPlat`: 12 INTEGER | 240,048 under stated ABI |
| `list` | 20 INTEGER | 80 under stated ABI |
| ARCANA runtime records | 64,442 × 51 REAL(KIND=8) | 26,292,336 |
| Region/LR parameters | 13 REAL*8 + 2 LOGICAL per `0:LRn` | `112 * (LRn+1)` under stated ABI |

The fixed subtotal above, including the matrix, is **2,932,975,900 bytes + 112*(LRn+1) bytes**, or **2.73155 GiB + 112*(LRn+1)/2^30 GiB**, under the stated ABI assumptions. It excludes small fixed-shape arrays, allocation descriptors, stack frames, compiler-generated temporaries, MPI/runtime/library state, allocator overhead, and OS accounting. This is an explicit-array estimate, not measured RSS or a complete process upper bound. Fault arrays have zero element extent for `mxFEl=0`; their descriptors/allocator overhead are not treated as exactly zero.

### Peak, per-process, and aggregate interpretation

- **Code-visible solver-worker lower bound:** one `stiff` matrix, RHS, pivots, main arrays, and runtime records coexist at the solve call. The matrix alone is 2.09529 GiB; the explicit source-visible subtotal is about 2.73155 GiB plus LR-dependent storage under the stated ABI.
- **Snapshot scenario:** preserving an independent A0 band copy adds another 2,249,799,104 bytes; preserving b0 adds 1,031,072 bytes. The corresponding explicit subtotal becomes about **4.82684 GiB + LR-dependent storage**, before library/OS/temp overhead. This is a scenario estimate, not a proposed allocation or enforced cap.
- **F2A-V MPI layout:** the run record says two ranks. Historical `ShellSetMain.f90` uses rank 0 as the Boss/scheduler and dispatches model IDs to ranks 1 through `np-1` (212–260); model execution is on worker ranks (worker flow around 624–676). For `np=2` and one model this identifies one model worker, not two model matrices. Rank 0 still consumes scheduler/runtime memory, which was not measured. This source-path observation does not establish Fair's total job RSS or shared-library accounting.
- **Aggregate memory:** do not multiply the worker subtotal by rank count. A future run must measure the actual rank/process set and job cgroup. Report per-PID RSS and PSS plus job/cgroup memory; RSS summation can double-count shared pages, whereas cgroup usage is the enforcement-domain total.
- **Maximum theoretical memory:** the finite source-visible array inventory above is calculable, but a defensible total upper bound is not available statically because compiler temporaries, stack placement, MPI/NVHPC/LAPACK internals, allocator behavior, libraries, and Fair job limits are not sealed by this evidence. No RSS peak was recorded for a Solver attempt. The 282.092 s F2A-V elapsed time ended at the deliberate pre-Solver stop and is not a solver-runtime estimate.

`PrintK` declares a band-sized local `k` array (MOD_Shells 6644–6645), but the historical source has no `CALL PrintK` call site. Do not add it to the SI1 active-path peak. Any future debug/diagnostic build that makes that routine reachable could introduce another 2,249,799,104-byte explicit array and must be re-audited.

## DGBSV semantics and preserved inputs

ShellSet calls `dgbsv(n,kl,ku,nrhs,ab,ldab,ipiv,b,ldb,info)` with `n=128884`, `kl=ku=727`, `nrhs=1`, `ldab=2182`, `ldb=128884` (`MOD_Shells.f90:8626–8692`). The official Netlib DGBSV contract states `LDAB >= 2*KL+KU+1`; on entry A occupies rows `KL+1` through `2*KL+KU+1`, and the first `KL` rows are reserved for fill. On exit AB contains LU factors and multipliers, IPIV records row pivots, and B is overwritten by X when `INFO=0` ([Netlib DGBSV documentation](https://www.netlib.org/lapack/explore-html/db/df8/group__gbsv_gaff55317eb3aed2278a85919a488fec07.html)). Thus this path destroys the original band coefficients and RHS unless separate snapshots or reproducible reconstruction are provided.

For this case `2*kl+ku+1 = 2*727+727+1 = 2,182`, agreeing with `nKRows=3*727+1`. This is the general band LU path with pivoting. It is not a symmetric-band solver and does not imply the operator is symmetric. D2's `OPERATOR_CLASS_UNVERIFIED` remains in force.

`INFO < 0` reports an illegal argument; `INFO > 0` reports an exactly zero diagonal U pivot and a singular factorization in the LAPACK contract. `INFO=0` only reports successful routine completion; it is not a condition estimate, residual, backward-error bound, or physical validation. Near-singularity/conditioning needs distinct evidence. No gauge is inferred or added here.

Before a future call, preserve or make reproducible:

1. the exact A0 band coefficient data and band-layout metadata used at Solver entry;
2. the exact b0 RHS before the call;
3. an identity for source, executable, FEG, runtime package, parameter inputs, ordering, and operator state;
4. the returned x and IPIV/INFO plus the complete diagnostic log.

IPIV is not a substitute for A0, and the factored AB cannot serve as the original matrix for residual evaluation.

## Residual and error validation design

Let `r = b0 - A0*x`. Compute and report at least:

- **Absolute residual:** `||r||_infinity = max_i |b0_i - sum_j A0_ij*x_j|`.
- **Normwise backward error:** `eta_inf = ||r||_infinity / (||A0||_infinity*||x||_infinity + ||b0||_infinity)`.
- **Componentwise backward error (preferred additional diagnostic):** `eta_c = max_i |r_i| / (sum_j |A0_ij|*|x_j| + |b0_i|)`.
- Output finiteness for every x and every residual/error accumulator; report INFO and pivot/failure details independently of residual metrics.

No numerical acceptance threshold is established by D2, the engineering-case reproducibility tolerance, or LAPACK DGBSV. The residual and backward-error cutoffs are therefore **THRESHOLD_UNJUSTIFIED** until an explicit numerical contract justifies them. An observed residual must not be converted into a pass by selecting a tolerance after seeing the result.

### Zero denominators and extreme scales

- If a normwise denominator is zero and the numerator is zero, report the defined zero-over-zero convention explicitly as `0` only if the future contract adopts that convention; if numerator is nonzero, report `+Inf`/failure. Do not silently return zero.
- For componentwise rows, a zero denominator with zero residual contributes zero only under a declared convention; nonzero residual over zero denominator is infinite and fails closed.
- NaN or infinity in x, A0, b0, r, norms, or errors fails validation; never allow IEEE NaN comparison behavior to bypass a threshold.
- Avoid overflow in `||A||*||x||`, row sums, and componentwise denominators with scaled norms/sums or exponent-aware ratios. Record underflow/overflow flags separately; do not use a computed infinity caused by overflow as the mathematical denominator.
- Compute residual with a declared accumulation method. A stable/compensated accumulation may be reported as an independent diagnostic, but must not replace the source operator or silently change ShellSet coefficients.

### Candidate A0/b0 provenance strategies

| Strategy | Added memory | Validation value | Limitation / gate |
|---|---:|---|---|
| Preserve band A0 and b0 before DGBSV | +2,249,799,104 bytes plus about 1,031,072 bytes | Direct residual against the exact pre-factorization bytes; straightforward identity | Requires resource headroom above the 4.82684 GiB explicit-array scenario, plus measured process/system overhead. No cap available yet. |
| Reconstruct A0 and b0 after solve | Can reuse overwritten band storage; no second simultaneous band copy if lifecycle is designed carefully | Hash pre-solve A0/b0, deterministically rebuild, verify matching identities, then compute residual | Reassembly reproducibility does not establish independent correctness; evolving state, accumulation order, and complete recipe must be pinned. Reassembly is not authorized by this design. |
| Independent matrix-vector action for A0*x | O(nRank) work vectors, rather than another band matrix | Avoids matrix copy and supplies a separately coded residual action | Must prove it uses the identical operator/state and all element/fault/constraint contributions. A second implementation can share a bug or diverge; D2 currently lacks pointwise tangent capture and anomaly attribution. |

The eventual contract should select and justify a strategy before any Solver authorization. At minimum, pre-solve fingerprints must bind A0/b0 construction inputs and operator state to the residual action. Hash equality alone proves byte identity of inputs, not scientific correctness of the operator.

## Fail-closed preallocation and execution gate

No future preflight passes from operator-declared limits alone. It must capture the following immediately before execution and again at the Solver gate:

1. **Exact source/input identity:** qualified ShellSet commit and clean/source-lock state; executable SHA; FEG/runtime/partition/reference-input SHA256; permutation and band dimensions; parameter roster and runtime mode. Any mismatch or unknown identity blocks.
2. **Per-process limits:** actual worker count, CPU affinity, address-space/data limits, process limits, and memory cgroup membership/limit. Record effective values from the running process/kernel (for example process limits plus cgroup v2 `memory.max` and `memory.current`, where present), not only command-line claims.
3. **Job-wide capacity:** scheduler allocation and enforced memory/time limits, cgroup/job memory current and maximum, node available memory, and competing job constraints. Unknown scheduler/cgroup enforcement or inadequate measured headroom blocks.
4. **Budget comparison:** compare the source-visible allocation estimate, chosen A0 preservation strategy, stack/compiler/library allowance, MPI/runtime overhead, and a justified safety margin against both enforced per-process and job limits. The safety margin itself requires an explicit authority; absent that, `RESOURCE_HEADROOM_UNJUSTIFIED`.
5. **Solver invocation bound:** instrument/guard a maximum of one DGBSV call for a preflight attempt; reject retries or nonlinear iterations unless separately scoped. The current source has iterative Pure calls and `maxItr` configuration, so the gate must establish how a single-call limit is enforced at the call site rather than infer it from the one-model launcher.
6. **Wall-clock bound:** require a declared maximum duration and an actually enforced scheduler/job timeout or process supervisor timeout. No duration is selected here. Missing declared or enforced limit blocks.
7. **Output isolation:** create a new external evidence run directory, verify it is empty and disjoint from source-locked inputs and canonical WORLD_HISTORY, write only diagnostic outputs, and seal a manifest. Never stage outputs over governed source/runtime/FEG or canonical stores.
8. **Failure behavior:** any mismatch, allocation failure, limit ambiguity, nonfinite diagnostic, DGBSV nonzero INFO, timeout, MPI failure, or output write failure terminates the attempt; preserve logs and partial evidence as blocked, never publish to canonical state or retry under changed parameters silently.

Distinguish an operator-declared requested limit from an enforced limit: configuration text is intent; kernel/cgroup/scheduler evidence is enforcement. Fair resource limits, actual memory availability, and RSS were not inspected in this audit.

## Requirement matrix

| Requirement | Source | Formula | Budget | Evidence | UNKNOWN | Failure gate |
|---|---|---|---|---|---|---|
| Band matrix allocation | SHELLS_v5.0.f90:664–672; MOD_Shells.f90:5360–5368 | `8*nKRows*nRank` = 2,249,799,104 B | One explicit matrix per active worker | SI1 dimensions in engineering case and recovered F2A-V diagnostics | NVHPC heap/RSS overhead and enforced memory cap | Any dimension/byte overflow, cap not enforced, or inadequate headroom |
| Pivot fill space | MOD_Shells.f90:5367–5377, 8664–8672; Netlib DGBSV contract | `ldab=2*kl+ku+1=2182`; fill workspace is first `kl=727` rows | Already inside matrix allocation | Source formulas and DGBSV contract agree | Actual linked LAPACK ABI/version should be recorded | LDAB/layout disagreement or wrong backend contract |
| Main worker arrays | SHELLS_v5.0.f90:381–453, 671 | Explicit shapes; subtotal table above | 2,932,975,900 B plus `112*(LRn+1)` under stated ABI, incl. band matrix and ARCANA runtime | Source declarations and SI1 dimensions | Exact LRn, compiler integer/logical sizes, temporaries, allocator overhead | ABI/extent mismatch or unbudgeted duplicate array |
| Array lifetime / copies | SHELLS_v5.0.f90:671, 735–759, 818; MOD_Shells.f90:6738–6762, 6996–7010, 3630–3734 | Main matrix remains live through Solver; dummy arguments alias it | No second matrix in active path; snapshot strategy adds 2,249,799,104 B | Source call chain; no PrintK call site | Compiler copy-in/out and stack behavior | Evidence of implicit copy or active debug matrix invalidates estimate |
| MPI/rank total | ShellSetMain.f90:88–90, 212–260; engineering case | Sum measured process/job usage, not ranks × matrix | One worker for one model at np=2, plus Boss and MPI overhead | Source dispatch sends model to ranks 1..np-1 | Fair RSS/PSS/cgroup total and scheduler enforcement | Any rank count/model scheduling mismatch or aggregate cap breach |
| DGBSV input/output retention | MOD_Shells.f90:8630–8672; Netlib DGBSV | AB and B are overwritten; IPIV is O(n) | Exact A0/b0 strategy must be budgeted | Source and LAPACK contract | No original A0/b0 snapshot in F2A-V | Cannot bind residual to exact pre-solve A0/b0 |
| Residual correctness | Future residual contract | `r=b0-A0*x`; normwise/componentwise formulas above | O(nnz-band) action; copy/rebuild strategy-specific | No Solver x/residual exists | Numerical acceptance threshold | `THRESHOLD_UNJUSTIFIED`, nonfinite, or input identity mismatch |
| Conditioning/singularity | Solver INFO plus future condition evidence | INFO and condition estimates are separate | No budget/acceptance rule yet | D2 and DGBSV call semantics | Conditioning and nullspace unknown | INFO failure, unbounded risk, or no separately authorized criterion |
| Per-process/job resource gate | Fair scheduler/kernel/cgroup, future preflight | Compare measured/enforced limits to explicit allocation + margin | No Fair values established | None collected here | Effective enforcement and headroom | Operator declaration without enforcement evidence; unknown limit |
| Invocation/time/output gate | Future runner/job wrapper | Solver-call counter ≤ 1; enforced wall timeout; isolated output | Duration and quota unselected | Engineering case requires per-process address-space and wall-clock limit | Exact imposed duration/output cap | Missing enforcement, repeat call, output overlap, or partial publication |

## Checks that can proceed without Solver

The following are safe next checks, subject to separate task scope, and do not need a new assembly:

- Offline source-only arithmetic review of all source allocation extents, default-kind flags, and the DGBSV ABI/version linked by the existing Fair executable metadata.
- Read-only verification of exact F2A-V source/input hashes, ShellSet source lock, band dimensions, and the residual design's required provenance fields.
- Read-only Fair node/job resource inventory in a non-solving shell: scheduler allocation, `/proc` process limits, cgroup memory limits/current usage, physical available memory, filesystem quota, and timeout enforcement mechanism. Record rank/PID mapping; do not launch ShellSet.
- A tiny synthetic unit-level arithmetic test of overflow-safe allocation formulas and residual denominator edge-case policy, using no production inputs and no scientific solver. This audit did not implement or run such tests.
- Static review of whether one-call guard, output isolation, and fatal cleanup can be enforced by a future runner without modifying canonical state.

These checks can establish resource enforcement and contract readiness, not numerical behavior of a future x. A future Solver attempt remains a distinct authorization gate.

## Preserved gates and next decision

- `OPERATOR_CLASS_UNVERIFIED` unchanged; no symmetry assumption.
- F2A-V original remains `BLOCKED_F2AV_QUALIFICATION`.
- `F2B_SOLVER_EXECUTION_AUTHORIZED=false`.
- No gauge, mechanics, forward evolution, canonical WORLD_HISTORY access/mutation, or scientific promotion.
- D3 decision: `D3_DESIGN_COMPLETE_PENDING_RESOURCE_AND_NUMERICAL_ATTESTATION`.
- Remaining attestation: Fair enforced memory/time/job limits and measured process/job memory; exact linked LAPACK/runtime identity; justified residual/error acceptance thresholds; explicit A0/b0 preservation or reconstruction strategy; no-solver verification of the preflight controls.
