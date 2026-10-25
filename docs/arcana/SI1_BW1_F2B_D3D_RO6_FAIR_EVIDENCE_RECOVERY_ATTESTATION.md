# SI1/BW1 F2B-D3D-RO6 — Fair evidence recovery attestation

**Decision:** `D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE`

## Scope and authority

This report consolidates the operator-reported read-only Fair observations from D3D-RO1–RO6 with local verification of the transferred RO6 attestation and sidecar. It does not launch or repeat any HPC activity, and it does not re-verify the entire original manifest or all historical Fair files.

The Windows access-blocked D3D report, `docs/arcana/SI1_BW1_F2B_D3D_EXISTING_FAIR_EVIDENCE_ACQUISITION.md` (SHA256 `fb5194bc6ed5bfa4e5d08bec322afae25a09373a0981d24bb7df2fefdab26701`), remains unchanged and valid for that earlier attempt: it recorded no Fair session or acquisition from that Windows context. RO1–RO6 is a later, distinct operator acquisition. This later evidence does not retroactively change the earlier report.

Transferred RO6 input:

- `outputs/r6_si1_bandwidth_f2b_d3d_ro6_fair_attestation/D3D_FAIR_RO6_ATTESTATION.json`
- Size: 4,133 bytes; SHA256: `320344b6cfb74042e450bac4347f5a8b820e5702fa4b15c3bf4ff240ec764ec0`.
- Sidecar `D3D_FAIR_RO6_ATTESTATION.json.sha256` names that file and contains the matching digest. JSON parsing and required-field/type checks passed; schema identifier is `ARCANA_D3D_FAIR_RO6_ATTESTATION_V1`.
- No standalone schema definition, detached operator signature, individual RO2–RO5 transcripts, original manifest bytes, selected binaries/logs, ELF inspection output, or scheduler accounting files are included in the transferred directory. The JSON reports `full_manifest_membership_verified=false`.

The sidecar and locally supplied expected SHA establish the identity of the bytes reviewed against that digest. The JSON is an operator record, not a cluster-signed statement; this local check does not independently replay Fair-side reads or hash the underlying artifacts. Additional ELF details below are supplied in the operator's RO2–RO6 result and are attributed as reported observations, not as fields independently verifiable from this JSON.

## Historical artifact identity

| Item | Operator-reported Fair result | Local RO6 record | Bounded conclusion |
|---|---|---|---|
| Compile-only executable | SHA256 `4ef42e110b7386ceed3afae229c2ec08f5db6047f059d2abb95870f9746e91a4` | `build_f2av/ShellSet.exe`, 1,273,664 bytes, same digest | Distinct compile-only artifact; it is not the run executable identity |
| Run build and run copies | Both SHA256 `7e91391478fcee4b29de8831be871b04805db53ff582b5657e57a57b221bc0cf`; copies reportedly byte-identical | Both paths recorded at 1,273,648 bytes with that digest | Their identity/equality is reported as checked on Fair; raw bytes are not present here for independent rehash |
| Original F2A-V run manifest | SHA256 `e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854` | JSON records this as the expected run-manifest identity | RO6 reports the two run binaries and selected build/MPI logs matching their manifest entries; this was five selected members total, including the compile-only executable. It is not exhaustive verification of all 79 run-manifest members |
| Selected build log | SHA256 `2b9dcdfd7345e1062140f472950ba2e273068c837a6e417e46c40597acc56226`, 1,564 bytes | Same path, size and digest recorded | Operator-reported Fair member verification; content itself was not transferred |
| Selected MPI log | SHA256 `23d2f28e58325ea4c719ef816605d42ba7a4486d475e239ead3daa87e44294a7`, 4,313 bytes | Same path, size and digest recorded | Operator-reported Fair member verification; content itself was not transferred |

The compile-only binary hash differs from the run binary hash. Do not conflate the two. Agreement of retained run copies and manifest entries supports artifact provenance within the selected-member scope, but the attestation alone does not prove process-level binding beyond its recorded contemporaneous run evidence.

