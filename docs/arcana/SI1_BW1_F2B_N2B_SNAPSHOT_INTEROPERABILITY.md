# F2B-N2B — binary snapshot interoperability prototype

## Final result and authority boundary

Decision: `N2B_SYNTHETIC_CROSS_LANGUAGE_INTEROP_PASS__SI1_CAPTURE_NOT_QUALIFIED`.

Fair operator-reported runs now verify the synthetic Python↔Fortran fixture independently with GNU Fortran and NVFORTRAN. GNU Fortran 13.3.0 passed 21 tests (exit 0) on source commit `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`. NVFORTRAN 25.11-0 passed 29 tests (exit 0) on source commit `2d6021ff0036d350b12a583d9eff1d03e32a7239`, with `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`. The reported test runs separately cover Python writer → Fortran reader, Fortran writer → Python reader, malformed-payload failures, bitwise values and independent synthetic numerical checks.

The test logs and SHA256 values below are operator-reported from Fair. Codex Windows did not read or independently rehash those remote log files. The earlier Windows compiler-unavailable result remains a valid historical development-stage observation, not the current N2B cross-language status. The separate earlier NVFORTRAN compile-only result also remains historical and is superseded in scope by the later runtime fixture test; retain it as a distinct compile record, not as the source of the runtime decision.

| Compiler evidence | Tested source commit | Environment and result | Fair log and reported SHA256 |
|---|---|---|---|
| GNU Fortran 13.3.0 | `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406` | Conda `arcana-r6-linux`; Python 3.12.14; pytest 9.1.1; 21 passed, 0 failed, 0 skipped; exit 0 | `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_GFORTRAN/N2B_GFORTRAN_TEST_20261010T233835Z.log`; `b7a953072d9b142a8836190454cccbebb5399f3fc8b71b50057c6998a94cf0ef` |
| NVFORTRAN 25.11-0 | `2d6021ff0036d350b12a583d9eff1d03e32a7239` | Conda `arcana-r6-linux`; flags `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`; 29 passed, 0 failed, 0 skipped; exit 0 | `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_NVFORTRAN_RUNTIME/N2B_NVFORTRAN_TEST_20261010T235701Z.log`; `b219f790e1c45369a55c12cf60a635d71068a05bda774e5a1577116cb02c945b` |

Both compiler results are bounded to synthetic interoperability fixtures. They do not establish capture of real ShellSet A0/b0, FEM invocation identity, durable integrity of a real SI1 snapshot, Fair memory/I/O sufficiency, solver qualification, or numerical/scientific acceptance. No further HPC test was performed during this consolidation.

### Historical Windows development phase

At the earlier Windows implementation stage, Python 3.12.10 was available but no supported Fortran compiler was on PATH. The compiler-backed tests were skipped, so that phase correctly reported `N2B_INTEROP_IMPLEMENTATION_PREPARED__CROSS_LANGUAGE_BLOCKED_COMPILER_UNAVAILABLE`; it did not claim cross-language PASS. Subsequent Fair GNU and NVFORTRAN results above resolve that bounded fixture-interoperability gap without changing the historical record.

## Wire format v1 (N2A-compatible)

All integer and binary64 fields are explicitly little-endian; no native Fortran derived-type or unformatted sequential record serialization is used. Fortran fixture code writes bytes through `ACCESS='STREAM', FORM='UNFORMATTED'` and explicit byte shifts. The unchanged Python N2A module is the Python writer/reader.

| Offset/order | Type | Meaning |
|---|---|---|
| 0 | 8 bytes | ASCII magic `ARCNSNP1` |
| 8 | u32 | `n` |
| 12 | u32 | lower bandwidth `kl` |
| 16 | u32 | upper bandwidth `ku` |
| 20 | u32 | sparse coefficient record count |
| 24 | 32 bytes | digest B, raw SHA-256 bytes |
| 56 onward | repeated 16-byte records | `row:u32, column:u32, value_bits:u64` |
| after records | `n` × u64 | RHS binary64 bit patterns, vector order |

Matrix indices in the file are zero-based. Records are strictly increasing lexicographically by `(row,column)`. They cover logical matrix coordinates satisfying `0 <= row,column < n` and `-ku <= row-column <= kl`; each non-`+0.0` value is stored exactly once. `+0.0` is implicit; `-0.0` has a nonzero sign bit and is an explicit record. Subnormals are stored as raw 64-bit patterns; no magnitude threshold is applied. RHS values are all explicit. DGBSV fill/padding rows are outside the logical coordinates and must be zero in the supplied AB representation; nonzero fill/padding is rejected.

Header size is 56 bytes. Payload length must equal `56 + 16*record_count + 8*n`; all dimensions and products must pass bounded validation before reconstruction. Reject unsupported magic/version, truncation/trailing bytes, count/length mismatch, invalid or out-of-band indices, duplicates/noncanonical order, explicit positive zero, nonfinite coefficient/RHS, digest mismatch, nonzero fill/padding, or missing coefficient relative to an independent oracle.

### Four distinct identities

**A — payload identity:** SHA-256 of every serialized payload byte. It is detached and must be retained independently (sidecar or publication manifest). The format itself cannot contain its own complete payload hash without defining a separate envelope.

