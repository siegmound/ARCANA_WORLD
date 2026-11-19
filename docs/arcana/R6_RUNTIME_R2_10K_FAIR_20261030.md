# R2 — fresh synthetic 10k FAIR execution

2026-10-30. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`R2_10K=PASS_FRESH_10000Y_COMMITTED_HISTORY_AND_MEASURED_RESOURCES`

One newly computed trajectory reached Y10000 with10000 annual physical advances,
one live R2 frontier and40 REC1 B0 committed checkpoint/journal pairs. The user
ratified the policy and explicitly authorized this run; the free-memory preflight
was waived and not performed. No retry, resume, second full trajectory,100k,
physics/source edit, full legacy export, commit or push. Scientific/production
authority remains false. This is a synthetic nine-cell/C028–C029 engineering run,
not a qualified planetary/scientific production history.

## Identity and execution

Branch r6/runtime-copy-r1-fair, HEAD2c71370eb9a959c78121ce1c88ec8e9e37187787,
intentional uncommitted R1/R2/REC1/L1 sources preserved. All2745 L1 evidence
members and measured source/test SHA pins were independently rehashed before
launch; the three original E0 inputs were verified by the unchanged L1 reader.
All source/test pins were independently rechecked at completion. Original
oracle/REC1/L1 manifest identities are unchanged. Prior archives were read-only;
no fresh full original-member rehash is claimed beyond the L1 evidence checks.

