# SI1/BW1 F2B-D3A — Resource and Numerical Attestability Audit

## Decision

**D3A_AUDIT_COMPLETE__SOLVER_PREFLIGHT_NOT_ATTESTABLE_FROM_CURRENT_EVIDENCE**

This is an offline source/evidence audit. It establishes source-derived dimensions, the arithmetic for named arrays under explicit ABI assumptions, the DGBSV overwrite contract, and a residual-validation design. It does **not** establish Fair resource headroom, process/job memory enforcement, actual peak RSS, a successful solve, numerical acceptance thresholds, operator class, nullspace, or gauge. No Fair, MPI, Solver, factorization, assembly, gauge, simulation, or WORLD_HISTORY operation was run.

The qualified engineering case is not a scientific mechanics qualification. Preserve `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Audit baseline and provenance

- Branch: `r6/si1-bandwidth-f2av`; checkout HEAD: `9adb986f510d81d220ab39b69a2df71704aac606`.
- The F2B-D3 report was byte-hash checked against its ledger identity: `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF`.
- The SI1 case is `configs/r6_shells_si1/engineering_case.json`: it records 64,442 nodes, 128,880 triangles, zero fault elements, one model and two MPI ranks; the operator memory cap and runtime limit are requirements from the operator, not observed or enforced values (case fields `mpi_ranks`, `models`, and resource-preflight entries).
- Historical F2A-V ARCANA execution/source commit: `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`. The vendored source lock separately identifies ShellSet source commit `9fef54f6cd17e6e756db3ec28bfc43ee0230fc27` and hashes the source artifacts. All 15 source-lock hashes were checked against the current vendored source files. The relevant `SHELLS_v5.0.f90`, `MOD_Shells.f90`, `ShellSetMain.f90`, and `MOD_ArcanaRuntime.f90` contents match the corresponding paths at the historical execution commit. Thus `df670…` identifies the ARCANA run snapshot; it should not be described as the vendored ShellSet commit.
- Existing untracked D1A and F2A-V evidence directories were left untouched.

## A. Static resource attestation

### Dimensions and band storage

`SHELLS_v5.0.f90:326–365` derives the principal capacities from the FEG: `mxNode=numNod`, `mxDOF=2*mxNode`, `mxBn=numNod`, `mxEl=numEl`, and `mxFEl=nFl`; it sets `mxStar=20`, `nPBnd=1250`, and derives `LRn` by scanning element LR codes. The F2A-V stopped-before-Solver record supplies the realized band dimensions: `nRank=128884`, `kl=ku=nCodiagonals=727`, `nKRows=2182`, `iDiagonal=1455`, one RHS.

`MOD_Shells.f90:5311–5338` computes node connectivity extrema from every triangle and fault; with `nFl=0` the fault loop contributes nothing. `:5362–5368` doubles node bandwidth for two DOFs and sets `nKRows=3*nCodiagonals+1`. Storage is `stiff(row,column)` with row `iDiagonal + i - j` (`:5293–5295`). The independently evaluated matrix allocation is:

```text
nRank = 2 × 64,442 = 128,884
nKRows = 2,182
elements = 2,182 × 128,884 = 281,224,888 REAL*8
bytes = 8 × elements = 2,249,799,104 bytes
       = 2.095288694 GiB (2^30 bytes/GiB)