## Toolchain, ELF and Solver boundary

The RO6 record reports `nvfortran 25.11-0`, `mpifort` backed by the same NVFORTRAN version, and `mpiexec (OpenRTE) 4.1.9a1`; the historical invocation requested two MPI ranks. The operator additionally reports ELF64, x86-64, little-endian; static ELF dependencies `liblapack_lp64.so.0`, `libblas_lp64.so.0`, and MPI/NVHPC libraries; and symbol `dgbsv_` present.

The transferred JSON has version excerpts but no ELF header/dynamic-section transcript or named library file hashes. Accordingly, the ELF and LP64 dependency details are classified as **operator-reported static inspection**, not independently reproducible from the transferred file. Static dependency metadata does not establish which shared-library files were loaded during the historical run. Presence of `dgbsv_` proves only that the symbol is present in the inspected binary/linkage context; it does not prove that a factorization or Solver call occurred.

Recorded historical command:

```text
mpiexec -n 2 ./ShellSet.exe -Iter 1 -InOpt List -Dir RUN_OUTPUT
```

Recorded elapsed time: `282.0919778123498` seconds. Recorded return code: `75`. Historical decision remains `BLOCKED_F2AV_QUALIFICATION`; the run stopped intentionally before Solver/factorization. No such operation was executed in this consolidation.

## Resource evidence

The record contains declarations of 32 GiB `RLIMIT_AS` per process, an operator-asserted aggregate budget of 80 GiB, and a 1,800-second runtime limit. `aggregate_cgroup_enforcement_verified=false`. No RSS/PSS measurements were acquired. The bounded RO5 search reportedly found no accounting file in the inspected paths; that result is **limited to those paths** and is not evidence that accounting does not exist elsewhere on Fair. Thus requested/declarative values are not promoted to granted or enforced limits, and no historical memory peak or aggregate enforcement is attested.

## Evidence classification

- **Locally verified transport integrity:** the transferred JSON matches the supplied SHA256 and its sidecar; JSON parses and its declared schema identifier and required fields are consistent.
- **Operator-reported selected-member checks:** compile-only executable identity; equality of the two run-bundle executable copies; selected run binary/build/MPI log matches to the original manifest. No independent local rehash of those underlying members was possible because they were not transferred.
- **Operator-reported toolchain/static inspection:** compiler and OpenRTE excerpts; ELF class/architecture/endian; LP64 BLAS/LAPACK and MPI dependency names; `dgbsv_` symbol presence. Exact historical loaded library identity is not established.
- **Declared only / not enforced:** per-process and aggregate resource budgets and runtime limit. Aggregate cgroup enforcement is explicitly false/unverified.
- **Not acquired / not attested:** RSS/PSS, historical memory peak, accounting outside the bounded RO5 search, complete original manifest membership, all 79 run members, and independently verifiable RO2–RO5 transcripts.

## Decision and next gates

`D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE` records a provenance advance for selected historical artifacts only. It does not qualify the F2A-V operator or resources, and does not alter the historical `BLOCKED_F2AV_QUALIFICATION` result.

Keep three subsequent workstreams distinct:

1. **Historical accounting recovery (optional, read-only):** an already-authorized operator may inspect additional pre-existing accounting only if a historical job identity or bounded locator is available. No global absence claim, new job, or current-cluster proxy.
2. **F2B residual and numerical criteria:** separately justify the residual/backward-error evaluation contract and any acceptance criteria. `THRESHOLD_UNJUSTIFIED` remains; synthetic validator results are not SI1 numerical evidence.
3. **Operator authorization before any Solver:** require a separate explicit authorization gate after evidence/resource and numerical prerequisites are reviewed. This report grants no Solver permission.

Preserved: `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `BLOCKED_F2AV_QUALIFICATION`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No Fair job, MPI, ShellSet, build, Solver, factorization, assembly, or canonical operation was performed here. No original or historical output was modified.
