# SI1/BW1 F2B-D3C — Fair runtime and resource authority reconnaissance

**Decision:** `D3C_RECONNAISSANCE_COMPLETE__EXECUTION_AUTHORITY_GAPS_REMAIN`

**Scope:** read-only reconciliation of existing repository records and locally retained derived evidence. No Fair connection, job, process launch, MPI, ShellSet, Solver, factorization, assembly, or simulation was performed. No runtime or canonical state was changed.

**Checkout:** `r6/si1-bandwidth-f2av`, HEAD `3247a2f58db282db20722d1155cfa5f605141e63` (the D3B-P0 consolidation baseline). The only pre-existing worktree entries observed were untracked D1A/F2A-V derived `outputs/` files; they were not modified. This report is the sole new file from this audit.

## Evidence boundary

The authority records were read from `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json`, `configs/r6_shells_si1/shellset_source_lock.json`, `configs/r6_shells_si1/engineering_case.json`, `contracts/R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json`, the BW1 reports/manifests and staging contract, the local F2A-V recovery result/manifest, the D3/D3A reports, and the operational ledger. Local SHA256 values below identify the exact files inspected; they do not authenticate an external Fair filesystem or prove runtime facts beyond each artifact's declared scope.

| Local authority artifact | SHA256 |
|---|---|
| `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` | `ab29de4577c4c4b007d41a7ac5567d7b287c7fed5dee3107aeb69dc35df1a350` |
| `configs/r6_shells_si1/shellset_source_lock.json` | `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2` |
| `configs/r6_shells_si1/engineering_case.json` | `c5062a1d831e44ff787e66d2a88e50f570b9d716dfe2b5b19aba0751d2ee529d` |
| `contracts/R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json` | `2a52d5254eb7d3a0efcdeddd9b2c3cf995c22981ed8aba3157c49da1aaa1b2d2` |
| `outputs/r6_si1_bandwidth_bw1/reports/BW1_REPORT.json` | `944dfd039756d8b6cd9faf7ad1907fd034bac09cdbfd563f2385838b2eabc070` |
| `outputs/r6_si1_bandwidth_bw1/manifests/BW1_INPUT_MANIFEST.json` | `63099f944c5379172f74831e08991c3dbe3315967de9bffbb639258448749732` |
| `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_RESULT.json` | `ff32569dc56f500725ca45c790d7e3ea925bc1e99df5d28138e6342ab4b9979f` |
| `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_ARTIFACT_MANIFEST.json` | `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f` |
| `docs/arcana/SI1_BW1_F2B_D3_RESOURCE_RESIDUAL_PREFLIGHT_DESIGN.md` | `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF` |
| `docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md` | `CA2FF09491BBDCB995FC79FB9E4CF66B461C519A2FC67F652E09099C70884989` |

The source lock contains 15 ShellSet file entries. All 15 corresponding files under `external/ShellSet-v1.1.0/` were found and their byte SHA256 values matched the lock. This verifies the checked-out source files against that lock; it does not identify a compiled executable or prove that a particular Fair executable was built from them.

## Three runtime identities — kept separate

