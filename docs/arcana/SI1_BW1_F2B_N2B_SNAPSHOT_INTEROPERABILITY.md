# F2B-N2B — binary snapshot interoperability prototype

## Result and boundary

The N2B wire contract is an interoperability extension of the existing N2A `ARCNSNP1` bytes, with an independent fixture-level oracle and a small Fortran reader/writer. The local Windows environment has Python 3.12.10 but no `gfortran`, `ifx`, `ifort`, `flang`, or `nvfortran` executable on `PATH`. Therefore the Fortran source could not be compiled or run, both compiler-backed directions remain untested, and **no cross-language PASS is claimed**. Python-only contract and negative tests can still run.

Current result: `N2B_INTEROP_IMPLEMENTATION_PREPARED__CROSS_LANGUAGE_BLOCKED_COMPILER_UNAVAILABLE`. The required positive decision `N2B_SYNTHETIC_CROSS_LANGUAGE_INTEROP_PASS__SI1_CAPTURE_NOT_QUALIFIED` is not available until a compiler-backed run succeeds.

No ShellSet, SI1 data, MPI, Solver, factorization, assembly, Fair, canonical state, or ledger was used or modified.

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

The Python tests cover explicit wire fields, independent digest construction, Python reader failure on payload SHA mismatch, altered values, omitted records, duplicate coordinates and invalid indices; they contain compiler-backed tests for Python-writer → Fortran-reader, Fortran-writer → Python-reader, raw bitwise fixture comparison, and diagnostic comparison against a dense oracle. In this environment the combined N2B/N2A/D3B run produced 18 passed and 3 skipped; the three skipped cases are exactly the compiler-backed interoperability/Fortran negative tests, skipped because no supported compiler is installed or on `PATH`. The reader's Fortran source is a fixture, not production code. It uses a dense 4×4 array for clarity and is not a production-scale memory design.

When a supported compiler is available, required verification is to compile with conservative IEEE-preserving options, run both directions, compare every logical A0/b0 bit against the independent fixture, verify payload A and source-value B separately, then compare residual/backward-error calculations to the dense oracle. Floating-point matvec results need not be bitwise identical when accumulation order differs; the fixture compares declared metric results to the independent reference without imposing a general scientific acceptance tolerance. Signed-zero/subnormal behavior must be demonstrated for that exact compiler and flags.

## Cost and future capture point

For `m` stored non-`+0.0` logical coefficients and dimension `n`, payload bytes are `56 + 16m + 8n`. This is format arithmetic, not a measured SI1 size. A future streaming Fortran writer can use bounded scalar/record buffers, but needs a count pass (or a safely backpatched count), a write pass, and independent source-digest pass unless one rigorously defined streaming orchestration combines them. Payload verification requires a reread/hash pass or an independently verified streaming digest plus checked close/flush; production atomicity/durability is not demonstrated here. A failed write, short write, hash mismatch, incomplete close, or provenance failure must prevent the subsequent Solver call.

The source-derived candidate capture boundary remains after `VBCs` and before `Solver`/`DGBSV`, for one FEM invocation and iteration only. No hook is implemented. Future failure handling must stop before Solver, preserve originals, and make partial files non-authoritative.

## Remaining gates

- Local Fortran compiler unavailable; cross-language execution is not tested.
- Exact writer/reader bytes and IEEE signed-zero/subnormal handling are unverified on any compiler in this work.
- Fortran reader fixture uses dense storage and is not evidence of a memory-bounded production reader.
- No SHA-256 implementation exists in this fixture; Fortran consumes the expected B value but does not independently recompute B or payload A. Production integrity must use an approved SHA implementation or an independently trusted host-side verifier, with exact byte coverage and fail-before-Solver gating.
- C/D provenance sidecar contract is specified but not implemented or bound to a real invocation.
- No integration test proves that a runtime hook captures the actual post-VBCs buffers, completes durable output before Solver, or preserves the system used by DGBSV.
- No SI1 resource/I/O measurement, numerical acceptance threshold, operator qualification or Solver authorization follows.

Preserved: `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
