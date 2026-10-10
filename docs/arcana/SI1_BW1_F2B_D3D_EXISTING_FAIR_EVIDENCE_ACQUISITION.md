# SI1/BW1 F2B-D3D — Existing Fair evidence acquisition

**Decision:** `D3D_BLOCKED_EXISTING_EVIDENCE_UNAVAILABLE`

**Acquisition state:** `REMOTE_EVIDENCE_ACCESS_UNAVAILABLE`

## Scope and baseline

This gate is limited to acquiring already-existing Fair artifacts. It does not authorize or perform a job, process launch, MPI, ShellSet, Solver, compilation, factorization, assembly, numerical diagnostic, or simulation.

The local checkout was `r6/si1-bandwidth-f2av` at `a20efeadb51be4dc5da27f624a00d8ee3e962e87`. No tracked changes were present at entry; previously untracked D1A/F2A-V derived `outputs/` artifacts were left untouched. The available execution context is local Windows PowerShell. No Fair session, remote filesystem mount, or Fair connector is configured in this context. No attempt was made to obtain credentials, establish a remote connection, or access an unconfigured mechanism.

The D3C report was verified against SHA256 `76a5a65adbbc7d6a9b6a64b35497ee9cd3f4642f286d672579d2779f7f53d058`. Relevant repository indexes point to Fair-side locators under the remote `$HOME`; they do not make those paths locally accessible:

- `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_COMPILE_ONLY/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T125317Z`
- `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`

The compile-only and run directories are separate evidence identities. No assumption is made that they contain the same executable.

## Evidence available locally versus not acquired

| Requirement | Existing local record | D3D status | Gap / next verification |
|---|---|---|---|
| F2A-V compile-only artifact inventory | Ledger locator identifies the Fair compile-only directory and records compile-only PASS. The directory contents are not present in the local checkout. | `UNKNOWN` | Operator should inventory only that exact directory and identify compiler log, executable, source/flags records and their hashes. |
| F2A-V run executable path, size and SHA256 | The locally available recovered result records launch command `mpiexec -n 2 ./ShellSet.exe -Iter 1 -InOpt List -Dir RUN_OUTPUT`; no executable identity is established by that local record. Fair was not accessed, so remote files were not checked. | `UNKNOWN` from local records; remote evidence uninspected | An already-authorized Fair operator should inspect only the exact run locator for the binary and contemporaneous build/provenance metadata. A current file hash does not establish that those bytes were executed historically unless the run-time evidence binds them. |
| Compile-only binary equals run binary | No cross-run hash or immutable artifact identity is recorded locally. | `UNKNOWN` | Hash both binaries independently if both exist; do not equate them by filename, source commit or directory lineage. |
| Historical F2A-V launch/source/log identity | Recovery result records source execution HEAD `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`, command, elapsed `282.0919778123498 s`, exit 75, and log SHA256 `23d2f28e58325ea4c719ef816605d42ba7a4486d475e239ead3daa87e44294a7`. | `ATTESTED_FROM_EXISTING_EVIDENCE` only as values in the locally verified recovery record; Fair source files not acquired in D3D | Acquire the corresponding original log and verify its SHA against the contemporaneous manifest. This does not identify the executable unless the log/build artifacts provide a verifiable link. |
| Original evidence manifest and membership | Recovery record declares original F2A-V manifest SHA256 `e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854`, 79 artifacts, verified by its recovery procedure. Original run cross-reference separately records F2-A manifest SHA `605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd`. | `ATTESTED_FROM_EXISTING_EVIDENCE` as recovery-record assertions; original bundle not acquired here | Operator should verify original manifest and each member from the exact run bundle, maintaining the distinction between F2A-V and F2-A manifests. |
| F2A-V compiler and flags | F2A contract declares NVHPC 25.11; upstream runtime qualification lists NVHPC 25.11, `nvfortran 25.11-0`, `mpifort/nvfortran`, and `-Mbackslash` for a different upstream binary. No F2A-V compile log was acquired. | `DECLARED_ONLY` for F2A-V; upstream identity is not transferable | Read the F2A-V compile-only and run build logs separately. Record exact compiler executable/version and compile/link command only if the logs establish them. |
| MPI, BLAS/LAPACK and dynamic linkage | No F2A-V link map or executable was acquired. Upstream qualification lists HPC-X/OpenMPI and LP64 OpenBLAS-backed LAPACK for its own binary. | `RUNTIME_LINK_IDENTITY_UNKNOWN` | Inspect the F2A-V binary statically with `readelf`/equivalent and retained link/build metadata. Static `NEEDED` entries identify names, not necessarily the exact library files loaded during the historical run. Do not use `ldd` on an untrusted executable. |
| INTEGER/LOGICAL and LP64/ILP64 ABI | D3A uses explicit conditional ABI assumptions; no F2A-V binary-bound ABI artifact is locally available. | `UNKNOWN` | Inspect contemporaneous compiler flags, module/build metadata and any existing ABI report. Do not infer from the upstream LP64 label. Without a historical probe or equivalent build authority, retain UNKNOWN. |
| Scheduler and historical job identity | No scheduler type or job ID is established in the local F2A-V recovery record. `mpiexec -n 2` documents requested launch cardinality, not scheduler allocation or enforcement. | `UNKNOWN` | Determine scheduler/job ID only from files in the exact run evidence bundle. Query the corresponding historical accounting record only if an ID and scheduler are documented. Do not infer from present cluster configuration. |
| Requested, granted and enforced memory/time limits | The F2A-V contract declares per-process `RLIMIT_AS=32 GiB`, operator-asserted aggregate 80 GiB, and runtime limit 1800 s; it explicitly says aggregate cgroup enforcement was not verified. No historical scheduler or kernel capture was acquired. | `DECLARED_ONLY`; enforcement `PENDING_HPC_MEASUREMENT` | Read contemporaneous job request/allocation plus saved process/cgroup limit snapshots. Current limits cannot prove historical enforcement. |
| Historical RSS/PSS/cgroup peak | No process or job peak measurement is present in the local recovery result; elapsed time is to the intentional stop before Solver. | `PENDING_HPC_MEASUREMENT` / otherwise `UNKNOWN` | Search only exact run artifacts and associated identified job accounting. If absent, historical peak is unrecoverable; do not substitute pre-Solver memory estimates or current cluster measurements. |
| F2B candidate executable | No candidate executable/build was identified in D3C; no F2B runner is supplied by the BW1 contract. | `UNKNOWN` | No candidate inspection applies. Any later candidate needs separate source/build/executable provenance and authorization. |