| Identity | Path / hash / source identity | Toolchain and ABI evidence | Status and authority boundary |
|---|---|---|---|
| **1. Historically qualified upstream runtime** | Qualification record names `/home/jlpfritas/HPC-POMDP/tools/ShellSet-v1.1.0/ShellSet.exe`, SHA256 `03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349`; runtime branch `arcana-r6-runtime-capacity`, commit `09a06ecd061f00b80a52af86e31d609ff5545a8b`; upstream source identity `JonBMay/ShellSet` commit `e4a6fbd5997b6c4978924649dff1abab0c96ca57`. The executable and source commit are distinct identities. | Record declares NVIDIA HPC SDK 25.11, `nvfortran 25.11-0`, x86-64 Linux / Sapphire Rapids target, `mpifort/nvfortran`, `-Mbackslash`, NVIDIA HPC-X/OpenMPI, and NVIDIA HPC SDK LP64 OpenBLAS-backed BLAS/LAPACK. This is a historical declaration for this upstream build. It is not an ABI probe of the F2A-V process. | `ATTESTED_EXISTING_EVIDENCE` **only for the historical upstream qualification record**. The record reports stock/capacity executions and LAPACK smoke tests. It does not qualify the ARCANA SI1 binary, its modified source, or its memory behavior. The executable itself is not in this Windows checkout for independent rehashing. Its Git commit is absent from the current object database. |
| **2. ARCANA SI1 F2A-V diagnostic run** | Recovered record gives `source_execution_head=df670c8c4faaed641997f5c4bdb701e2ba0afc7d`; evidence Git commit `f318a217dfee2f99d51e834948bcf765d5d45c6b` is locally present as a commit whose parent is `df670…`. Command recorded: `mpiexec -n 2 ./ShellSet.exe -Iter 1 -InOpt List -Dir RUN_OUTPUT`; elapsed `282.0919778123498 s`, return code `75`, log SHA256 `23d2f28e58325ea4c719ef816605d42ba7a4486d475e239ead3daa87e44294a7`. Original F2A-V manifest SHA is `e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854`; recovery cross-reference records original run source commit `e1694e18ddf1843c6709dd7e78f5de7bd6a281b4` and original manifest SHA `605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd`. | Eight staged input files are recorded as verified by the recovery result. The staged reordered FEG hash is `18d78ec0c3382e0408f11f7b9826f5f22db7e6d921884c3375600fb2d447ffd1`; runtime package hash is `a68c073011b2cb7782b760d5ff43b010610eaaddec731d5b39172c6b08294a31`. Contract declares NVHPC 25.11, two MPI ranks, per-process `RLIMIT_AS=32 GiB`, operator-asserted aggregate `80 GiB`, and 1800 s runtime limit; it explicitly records aggregate cgroup enforcement as false. | Run command, staged inputs, log identity, return code and pre-Solver stop are `ATTESTED_EXISTING_EVIDENCE` within the retained recovery record. Actual executable path, executable SHA, compiler build output, linked MPI/LAPACK/BLAS identities and actual ABI are `UNKNOWN`. NVHPC and limits in the contract are `DECLARED_ONLY`; they are not proven runtime observations. The historical upstream binary hash cannot be assigned to this run. The recovered record preserves original `BLOCKED_F2AV_QUALIFICATION`; Solver was not executed. |
| **3. Future F2B preflight candidate** | No selected/built candidate executable, path, SHA256, build commit, or run manifest was found in the inspected artifacts. The BW1 report records no preflight runner and `launch_authorized=false`; its contract says it supplies staging instructions only. The checked-in/vendor source lock identifies source commit `9fef54f6cd17e6e756db3ec28bfc43ee0230fc27`, distinct from the upstream capacity runtime and F2A-V execution snapshot. | Compiler flags, integer/REAL ABI, MPI implementation, linked BLAS/LAPACK, loader resolution and build reproducibility for a future candidate are `UNKNOWN`. | `UNKNOWN`. Source-lock identity is not executable identity. A future candidate needs its own reproducible build record and executable/library inspection before any separately authorized execution. |

The source/runtime commit distinctions are also checkable locally: `df670…`, `e169…`, `f318…`, and the vendor source-lock commit `9fef…` resolve as Git commits in this checkout. The upstream runtime commit `09a06…` does not resolve in this repository object database. This is an object-availability observation, not a claim that the upstream record is false.

## Resource arithmetic and authority

The current engineering case declares 64,442 nodes, 128,880 triangles, zero faults, one model and two MPI ranks. Recovered pre-Solver diagnostics report `nRank=128884`, `kl=ku=727`, `nKRows=2182`. The source-derived band allocation is:

```text
8 × nKRows × nRank = 8 × 2182 × 128884
                   = 2,249,799,104 bytes
```

Under the D3A explicit-array inventory and its stated assumptions (REAL*8 8 bytes; default INTEGER and LOGICAL 4 bytes; default CHARACTER 1 byte), the subtotal is:

```text
2,932,975,900 + 112 × (LRn+1) bytes
```

The optional A0/b0 preservation scenario is:

```text
5,183,806,076 + 112 × (LRn+1) bytes
```