```

The reported value `nKRows=3×727+1=2182` agrees. DGBSV requires `2*kl+ku+1` rows; `MOD_Shells.f90:8664–8673` passes exactly `n=128884`, `kl=ku=727`, `ldab=2182`, and one RHS. Its leading `kl` rows are reserved for pivot fill and are already inside `stiff`, not a second matrix.

### Source-visible active arrays and lifetime

The following table inventories the main `Shells_v5p0` allocations at `SHELLS_v5.0.f90:381–453,671,818`, plus the ARCANA runtime table. Bytes assume 8-byte REAL*8, 4-byte default INTEGER and LOGICAL, one-byte default CHARACTER, and no allocator/descriptor overhead. The `mxEl` real count is 603 values/element; node real count is 20/node; element IDs/flags are 4 integers + 18 logicals/element. Region/LR arrays use `LRn+1` entries.

| Active array family | Extent at SI1 | Explicit bytes | Allocation / release / overlap notes |
|---|---:|---:|---|
| `stiff` | `2182 × 128884` REAL*8 | 2,249,799,104 | Allocated after KSize at line 671; passed through `Pure`/`FEM`/`Solver` as the same storage (`:735–759`, `MOD_Shells:3630–3734`, `:8626–8673`); remains live until line 818; overwritten by DGBSV. |
| Element REAL arrays (`alpha`, `area`, `curviness`, `delta_rho`, `detJ`, `dXS`, `dYS`, `dXSP`, `dYSP`, `edgeTS`, `eRate`, `eta`, `fPSfer`, `geothC`, `geothM`, `glue`, `oVB`, `outVec`, stress/temperature/geometry arrays, etc.) | 603 REAL*8 × 128880 | 621,717,120 | Allocated together at lines 408–423; live through computation; not all entries necessarily populated/used in this SI1 branch, but their declared allocation extents are explicit. |
| Node REAL arrays (`atNode`, `basal`, `cooling_curvature`, `density_anomaly`, `dQdTdA`, `dv`, `dVLast`, `elev`, `tauZZN`, `tLNode`, `v`, `vM`, `xNode`, `yNode`, `zMNode`) | 20 REAL*8 × 64442 | 10,310,720 | Allocated at lines 381–392; coexist with runtime and matrix. |
| Node indices/flags (`jCol1`, `jCol2`, `whichP`, `checkN`) | 3 INTEGER + 1 LOGICAL × 64442 | 1,031,072 | Same allocation block. |
| DOF arrays (`comp`, `fBase`, `force`, `ipiv`) | 8 REAL*8 + 1 INTEGER × 128884 | 8,764,112 | Lines 395–396; live across the solve; `force` is the RHS storage and is overwritten with solution. |
| Boundary arrays (`r2Edge`, `vBCArg`, `vBCMag`, `xEdge`, `yEdge`; `iCond`, `iEdge`, `nodCon`; `savTag`) | 5 REAL*8 + 3 INTEGER + 2-character × 64442 | 3,479,868 | Lines 401–405; explicit size uses ABI assumptions. |
| Element identifiers/flags (`nodes`, `continuum_LRi`, `checkE`, `contin`, `edgeTS`, `pulled`) | 4 INTEGER + 18 LOGICAL × 128880 | 11,341,440 | These are already included in the element family above only if counting the real arrays separately; this row is the non-real portion. |
| Fault arrays | extent proportional to `mxFEl=nFl=0` | 0 payload bytes | Allocated at lines 426–431 with zero extent. Descriptor/allocator bookkeeping is not zero by assertion. |
| `list` | 20 INTEGER | 80 | Line 434. |
| Plate arrays (`pLat`, `pLon`, `nDPlat`) | 2 × 12 × 1250 REAL*8 + 12 INTEGER | 240,048 | Lines 437–438. |
| Region/LR arrays | 13 REAL*8 + 2 LOGICAL per `LRn+1` | `112 × (LRn+1)` | Lines 441–453 continue beyond this range; LRn value is case/input-derived and no exact value was independently extracted here. |
| ARCANA `runtime_nodes` | 64442 × 51 REAL(KIND=8) | 26,292,336 | Module type has 51 values (`MOD_ArcanaRuntime.f90:52–56`); allocated during runtime load at `:79–89`; no deallocation is shown in the excerpted main lifecycle before solver, so overlap with ShellSet arrays is conservatively counted. Release routine exists at `:179–181`. |

The region/LR term and matrix-inclusive fixed subtotal independently sum to:

```text
2,932,975,900 bytes + 112 × (LRn+1) bytes
= 2.731546666 GiB + 112 × (LRn+1) / 2^30 GiB
```

This reproduces D3’s `2.73155 GiB + 112*(LRn+1)` estimate under its ABI assumptions. The main-source split above avoids double-counting non-real element/node/DOF portions.

**Correction to the D3 A0/b0-copy variant:** adding an A0 copy of `stiff` and a b0 copy of `force` adds `2,249,799,104 + 1,031,072` bytes. Therefore the corrected estimate is:

```text
5,183,806,076 bytes + 112 × (LRn+1) bytes
= 4.827795621 GiB + 112 × (LRn+1) / 2^30 GiB
```

The D3 value `4.82684 GiB` is low by about 1.03 MiB because it omitted the copied RHS from the arithmetic. This audit does not edit D3 or claim that the copy strategy is selected.

### Other active local arrays, compiler/runtime overhead, and maximum

- `Assign` allocates `plate_outline_uvecs(3,nPBnd)` (`MOD_Shells.f90:293–303`): at `nPBnd=1250`, 30,000 REAL*8 = 240,000 bytes. It is a local allocatable and does not overlap the later Solver call if normal subroutine return deallocates its local allocatable as required by the implementation/language lifecycle; it does overlap the long-lived main arrays/runtime.
- `GetPBx`’s relevant outline-reading path declares and allocates `other_counts(nPlate-1)`, `iOtherPlate(nPlate-1)`, and conditionally `other_shapes(n_others,2,max_count)` (`MOD_Shells.f90:1620–1629,1904–1938`). Exact shape sizes depend on plate-outline file contents. These allocations occur before `stiff` allocation at main `:577–578` versus `:671`, so they are not concurrent with the matrix allocation; they are nevertheless active source-visible memory and not represented in the core subtotal.
- `Tract` allocates `tpvecs(3,nPlate)` and `tpread(nPlate)` and releases them before return (`MOD_Shells.f90:9700–9705,9797–9801`), but the relevant call is gated to `iConve==6`; SI1 sets `iConve=0`, so this allocation is inactive. Static local fixed-shape arrays/scalars and procedure workspaces also exist.
- `PrintK` contains a local band-sized matrix declaration (`MOD_Shells.f90:6644–6645`) but has no call site in the active SI1 source path; exclude it from the active peak unless a future build makes it reachable.
- Source cannot establish exact default INTEGER/LOGICAL ABI widths, compiler stack placement/temporaries, Fortran allocation descriptors, allocator fragmentation, MPI/NVHPC runtime/library allocations, LAPACK workspace internals, OS page accounting, or Fair cgroup behavior. Therefore the explicit subtotal is neither a complete upper bound nor measured RSS.

### MPI dispatch and resource evidence

`ShellSetMain.f90:88–90` initializes MPI and gets rank/size. In List mode rank 0 reads one model row (`:137–149`, `:143–144`); with `np=2`, its dispatch loop sends model 1 to rank 1 (`:244–259`). Rank 0 is the Boss/scheduler (`:211–212`); worker ranks receive one model row (`:567–570`) and call the ShellSet model path (`:694–700`). Thus source control flow has one model-solving worker and does not dispatch a second copy of the SI1 matrix to rank 0. Rank 0 still has scheduler, input, result, and MPI allocations; there is no evidence that all its allocations are zero. No two-rank Fair memory measurement exists here.

The case’s `memory_cap_required_from_operator=true` and `runtime_limit_required_from_operator=true` (`engineering_case.json` resource section) only require the operator to provide limits. Offline checks can validate those declarations, command/config identity, source lock, and arithmetic. They cannot attest the current Fair node memory, cgroup/job limit, per-process RLIMIT, scheduler-enforced walltime, rank placement, available headroom, or actual RSS/PSS. These require a separately authorized, non-Solver Fair environment attestation and later bounded measurements. The F2A-V run stopped intentionally before Solver; its elapsed time is not Solver runtime or RSS evidence.

## B. Numerical contract and attestability

### Original-system identity

The solve changes both operands: `MOD_Shells.f90:8635–8636,8672` says the coefficient matrix is destroyed and the solution overwrites the forcing vector. `INFO=0` means routine completion, not residual adequacy, conditioning, or physical validity; `INFO>0` reports a zero U pivot under the LAPACK contract. Before a future authorized solve, a residual must be evaluated against the exact `A0` and `b0` entering that exact call, with matching DOF ordering, constraints, band layout, source/executable, FEG/runtime/configuration identity. A factored `AB`, `IPIV`, or post-solve RHS alone cannot reconstruct the original system.

Three possible evidence strategies remain:

1. **Copy `A0` and `b0` before DGBSV.** Direct and auditable, but adds the corrected `2,250,830,176 + 112*(LRn+1)` bytes to the stated core arrays (one A copy plus RHS copy). Not authorized or measured.
2. **Independent deterministic reconstruction.** Lowest retained-memory approach if it is demonstrably the same operator; requires an independent assembly implementation and identity/reconciliation proof. No such reconstruction is currently attested; repeating the production assembly is outside this audit.
3. **Immutable replayable matvec representation.** Retain a representation sufficient to evaluate `A0*x` and `||A0||∞` without a full second band matrix. It must preserve all element contributions, constraints, ordering, coefficient precision, and exact input identities. Such representation is not yet designed/qualified and may itself approach matrix-scale storage.

### Definitions and robust evaluation requirements

For a finite candidate `x`, define `r=b0−A0x`. A future report should include:

```text
absolute residual:       ||r||∞
normwise backward error: η∞ = ||r||∞ / (||A0||∞ ||x||∞ + ||b0||∞)
componentwise error:     ηc = max_i |ri| / (Σ_j |aij| |xj| + |b0_i|)
```

The componentwise denominator is row-wise; the normwise denominator is formed without overflowing intermediate products. The computation should validate all input/output values are finite; use scaled products/sums (e.g. mantissa/exponent scaling) or an adequately wider accumulator where available; use compensated accumulation for dot products; preserve/record underflow and subnormal behavior; and not let overflow or underflow silently become a finite-looking success. The band’s reserved LU fill rows must not be mistaken for original nonzeros when applying `A0` or calculating `||A0||∞`.

Zero-denominator policy must be explicit: if a denominator is zero and its numerator is zero, return zero only under a documented convention; if the numerator is nonzero, report an infinite/undefined error and fail closed. Non-finite numerator, denominator, matrix, RHS, or solution is a validation failure. Scaled norm algorithms (such as LAPACK’s xLASSQ family) can avoid avoidable overflow/underflow in sum-of-squares, but the metrics above use infinity and absolute row sums, so the implementation still needs a safe scaled-sum/product procedure.

### What theory does and does not authorize

Floating-point unit roundoff and backward-error analysis explain arithmetic sensitivity under explicit assumptions; they do not set a universal application acceptance cutoff. Backward error asks whether the computed solution solves a nearby problem, while forward error also depends on conditioning. LAPACK’s error-bound literature distinguishes these concepts and discusses componentwise bounds; `DGESVX` estimates reciprocal condition and error bounds, with its `INFO=N+1` condition warning being a driver-specific rule, not a universal acceptance standard. ShellSet calls `DGBSV`, not `DGESVX`, and the supplied F2 evidence contains no validated condition estimate, residual, or solution. See [LAPACK Working Note 165](https://netlib.org/lapack/lawnspdf/lawn165.pdf), [DGESVX source](https://www.netlib.org/lapack/explore-html/da/d21/dgesvx_8f_source.html), and [DGESVX documentation](https://www.netlib.org/lapack/explore-html/d5/dbe/group__gesvx_ga82173a93234afc15d70b64233b3e5bc8.html).

No source or authority justifies a numerical residual/backward-error threshold for this ARCANA case. Keep `THRESHOLD_UNJUSTIFIED`. The engineering comparison tolerances in other diagnostic contexts are not solve acceptance tolerances and must not be repurposed. Numerical backward error, forward accuracy/conditioning, discretization error, input uncertainty, and physical-model accuracy are separate claims requiring separate evidence.

### Nullspace, gauge, and operator class

The possible nullspace/rigid modes and any gauge policy are unresolved and remain distinct from residual quality. Weak diagonal dominance does not prove singularity; an `INFO>0` pivot or poor residual would not by itself identify a physical nullspace. Do not infer or apply a gauge here. D2’s `OPERATOR_CLASS_UNVERIFIED` is unchanged; no symmetry or positive-definiteness presumption is made.

## C. Requirement / gate matrix

`ATTESTED_OFFLINE` applies only to the named source-derived/configuration fact, not to runtime execution. Failure action means the future gate must stop without entering Solver or accepting a numerical result.

| Requirement | Evidence source | Verification method | Status | Missing authority / evidence | Failure action |
|---|---|---|---|---|---|
| Mesh, DOF, and band dimension formulas | `SHELLS_v5.0.f90:326–365`; `MOD_Shells.f90:5311–5368`; recovered F2A-V diagnostic | Recompute integer dimensions and checked byte multiplication | `ATTESTED_OFFLINE` | None for source-derived dimensions; runtime revalidation still required | Reject mismatching FEG/config/diagnostic dimensions |
| Named main-array element counts and ABI-conditional bytes | `SHELLS_v5.0.f90:381–453,671,818`; runtime module `:52–56,79–89` | Source census plus overflow-safe arithmetic under stated sizes | `ATTESTED_OFFLINE` | Exact Fair ABI/compiler flags, descriptors, local temporaries | Do not use subtotal as hard total-memory cap |
| Complete peak process memory / max theoretical total | ShellSet source, compiler/runtime/LAPACK allocations | Source inspection cannot bound all implementation/runtime allocations | `PENDING_HPC_MEASUREMENT` | Compiler-generated temporaries, libraries, stack, allocator, MPI and OS accounting | No resource sign-off |
| `Assign` / `GetPBx` active local allocations | `MOD_Shells.f90:293–303,1620–1629,1904–1938` | Determine source extents and outline-file-dependent dimensions | `ATTESTED_OFFLINE` for existence/order; exact `other_shapes` bytes unresolved | Actual outline point counts, ABI and transient peak | Validate shape bounds; resource budget remains open |
| One-worker/two-rank dispatch | Case contract; `ShellSetMain.f90:88–90,137–149,211–212,244–259,567–570` | Trace List-mode dispatch for one model and two ranks | `ATTESTED_OFFLINE` as source control-flow | Runtime rank placement and actual per-PID memory | Verify rank map before any future authorized call |
| Fair-enforced memory headroom and process/job caps | Case asks operator for cap; no new Fair evidence | Read cgroup, scheduler, RLIMIT and available-memory settings in authorized environment | `PENDING_HPC_MEASUREMENT` | Current Fair node/job constraints and enforcement | Do not launch until actual imposed limits and safety margin are attested |
| Fair peak per-PID RSS/PSS and job cgroup peak | No Solver attempt; F2A-V stops pre-Solver | Instrument a separately authorized bounded run | `PENDING_HPC_MEASUREMENT` | Actual runtime peak and rank accounting | Stop on cap breach; report raw metrics, no inferred cap |
| Exact `A0`, `b0` preservation/reconstruction | `MOD_Shells.f90:8635–8673`; D3 design | Select and verify copy, independent rebuild, or immutable matvec record | `BLOCKED_INSUFFICIENT_AUTHORITY` | No selected/qualified original-operator retention strategy | Future result cannot be accepted without same-call A0/b0 identity |
| Residual/backward-error algorithms and non-finite/zero handling | Mathematical definitions in this report; DGBSV entry contract | Implement scaled/compensated calculation and synthetic edge tests before any solve | `ATTESTED_OFFLINE` for definitions/design only | No implementation/tested numerical evidence yet | Reject invalid/nonfinite/undefined metric cases |
| Numerical acceptance threshold | No ARCANA threshold authority identified; D3 `THRESHOLD_UNJUSTIFIED` | Authorial/numerical policy plus evidence appropriate to intended claim | `BLOCKED_INSUFFICIENT_AUTHORITY` | No defensible solve acceptance tolerance | No pass classification for a candidate solve |
| Solver residual/solution/conditioning evidence | No F2A-V solve; stop was before Solver | Future explicitly authorized numerical evidence with A0/b0 and error assessment | `PENDING_NUMERICAL_EVIDENCE` | No `x`, residual, condition estimate, or validated uncertainty | Preserve blocked result |
| Operator class / possible nullspace / gauge | D2 report, source, F2A-V asymmetry evidence | Separate mathematical and numerical adjudication | `BLOCKED_INSUFFICIENT_AUTHORITY` | Active alpha values, operator identity/symmetry proof, nullspace/gauge authority | Keep `OPERATOR_CLASS_UNVERIFIED`; no gauge |
| Exact Fair binary and linked LAPACK/MPI identity | Source lock and qualification artifacts | Verify executable/build provenance and linked runtime in the target environment | `PENDING_HPC_MEASUREMENT` | No fresh target executable/library attestation in this gate | Reject environment/source mismatch |

## Checks performed in this audit

- Read the repository instructions and current project ledger handoff, including all five ledger records; no ledger file was changed.
- Rechecked branch, HEAD and status; preserved all pre-existing untracked output evidence.
- Verified the D3 report hash and checked the vendored ShellSet source lock against all 15 current source artifacts.
- Traced main ShellSet dimensions/allocations, KSize band arithmetic, DGBSV call/overwrite, active iConve dispatch, local outline allocations, and the Boss/worker path.
- Independently recomputed the matrix, D3 core subtotal, A0/b0-copy variant, and identified the D3 copy-scenario arithmetic discrepancy documented above.
- No Python tests were added or run; no source, ledger, input, FEG, runtime package, evidence bundle, or canonical state was modified.

## Remaining blockers and next decision

Offline work can next produce static arithmetic regression checks and synthetic tests for overflow, byte formulas, band indexing, residual scaling, zero denominators, and non-finite handling. These would test a proposed implementation, not qualify a Solver run. Before any resource gate, obtain a separately authorized Fair environment attestation of the actual executable/toolchain, MPI rank placement, job and per-process limits, available headroom, and measurement/enforcement mechanism. Before any future numerical run, separately authorize a run and select an A0/b0 identity strategy; produce a justified acceptance policy or explicitly limit conclusions to descriptive diagnostics. Nullspace/gauge and operator-class adjudication remain independent.

No Solver authorization follows from this audit. The possible next administrative decision is whether to commission offline-only test design and a non-executing Fair resource-mechanism attestation. Neither authorizes Solver, factorization, gauge, mechanics, or evolution.