No file was copied from Fair in this gate. Consequently, **no D3D acquisition manifest is created**; creating one would falsely imply that remote evidence was acquired. No replacement or reconstructed historical evidence was written.

## Operator-run read-only acquisition plan

Run only from an already authorized Fair session and only against the two indexed directories above. Do not start a job or executable. Preserve the compile-only and run bundles separately. First list regular files at bounded depth and record metadata; do not recursively search the home or project tree. For every candidate artifact, record host, exact path, run ID, acquisition timestamp, byte size and SHA256. Compare against an independently recorded historical digest where one exists; otherwise label the hash `ACQUIRED_CURRENT_BYTES_ONLY`.

Example bounded inventory (run on Fair by the operator; not run in this audit):

```sh
for d in \
  "$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_COMPILE_ONLY/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T125317Z" \
  "$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z"; do
  printf '\n=== %s ===\n' "$d"
  if [ -d "$d" ]; then
    find "$d" -maxdepth 3 -type f -printf '%p\t%s bytes\t%TY-%Tm-%TdT%TH:%TM:%TS%TZ\n' | sort
  else
    printf 'LOCATOR_NOT_FOUND\n'
  fi
done
```

For a binary found in each bundle, separately use `stat`, `sha256sum`, `file`, and static ELF inspection (`readelf -h -d -n`). Capture retained compiler/link logs and compare binary hashes across the two bundles. Do not execute the binary, including version/help flags. Record that `readelf` dependencies are static metadata; exact loaded library-file identity is not proved without historical loader/build records. For scheduler/resource history, first identify scheduler and job ID from contemporaneous run artifacts; then inspect only that job's existing accounting record and retained process/cgroup snapshots. If there is no saved historical snapshot, mark the corresponding fact unrecoverable/unknown rather than consulting current limits as a proxy.

The operator's resulting evidence bundle should be new and immutable, with a manifest containing only actually acquired files and provenance fields above. Keep unknown fields explicit. A later review must distinguish current filesystem bytes from historical run-time identity.

## Decision and preserved gates

`D3D_BLOCKED_EXISTING_EVIDENCE_UNAVAILABLE`: no Fair access was available in this execution context, so no Fair access was performed and no Fair artifact was acquired. Remote file existence and contents were not checked. The operator plan is ready; executing it requires an operator who already has authorized Fair access. This decision is about access availability only, not evidence existence.

Preserved:

- `OPERATOR_CLASS_UNVERIFIED`
- `THRESHOLD_UNJUSTIFIED`
- `BLOCKED_F2AV_QUALIFICATION`
- `F2B_SOLVER_EXECUTION_AUTHORIZED=false`
- `ARCANA_SI1_MECHANICS_QUALIFIED=false`
- `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`

No job, build, Solver, numerical diagnostic, mechanics, or canonical evolution is authorized by this document.