These are conditional named-array arithmetic, not measured memory, RSS, a complete peak, or an upper bound. The local case/report do not establish the actual Fair ABI or the exact LRn value needed to close the expression. Compiler temporaries, descriptors, stack, allocator, MPI/NVHPC/LAPACK runtime and OS accounting remain outside the subtotal.

| Resource fact | Evidence / classification |
|---|---|
| Matrix and explicit-array formulas | `ATTESTED_EXISTING_EVIDENCE` as source-derived arithmetic under stated ABI assumptions; not as process/job memory. |
| Per-process 32 GiB virtual address-space limit | `DECLARED_ONLY` in F2A-V contract; no process/kernel record demonstrates installation or enforcement. It is not a physical-memory budget. |
| Aggregate 80 GiB budget | `DECLARED_ONLY`; contract explicitly says `aggregate_cgroup_enforcement_verified=false`. |
| Runtime ceiling 1800 s | `DECLARED_ONLY`; no scheduler/job enforcement record. F2A-V's 282.092 s is elapsed time to the intentional pre-Solver stop, not a Solver runtime or time-limit enforcement proof. |
| Two ranks / one model | Contract and recorded `mpiexec -n 2` command support requested/launched rank cardinality (`ATTESTED_EXISTING_EVIDENCE`). Static ShellSet dispatch analysis supports one worker for one model. Actual rank-to-PID placement and per-rank memory are `UNKNOWN`. |
| RSS/PSS, cgroup current/peak, available node memory | `UNKNOWN`; no such measurements are in the retained local recovery result or qualification record. |
| Scheduler, enforcement domain and filesystem quota | `UNKNOWN`; no scheduler job record/configuration or enforced-limit capture is available locally. No scheduler type is inferred. |

The historically qualified upstream evidence has runtime durations for its separate example workload, but no SI1 F2A-V memory/RSS/cgroup evidence. Those timings and toolchain metadata cannot fill the SI1 resource gap.

## Evidence matrix

