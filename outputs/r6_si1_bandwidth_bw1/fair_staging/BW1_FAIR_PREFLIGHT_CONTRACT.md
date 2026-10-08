# SI1-BW1 Fair Preflight Contract

Classification: `NON_CANONICAL_ENGINEERING_REORDERED_INPUT`.

Use only the files staged in this directory's `INPUT/` subdirectory. They use the original ShellSet filenames but are a distinct derived FEG/runtime pair; do not replace canonical inputs.

FEG SHA256: `18d78ec0c3382e0408f11f7b9826f5f22db7e6d921884c3375600fb2d447ffd1`

Runtime package SHA256: `a68c073011b2cb7782b760d5ff43b010610eaaddec731d5b39172c6b08294a31`

## Permitted on Fair

1. Copy the two staged files into a disposable isolated ShellSet run directory under `INPUT/`.
2. Supply the same already-qualified SI1 control files that are not node-indexed (parameter/control inputs, plate outlines, and required non-node-indexed boundary-condition files), without editing them.
3. Build only a disposable preflight source copy instrumented to print the KSize values and terminate immediately after KSize returns.
4. Confirm the printed values are `nRank=128884`, `nCodiagonals=727`, `nKRows=2182`, and `matrix_bytes=2249799104`.
5. Verify termination occurs before stiffness-matrix allocation and before mechanics/solve entry.

## Prohibited

Do not invoke the existing SI1 engineering solve runner unchanged: its normal below-cap path can continue into mechanics. Do not allocate stiffness, run SHELLS/OrbData mechanics, use production MPI solve mode, overwrite governed files, or publish this pair as canonical.

This repository deliverable supplies the isolated staging contract only; it does not supply a preflight executable or claim Fair execution. Any inability to prove an immediate post-KSize stop is a fail-closed reason to stop the Fair run.