**B — source-value identity:** SHA-256 over `b"ARCANA-A0-B0-IDENTITY-V1\\0"`, little-endian u32 `(n,kl,ku)`, then every logical-band A0 binary64 bit pattern in row-major order (including both signed zeros), then every b0 binary64 bit pattern in vector order. N2A computes this while encoding and recomputes it after decoding; those two values alone are self-consistency checks. In the N2B fixture, a separately written Python oracle holds A0/b0 and independently calculates B. The Fortran writer receives B as an input value; it does not claim to calculate or authenticate B. The Python reader verifies its reconstructed values against the independent oracle. The Fortran reader compares the header B to an independently supplied expected B and exports raw reconstructed values for byte comparison by the oracle harness.

**C — invocation identity:** future sidecar provenance must bind one model/run identifier, MPI rank/process identity as relevant, one FEM call ordinal, nonlinear/outer iteration ordinal and pre-call state identity. No SI1 invocation or iteration identity is created here.

**D — source/input/ordering identity:** future provenance must bind source commit and source blob identities, executable/build/toolchain identity, engineering configuration digest, FEG and runtime input digests, constraints/support identity, and DOF-ordering/permutation digest. These are schema requirements only; no new execution is asserted.

Thus payload SHA is not source-value identity; source-value identity is not proof the correct assembly point was captured; and neither C nor D is encoded as invented SI1 provenance.

## Fixture and checks

The fixture is a 4×4 nonsymmetric general-band system with `kl=1`, `ku=2`. It includes an explicit negative zero, the smallest positive binary64 subnormal, ordinary nonzero values, and a four-entry RHS. Its independent oracle is declared in the Python test, not generated from the Fortran writer. The Fortran fixture source implements both modes:

- `write`: construct the known fixture, count stored records, write the 56-byte header, canonical records and RHS as explicit stream bytes. B is passed in from the independent Python oracle.
- `read`: validate header dimensions, expected record count and expected B, canonical record order, index/band membership, nonfinite values, truncation and trailing data; reconstruct values and export logical matrix/RHS bit patterns for exact Python comparison.

The Python tests cover explicit wire fields, independent digest construction, Python reader failure on payload SHA mismatch, altered values, omitted records, duplicate coordinates and invalid indices; compiler-backed cases exercise Python-writer → Fortran-reader, Fortran-writer → Python-reader, raw bitwise fixture comparison, malformed-payload handling, and diagnostic comparison against a dense oracle. The earlier Windows-only run produced 18 passed and 3 skipped because no compiler was installed or on PATH; this is retained as historical, and the subsequent Fair GNU/NVFORTRAN runs recorded above passed their respective suites. The reader's Fortran source is a fixture, not production code. It uses a dense 4×4 array for clarity and is not a production-scale memory design.

For a future compiler/toolchain combination, verification must compile with compiler-appropriate IEEE-preserving options, run both directions, compare every logical A0/b0 bit against the independent fixture, verify payload A and source-value B separately, then compare residual/backward-error calculations to the dense oracle. The GNU and NVFORTRAN runs above report those fixture checks for their respective versions and flags. Floating-point matvec results need not be bitwise identical when accumulation order differs; the fixture compares declared metric results to the independent reference without imposing a general scientific acceptance tolerance.

## Cost and future capture point

For `m` stored non-`+0.0` logical coefficients and dimension `n`, payload bytes are `56 + 16m + 8n`. This is format arithmetic, not a measured SI1 size. A future streaming Fortran writer can use bounded scalar/record buffers, but needs a count pass (or a safely backpatched count), a write pass, and independent source-digest pass unless one rigorously defined streaming orchestration combines them. Payload verification requires a reread/hash pass or an independently verified streaming digest plus checked close/flush; production atomicity/durability is not demonstrated here. A failed write, short write, hash mismatch, incomplete close, or provenance failure must prevent the subsequent Solver call.

The source-derived candidate capture boundary remains after `VBCs` and before `Solver`/`DGBSV`, for one FEM invocation and iteration only. No hook is implemented. Future failure handling must stop before Solver, preserve originals, and make partial files non-authoritative.

## Remaining gates

- No Fortran compiler is available in the Windows worktree; Fair GNU and NVFORTRAN cross-language fixture results are operator-reported, and the remote logs were not independently rehashed by Codex Windows.
- Exact writer/reader bytes and IEEE signed-zero/subnormal handling are reported as tested for GNU Fortran 13.3 and NVFORTRAN 25.11 under the listed flags; this evidence does not generalize to other compiler versions or production ShellSet integration.
- Fortran reader fixture uses dense storage and is not evidence of a memory-bounded production reader.
- No SHA-256 implementation exists in this fixture; Fortran consumes the expected B value but does not independently recompute B or payload A. Production integrity must use an approved SHA implementation or an independently trusted host-side verifier, with exact byte coverage and fail-before-Solver gating.
- C/D provenance sidecar contract is specified but not implemented or bound to a real invocation.
- No integration test proves that a runtime hook captures the actual post-VBCs buffers, completes durable output before Solver, or preserves the system used by DGBSV.
- No SI1 resource/I/O measurement, numerical acceptance threshold, operator qualification or Solver authorization follows.

Preserved: `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