| Requirement | Artifact/source | Identity | Evidence | Status | Authority gap | Next verification |
|---|---|---|---|---|---|---|
| Historical upstream executable identity | `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` | Path and binary SHA above; runtime commit `09a06…`; upstream source commit `e4a6…` | Existing qualification record declares executable, compiler, MPI and BLAS/LAPACK | `ATTESTED_EXISTING_EVIDENCE` (historical scope only) | Binary not locally rehashed; source/runtime commit not available in this repo object DB; not the SI1 executable | If relevant later, obtain artifact and verify hash/build metadata against its own evidence bundle |
| F2A-V executable identity | F2AV original manifest/recovery record; diagnostic contract | Run snapshot `df670…`; evidence commit `f318…`; original cross-reference `e169…` | Command, log SHA, exit 75 and staged-input hashes are retained; no executable hash field/value | `UNKNOWN` | Cannot bind observed compiler/ABI/libraries or binary bytes to the run | New authorized read-only acquisition of the exact staged Fair executable/build artifacts; do not infer from upstream runtime |
| Staged F2A-V inputs | Recovery result plus BW1 manifest/report | FEG/runtime hashes shown above | Eight staged files listed as verified; local BW1 report binds derived artifacts to its manifest | `ATTESTED_EXISTING_EVIDENCE` within those manifests/recovery | Original remote files are not all present in this checkout for independent reinspection; this does not supply executable identity | Reverify from the authoritative evidence bundle in an authorized environment if needed |
| Future F2B candidate executable and libraries | None; BW1 report and Fair staging contract | No candidate SHA/build identity | BW1 says no preflight runner is provided and launch is unauthorized | `UNKNOWN` | No selected candidate or artifact set | Build/source-lock and library identity contract, then static binary inspection; requires a separately approved stage |
| Actual compiler/MPI/BLAS/LAPACK for F2A-V | F2A contract vs upstream qualification record | Distinct run/source identities | Contract declares NVHPC 25.11; upstream record identifies NVHPC/HPC-X/OpenMPI/OpenBLAS-backed LAPACK only for upstream binary | `DECLARED_ONLY` for F2A-V; upstream toolchain is attested only to its binary | No F2A compiler log or link map; cannot transfer upstream library identity | Read existing F2A build/link logs or exact binary metadata; if absent, `PENDING_HPC_MEASUREMENT` under authorized acquisition |
| Actual F2A-V ABI | Contract, source lock, D3A assumptions | No executable-bound ABI record | Default INTEGER/LOGICAL widths are assumptions in resource subtotal | `UNKNOWN` | Compiler flags and actual storage widths not tied to F2A executable | Inspect exact compile flags and verify with existing build evidence or an explicitly authorized ABI probe |
| Static array subtotal | D3A report, source lock, SI1 case, D3B arithmetic tests | nRank 128884, nKRows 2182; LRn not resolved here | Exact matrix bytes; conditional subtotals above | `ATTESTED_EXISTING_EVIDENCE` under declared ABI/extent assumptions | Not complete total memory; LR term remains symbolic | Reconcile actual ABI and LRn from source/input identity; keep overhead separate |
| Requested memory/time limits | F2A-V contract and engineering case | 32 GiB per-process address-space request; 80 GiB asserted aggregate; 1800 s | Configuration declarations only | `DECLARED_ONLY` | Declarations do not show enforcement or current headroom | Read existing scheduler/job and process/cgroup records if available |
| Enforced process/job memory and timeout | No runtime telemetry artifact | F2A-V stopped before Solver | Contract says aggregate enforcement unverified; no cgroup/scheduler/RLIMIT capture | `PENDING_HPC_MEASUREMENT` | Effective memory/time boundary not evidenced | New explicitly authorized Fair read-only environment/resource capture; no job submission implied |
| Historical SI1 RSS/PSS/cgroup peak | No retained measurement identified | No solver execution; pre-Solver stop | Recovery records elapsed time only | `UNKNOWN` | No actual peak or process-to-rank memory data | Requires instrumented bounded runtime acquisition under separate authorization; no retrospective inference |
| Rank/worker placement and memory scope | Case/contract, recorded launch command, source dispatch reviewed in D3A | Two ranks, one model requested/launched | Source indicates rank 0 dispatcher and one worker; no per-PID runtime capture | `ATTESTED_EXISTING_EVIDENCE` for declared/launched cardinality and static dispatch only | Actual placement, resident memory, sharing and aggregate enforcement unknown | Collect rank/PID map and process/cgroup telemetry in a separately authorized run |
| D3B symlink protection tests | D3B ledger and test outcomes | Two skipped test cases | Both skipped because symlink creation was denied in this Windows runtime; `NOT_TESTED_RUNTIME_WINDOWS` | `UNKNOWN` for runtime behavior | No POSIX runtime exercise; Windows race guarantees intentionally not claimed | Separate isolated POSIX test environment, only when available/authorized; tests need no Fair job |

## Next verification and preserved gates

Closed by existing evidence: the upstream runtime's historical identity/toolchain **for that upstream executable only**; F2A-V command, staged-input hashes, log identity, stop code and pre-Solver boundary as recorded; BW1 derived input identity; source-derived band arithmetic under explicit ABI assumptions; and static two-rank/one-worker dispatch logic.

Still requiring a new evidence acquisition: exact F2A-V executable/build/library identity and ABI; future F2B candidate identity; actual scheduler/process/cgroup memory and timeout enforcement; available headroom; rank/PID memory accounting; and any measured SI1 RSS/PSS peak. If Fair can expose these from existing artifacts without launching anything, inspect those artifacts read-only. If not, the specific missing values remain `PENDING_HPC_MEASUREMENT` and need a separately authorized acquisition. No new job is authorized by this report.

The two D3B-P0 symlink tests remain `NOT_TESTED_RUNTIME_WINDOWS`. A POSIX verification may be a distinct, isolated local test procedure if an appropriate POSIX environment is available; it is not evidence about Fair limits and does not authorize contacting Fair.

Preserved without change:

- `OPERATOR_CLASS_UNVERIFIED`
- `THRESHOLD_UNJUSTIFIED`
- `BLOCKED_F2AV_QUALIFICATION`
- `F2B_SOLVER_EXECUTION_AUTHORIZED=false`
- `ARCANA_SI1_MECHANICS_QUALIFIED=false`
- `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`

No execution, numerical qualification, mechanics authorization, or production promotion follows from this reconnaissance.
