# SI1/BW1 F2B-D3D-RO6 — Fair evidence consolidation

**Decision:** `D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE`

**Scope:** integrity review of the transferred RO6 attestation JSON and its SHA256 sidecar. This is not a fresh Fair inspection, a full re-verification of the original F2A-V manifest, or a scientific qualification.

## Source and transport identity

The development checkout was on `r6/si1-bandwidth-f2av` at D3D commit `a6ea808e89b6aa5de00b07c75777ee1efc7b543d`. The earlier Windows attempt remains `D3D_BLOCKED_EXISTING_EVIDENCE_UNAVAILABLE` / `REMOTE_EVIDENCE_ACCESS_UNAVAILABLE`; that historical report is unchanged (SHA256 `fb5194bc6ed5bfa4e5d08bec322afae25a09373a0981d24bb7df2fefdab26701`). The later Fair RO1–RO6 acquisition is a separate observation and does not retroactively change the Windows result.

The transferred file `outputs/r6_si1_bandwidth_f2b_d3d_ro6_fair_attestation/D3D_FAIR_RO6_ATTESTATION.json` is 4,133 bytes and hashes to `320344b6cfb74042e450bac4347f5a8b820e5702fa4b15c3bf4ff240ec764ec0`. Its sidecar names the same file and digest. JSON parsing succeeded; the `schema` field is `ARCANA_D3D_FAIR_RO6_ATTESTATION_V1`, and the `decision`, `historical_decision_preserved`, `scope`, source commit, locator roots, run command, exit status, selected-file records, toolchain records, and resource-attestation booleans are present and internally consistent with the local D3D record where overlapping.

No standalone schema definition, individual RO2–RO5 transcripts, original compile/run manifests, binary files, build logs, MPI log, ELF inspection output, or scheduler accounting records accompany this transfer. Therefore this review checks the JSON’s syntax, sidecar, declared structure, and cross-reference consistency; it does not independently recompute the listed Fair artifact hashes or prove the provenance of the transferred JSON itself. The JSON explicitly sets `full_manifest_membership_verified` to `false`.

## RO2–RO6 evidence scope

The transferred item is a consolidated RO6 attestation. It records selected-file checks and tool-version observations, but does not transfer the underlying artifacts or separate RO2–RO5 records. “Observed on Fair” below means reported by this attestation, not independently observed in this Windows review.

| Evidence | RO6-reported result | What this consolidation verifies | Status / limit |
|---|---|---|---|
| Compile-only binary | `build_f2av/ShellSet.exe`, 1,273,664 bytes, SHA256 `4ef42e110b7386ceed3afae229c2ec08f5db6047f059d2abb95870f9746e91a4` | Record is present in valid JSON; not the binary bytes | `ATTESTED_FROM_EXISTING_EVIDENCE` as an RO6 assertion only; identity is not independently rehashed here |
| Run-bundle binary copies | `build_f2av/ShellSet.exe` and `run_f2av/ShellSet.exe`, each 1,273,648 bytes, SHA256 `7e91391478fcee4b29de8831be871b04805db53ff582b5657e57a57b221bc0cf` | The two reported records have matching size and digest; the original run manifest SHA is recorded as `e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854` | `ATTESTED_FROM_EXISTING_EVIDENCE` as RO6-selected-member assertion; historical execution linkage depends on contemporaneous run records |
| Compile-only vs run binary | Different reported SHA256 values | Difference is directly apparent in the attestation records | They are distinct artifact identities; do not transfer one identity to the other |
| Selected build and MPI logs | Build log 1,564 bytes, SHA256 `2b9dcdfd7345e1062140f472950ba2e273068c837a6e417e46c40597acc56226`; MPI log 4,313 bytes, SHA256 `23d2f28e58325ea4c719ef816605d42ba7a4486d475e239ead3daa87e44294a7` | Hash and size fields are present in the RO6 JSON; the log bytes and original manifests were not transferred for this review | `ATTESTED_FROM_EXISTING_EVIDENCE` as selected-member assertion, not a new content verification |
| Historical invocation and stop | `mpiexec -n 2 ./ShellSet.exe -Iter 1 -InOpt List -Dir RUN_OUTPUT`; elapsed 282.0919778123498 s; return code 75 | Structured record is present; D3D/recovery records agree on stop-before-Solver semantics | Solver was not executed in the recorded run; no new MPI or Solver activity occurred here |
| Toolchain version records | `nvfortran 25.11-0`; `mpifort` reports the same compiler; `mpiexec (OpenRTE) 4.1.9a1`; GNU Make 4.3 | Exact excerpts and return codes are present in JSON | `ATTESTED_FROM_EXISTING_EVIDENCE` as recorded version observations; not a full build/link provenance chain |
| ELF dependencies / ABI | The RO6 handoff reports BLAS/LAPACK LP64 and MPI dependencies | This JSON does not include dependency names, ELF inspection output, library hashes, or a structured ABI record | `DECLARED_ONLY` in the handoff; actual historically loaded library identities remain unattested |
| Full original manifest | Expected compile and run manifest hashes are recorded; membership flag is false | No original manifest bytes or complete member list were transferred | Full manifest verification is explicitly incomplete |
| Resource envelope | JSON repeats 32 GiB per-process `RLIMIT_AS`, operator-asserted aggregate 80 GiB, 1,800 s runtime and 2 MPI ranks; aggregate cgroup verification is false | These fields are declarations/assumptions in the record | `DECLARED_ONLY`; enforcement, RSS/PSS and aggregate limits remain unattested |

The RO6 record therefore supports the limited statement that **the two retained run-bundle executable copies were reported with identical SHA256 values and matched the original manifest**, and that the selected build/MPI log digests were reported matching that manifest. The compile-only binary is different. Because the original manifest and those files were not transferred, this Windows-side consolidation does not independently verify those comparisons. A matching current copy alone would not prove which bytes the historical process executed.

## Remaining gaps

- Full original compile/run manifest membership and all manifest members have not been re-verified in this consolidation.
- No independent historical binding from the run process to the exact executable bytes beyond the selected retained artifacts is established here.
- ELF dependency names, exact library-file identities loaded historically, complete link provenance, and INTEGER/LOGICAL ABI are not independently established by this JSON.
- Scheduler/job identity, requested versus granted limits, enforcement, RSS/PSS, and cgroup peaks remain unverified. The record explicitly says resource enforcement and historical peak RSS/PSS are not attested.
- RO2–RO5 source records are not included, so individual stage observations cannot be audited here.

## Decision and gates

`D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE` applies only to integrity of the transferred attestation and its bounded claims. It does not replace the historical `BLOCKED_F2AV_QUALIFICATION` decision or establish resource sufficiency.

Preserved: `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `BLOCKED_F2AV_QUALIFICATION`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No Solver, MPI, ShellSet, build, factorization, assembly, or scientific operation was performed in this consolidation. No original artifact was modified. Keep the JSON and sidecar out of the code commit; propose publishing them as a separate immutable evidence bundle on the evidence branch, with independently checkable bundle digest and manifest. That publication requires a separate review; no commit or push is performed by this report.