Evidence root:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R2_10K_FRESH_20261030_01`.
WORKTREE_BEFORE.tar/patch, PREFLIGHT, R6_10K_EXECUTION_GO, SINGLE_LAUNCH and
FINAL_PARAMETER_VERIFICATION bind authorization, source/forcing and invocation.
The first manual HEAD comparison contained a transcription error; it stopped
before launch and was corrected against the authenticated L1 REPORT head.
No numerical failure or retry occurred.

Launcher SHA `7844b40dd68d879850de4500370aa6418009496747e3d04634556880836b6dd9`.
Contract file SHA `8f02eadcc5fb6a065963956e64192eeb28cc14a6dccdf6eebef17a9c1723b9a4`.
This is a new exclusive read-only contract, with the nine ratified query years;
the earlier proposed contract SHA was not reused or rewritten.

Contract: planned10000Y, external advance1Y, compact_query, full causal retention,
CP+B0 every250Y, journal fsync10Y. C028 uplift0.0001m/year,total1.0m; C029zero.
Mechanical opening0.01m/year; hydrology31557600s. Effective config was checked
before launch using a zero-advance runtime. `--help`, `prepare --help` and
`run --help` supplied the actual CLI. The sole execution argv is in SINGLE_LAUNCH;
it uses `--advanced-segment-years 10000`, explicit opt-in and no `--resume`.

Same account-holder-authorized FAIR interactive session58727; no available
scheduler command/context or actual scheduler-only rule was identified. No
administrator policy attestation is claimed. Actual cpu.max=max100000 and
memory.max=max were observed; visible CPUs0..127 are not a reservation or128-core
utilization. Quota is UNKNOWN where not exposed; successful writes/fsync and
the observed run are the storage execution evidence. No invented application
RAM/time/output/thread limits. Runtime versions are in RUNTIME_ENVIRONMENT.

## Closure and causal integrity

Actual compact records **610001**: 1
root snapshot, 10000 deltas, 10000
regional annual records, 10000 Unified/Deep steps and
**580000 events**. Logical snapshots **10001**;
NULL/absent source event timestamps **80000**;
final deposits **110000**. Counts were measured, not
assumed from a constant annual58-event/11-deposit cadence. Observed annual
event min/max=[58, 58], deposit min/max=[11, 11].

Cold verification checked all40 B0 typed pairs, native digests, source/config,
regional/Unified clocks, global ordinals/local chain links and chunk hashes.
Latest committed pair is Y10000 and equals the launcher's final native digest.
A zero-advance terminal restore regenerates the same full native checkpoint.
No extra numerical advancement was performed during acceptance.

Every annual regional event equals its original annual-record event in order
and content; no timestamp was inferred. Every append-only deposit has a unique
event ID, unchanged material/source/destination identity and causal times, and
matches a deposition event. Existing rows are retained with zero delta deletion.
All annual regional water/solid, Unified water/sediment/substrate/geometry and
Deep inventory balances pass their existing numerical tolerances. Mechanical
energy residuals are retained as diagnostics under unchanged solver rules.
Material-volume identities, finite state values and Deep stock/time continuity
were checked. Detailed residual maxima, thermal substep histograms and all-year
event/deposit counts are in HISTORY_AND_QUERY_VERIFICATION/CAUSAL_YEAR_AUDIT.

Ordered compact kind/payload/global-sequence digest:
`31488e07c2f4372fd56764b3614a5bda86cc78ee80f25fc2278c15602a73efe4`.
This authenticates the compact causal record order; it is not a fabricated
10k oracle or a hash of eagerly materialized10001 full snapshots.
No unsupported original1000Y-prefix parity claim is made across horizons.

All nine saved snapshots were independently reconstructed from committed data:

| Year | Query file bytes | Canonical reconstructed snapshot SHA256 |
| --- | ---: | --- |
| 100 | 358265 | `99a83a0e7b0611c0c9b7ec13f9ab3210371a18f98f219c45e674a8bdcb87fd7e` |
| 250 | 888544 | `bb381c46bab057e2252c9cffc91676e78f5320d2f4c19c797fc419011789866d` |
| 500 | 1772380 | `0b2686fff4f7b7a2e3bbbc0a7c29fa481b821344afac6beb59e5f7916e47f613` |
| 750 | 2656170 | `aeff4afde76affe26514546423bd818e12902574261aa2e082b0741714059e46` |
| 1000 | 3539995 | `034c2614e1843d1ec18f9acfae425e93011e6bb10e46155f13aea16e73904659` |
| 2500 | 8908927 | `eea65aa24952aa70e18763b3583e795aa472544ccf965ed5d5e9a379b24931b9` |
| 5000 | 17857827 | `411113e1e34d9094d9a34811f3d23ce7454f5845a9aee90faca199023835952a` |
| 7500 | 26807078 | `3a8c297e642b41dcf75896323339c2bbc3938e362629964ddc7b84ce5af74c9d` |
| 10000 | 35756381 | `94692217e1ed614b33bdeb4dcc351e598a37fd5090747eae9649e59e49f43db2` |

## Resource measurements

| Measurement | Observed |
| --- | ---: |
| Advance+numerics+compact ingest sum | 1,244.446166s |
| Loop step service sum, including CP/fsync | 1,382.151218s |
| All40 paired commits | 117.845563s |
| Additional periodic journal fsync | 19.556098s |
| Launcher query batch, including prefix validation | 96.424889s |
| Launcher pre-receipt wall | 1,482.505809s |
| Supervised launch-to-exit observed wall | 1,484.032774s |
| Child CPU user/system | 1,453.308233/11.855023s |
| Equivalent utilized cores, full process | 0.987285 |
| Own process peak RSS | 3886424KiB (3795.34MiB) |
| Cold full pair verification | 63.580721s |
| Cold causal/query replay audit | 56.227237s |
| Post-run audit wall before receipt | 124.862212s |
| Observed calendar launch-to-acceptance | 1687.085s (~1s timestamp precision) |

The process total includes requested query serialization and final launcher
receipts. Supervisor wall may include up to about1s polling lag. Cold required
verification is additional; calendar launch-to-acceptance includes its elapsed
work and supervision gaps. Report/manifest construction follows these totals.
FINALIZATION.json records elapsed launch-to-final-evidence verification after
the manifest is sealed and rehashed; it binds that manifest and is a separate
post-manifest completion receipt.
Timings are nested: commit and phase components must not be added twice.
Full annual CPU/wall, memory and100 complete100Y windows are retained.
Annual service p50/p95/max=0.105937/0.265076/5.389727s.
Exclusive phases and CP/fsync/validation/B0 breakdowns are in REPORT/WINDOW100;
operator groups include numerical scans/bookkeeping, not isolated arithmetic.

| Window | Advance+compact s | Step service s | End RSS KiB | End deposits |
| --- | ---: | ---: | ---: | ---: |
| 1–100 | 3.181873 | 3.245628 | 63372 | 1100 |
| 901–1000 | 4.490687 | 5.812350 | 247536 | 11000 |
| 2401–2500 | 6.902569 | 8.770560 | 573468 | 27500 |
| 4901–5000 | 10.255873 | 13.500627 | 1035288 | 55000 |
| 7401–7500 | 17.191929 | 21.512807 | 1532780 | 82500 |
| 9901–10000 | 28.412477 | 33.803141 | 2059076 | 110000 |

Raw RESOURCE_SAMPLES and annual telemetry retain process-tree RSS and separately
shared cgroup current/peak. Shared session memory is not this process's RSS.
The128 NumPy threads do not imply128 utilized cores. Cold audit peak memory is
reported separately, not merged into the numerical process RSS.

Disk bytes/file counts by journal, checkpoints, B0, active and query/invocation
service are in REPORT.json. Complete run directory: **2469842406
logical B**, **2470232064 allocated B**,
**219 files**. Journal=1621296371B;
native checkpoints=739013891B. Complete evidence and
final manifest add source snapshots, telemetry and audit receipts.

## Interpretation and remaining limits

Five O(D) deposit scans and resident R2 entries/frames remain. Zero full snapshots
and old-deposit copies per numerical step were verified from structural metrics;
checkpoint/query compatibility work remains explicit. REC1 verification retains
the decoded checkpoint chain. Source and trajectory are unchanged; no second
optimization was introduced to force the run through. CP250 permits up to249
years rework; staged fsync does not authorize restart. This run suffered no
interruption; bounded L1/REC1 crash evidence supplies the existing recovery scope.

R1's historical1000Y loop214.125572s and1.916GB HISTORY represent a different
horizon and full legacy-output service. R2's prior1000Y loop40.240046s likewise
does not imply linear10x scaling. This run is a measured compact-service10k
result, not an equal-work speedup comparison against a nonexistent10k baseline.
No full legacy materialization, new scientific/production authority, geodynamic
solver qualification, hardware power-loss or storage failover certification.

Next: review the actual measured growth, resource/service costs and recovery
objective. Any new numerical run, optimization, legacy export or extended
horizon requires its own scope/authorization. No automatic follow-on simulation.
