# SI1-BW1-F2A-V diagnostic contract

F2A-V is an isolated assembly-only numerical verification probe. It reuses
the locked ShellSet source in a fresh build copy, stages the already validated
F1 inputs, reassembles the same operator, records bounded diagnostics, and
stops with `ERROR STOP 75` before `CALL Solver`. It does not run a solve,
factorization, eigensolve, gauge, mechanics, or tectonic evolution.

## Evidence and gate

The policy is machine-readable in
[`R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json`](../../contracts/R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json).
The runner requires the F2A-V branch, the qualified base and F1/recovery-tool
commits as ancestors, exact ShellSet source-lock validation, F1 evidence, and a
sealed recovery bundle. The original F2-A run is pinned to commit
`e1694e18ddf1843c6709dd7e78f5de7bd6a281b4` and original manifest SHA256
`605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd`. The
offline recovery artifact manifest is independently pinned to
`451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`; the
recovery implementation is pinned to `dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3`.
These identities are distinct. A single untracked partition payload is
allowed only at its governed repository path and only when its SHA256 matches
the validated input manifest. Any other untracked or tracked worktree change
fails closed; there is no global untracked-file exemption. The result preserves
the original F2A `BLOCKED` verdict.

Output must be a fresh child of `ARCANA_WORLD_QUALIFICATION_EVIDENCE_ROOT`,
or `${HOME}/ARCANA_WORLD_QUALIFICATION_EVIDENCE` when unset. Before creating
directories, the runner resolves paths and rejects symlinked/junction parents
and overlap with the repository, source-locked ShellSet, F1/recovery evidence,
or configured WORLD_HISTORY.

The assembly stop is unconditional and uniquely marked
`BW1_F2AV_STOP_BEFORE_SOLVER`. A generated-source proof checks marker/stop
ordering, absence of solver/factorization reachability in the instrumented
section, and the 132-column free-form line limit. The runner has no normal-solve
option.

## Measurements

The symmetry census uses the ShellSet LAPACK band mapping
`AB(iDiagonal+i-j,j)=A(i,j)`. It scans the existing band storage without making
a matrix copy. Every upper-triangle pair is compared; relative anomalies above
`1e-12` are retained with both coefficients, a scaled/saturating absolute
difference, local relative difference, row-scaled discrepancy, and pattern
classification. The census capacity is 100,000; excess or nonfinite pairs are
reported and fail closed, with retained rows explicitly marked incomplete.

Diagonal contribution is computed from scaled sums for
`abs(Aii)/sum(abs(Aij), j != i)`. A relative equality tolerance of `1e-12`
defines the `near` bucket. The ratio definition, zero/undefined cases, and raw
histogram are kept distinct from that classification. The p05/p50/p95 values
are empirical quantile bins from the log10-ratio histogram, not interpolated
continuous quantiles. Non-dominance does not imply singularity.

Row and column coefficient maxima, minimum nonzero magnitudes, scaled-L1
histograms, zero/nonfinite counts, and bounded top/bottom/weak-row lists are
reported. A `log10(scale)+log10(scaled_sum)` representation avoids forming an
unbounded direct norm. No matrix scaling is applied and no condition number is
claimed.

## Mapping limits

Source inspection establishes ShellSet's local pair of mechanical DOFs as
`x=2*node-1`, `y=2*node`. The complete mapping from the reordered global
matrix through the node permutation, component basis, and geographic
coordinates is not proven by the available linked artifacts. Therefore the
result defaults to `DOF_MAPPING_UNVERIFIED`; exported indices are raw matrix
indices only. Hash-shaped strings alone cannot validate the mapping: the actual
authoritative artifacts and their contents must be checked. No geographic
coordinate or plate identity is inferred.

Pairs exceeding the relative threshold are labelled only by their numeric
pattern: `ZERO_NONZERO` when exactly one coefficient is zero, otherwise
`NONZERO_VALUE_MISMATCH`. These labels make no physical or causal claim. Census
class counts, bounded extremes, all row/column histogram populations, zero and
nonfinite totals, and dominance categories must reconcile before the diagnostic
is accepted.
The reassembled matrix, forcing, and symmetry maxima are compared with recovered
F2-A values using relative tolerance `1e-12` and absolute tolerance `0`; symmetry
counts must match exactly. Census pairs must lie in the qualified upper band:
`1 <= i < j <= nRank` and `j-i <= ku`.

## IEEE phase sampling

The probe records inherited sticky `overflow`, `underflow`, and `inexact`
flags before `BuildF`. It captures each of seven requested phases, clears only
these three flags between phases, and restores the union of inherited and
observed flags at the end. It does not change rounding or halting modes. A flag
observed in a phase localizes the phase, not the individual causal operation.
Flags are emitted as per-phase `FLAG_OBSERVED_IN_PHASE` or
`FLAG_NOT_OBSERVED`; unresolved mapping/measurement states remain explicit.
The source-locked code has no IEEE sticky-flag queries, but temporary clearing
could still affect consumers not visible through those calls. The runner's
isolated NVHPC build must compile the IEEE intrinsic calls before runtime can
be attempted; compiler and sticky-flag behavior remain unverified until that
Fair qualification.

## Resource and safety interpretation

Execution retains the F2A envelope: two MPI ranks, one model, 32 GiB
per-process address-space limit, 80 GiB operator-asserted aggregate budget,
1,800 seconds, and NVHPC 25.11. The aggregate budget is not represented as
verified cgroup enforcement. The declared F2A-V workspace is estimated at
13,997,472 bytes (13.35 MiB) for `nRank=128,884` and the 100,000-pair limit:
six REAL*8 row/column norm arrays, one dominance-log array, three integer
row/column/defined counters, bounded pair storage, histograms, and extrema
lists. The estimate assumes 4-byte default INTEGER and excludes compiler and
runtime overhead. The matrix pass remains `O(nRank*nKRows)` already spent
by F2A; additional reductions are `O(nRank)` and bounded output is
`O(min(anomalies,100000))`.

F2A-V evidence is diagnostic and requires separate adjudication. It grants no
mechanics, production, or canonical-state authority.
