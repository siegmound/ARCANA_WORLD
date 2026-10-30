# ARCANA R6 INT10K — AUTHORIAL GO for one synthetic Runtime R2 1000Y numerical trajectory

**Date:** 2026-10-30. **User instruction:** "facciamo il prossimo passo" following R2 bounded PASS and explicit proposal of a separate R2 new 1000Y numerical execution gate. Interpretation: **user authorizes this ONE new R2 1000Y engineering benchmark**, not any 10k, production, geodynamics, other solver, commit or push. This file is an authorization and execution contract, **not an assertion that a run has occurred**.

## Prior qualification and source

Authoritative local FAIR report: `docs/arcana/R6_RUNTIME_R2_STRUCTURAL_FAIR_20261030.md`, candidate `R2_BOUNDED=PASS_BOUNDED_EXACT_RECONSTRUCTION_AND_STRUCTURAL_ELIMINATION`, 168 tests, 3Y/10Y exact replay, anchor y101/501/751 and five-year y751–755, offline exact 61001 logical payloads and 1001 snapshots from the original archive, including 8000 NULL source event timestamps; prior offline compact file 162,037,378 B vs 1,916,080,917 B legacy. **No full R2 numerical 1000Y trajectory has been executed as of this authorization.**

FAIR worktree (operator-reported): `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`; branch `r6/runtime-copy-r1-fair`; commit baseline `2c71370eb9a959c78121ce1c88ec8e9e37187787`. R1 and R2 changes are **intentionally uncommitted**. Never impose "clean git status" as a hard prerequisite; instead create an immutable manifest/diff/hash of the precisely validated dirty worktree. Preserve R1 backups and all earlier R1/R2 evidence. R1 patch: `R1_TRACKED.patch` SHA `1c868b243da5375bb5c948d3bbc9c57290828a5cb367a35e08b117ab35467c67`; R2 against preserved R1: `R2_AGAINST_PRESERVED_R1.patch` SHA `965f463559a618e100af85950513f97832714608169ef682e9c5103163371c9a`. Verify local actual bytes before use; do not recreate code from a published older GitHub branch.

Original immutable 1000Y manifest SHA `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`; R1 candidate 1000Y manifest SHA `3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b`. Their original archive directories are read-only inputs, never destinations.

## Gate P0 — read-only checks and bounded preflight before any 1000Y launch

1. Confirm actual FAIR cwd, local branch/HEAD, worktree staged/untracked files, exact source hashes, R1/R2 patch fingerprints, `QUALIFICATION_SUMMARY.json`, `SOURCE_SHA256.json`, latest 168 tests and original E0/source/oracle pins. On a mismatch, stop with `BLOCKED_SOURCE_OR_ORACLE_MISMATCH`. Do NOT reset, pull, checkout, merge, or overwrite original worktree/evidence.
2. Verify cluster allocation/job context, actual scheduler policy/site permission, cpuset/quota, free/user-quota storage and memory. Presence of many CPUs and unlimited cgroup max does NOT prove allocation rights. Run under site-approved execution context. User specified no extra application duration, memory, thread or output caps; site constraints still bind.
3. Use only synthetic **1000 planned model years**, existing E0 pins, identical region and Deep forcing, one external physical year per advance, fixed planned horizon **1000**, identical run-level uplift (preserve the same total/annual semantics as the original 1000Y), 3x3 basin and C028/C029. Validate numerical model authority for this synthetic scope. Before full run, execute cheap read-only sanity tests and one bounded smoke trajectory under the same exact source/config. The user authorizes necessary setup and small preflight tests, but not broader experimental exploration.
4. Prepare/review an opt-in R2 1000Y runner if not already present; the R2 module's public `CompactRuntime` API must be verified from local source, not invented. **Keep one live R2 runtime/frontier across 1000 yearly advances** and write compact frames/event/year records as they are produced. Do not cold-import/reconstruct the complete prefix/checkpoint or legacy full snapshot at every year. Unsealed frames must be labeled unsealed; their `DEFERRED_UNTIL_MATERIALIZATION` snapshot SHA is not silently converted to a full canonical SHA.
5. Use a uniquely named new evidence directory under `ARCANA_WORLD_EVIDENCE/R6`, not any original root. Explicitly refuse reuse of an existing directory (fail closed; no automatic cleanup of originals). Capture source code SHA, configuration, command, environment, host/allocation, manifest, results and errors. Ensure writer flush/close and on-disk readback integrity. No invented limit or silently swallowed writer errors.

## Gate P1 — authorized ONE fresh synthetic numerical 1000Y R2 run

- Advance from year 0 to 1000 once in a continuous new R2 trajectory, with explicit durable compact journal/order/identity. Preserve original numerical operators, constants, float reduction order, all 58000 events, 1000 region year records, 1000 unified Deep steps, 1001 logical regional snapshots, all 8000 source event NULL timestamps and physical balances. New R2 compact representation need not be physically byte-identical to legacy full-history output.
- At milestones year **100, 250, 500, 750, 1000**, materialize and verify complete coupled restart checkpoint from the live frontier; record checkpoint creation, SHA, file size and verification timing. Do not force a full checkpoint every year. Verify continuity on a separate bounded resumed copy/checkpoint without mutating the continuing master run; compare exact next-step/restart against continuous record.
- After (or independently of the timed hot loop), use the **newly computed R2 compact history**, not the archived B1 converter, to reconstruct every required original-format state and the whole source ordering. Check **61,001** original payloads against independent original indexed kind/payload SHA in order; all 1001 regional full snapshots and 9 cells, all nondeposit and deposit fields, 58000 events incl original 8000 NULL source times, 1000 annual and 1000 unified Deep. Verify source material IDs, mass conservation, hydrology, Deep, unknown semantics and provenance; on mismatch preserve evidence and mark BLOCKED.
- Distinguish exact *logical frontier state* from different legitimate R2 checkpoint envelope format. Compare governing contents, replay sufficiency and canonical physical values; only claim checkpoint byte equality if exactly the same schema/bytes. Validate new R2 checkpoint seal/hash and a real resumed numerical continuation.
- No extra long runs, no 10k, no other solver, no physics modification, no source auto-commit/push. If first run fails, preserve failure evidence; **do not automatically relaunch or patch-stack**.

## Measurements required for a fair R1/R2 comparison

- Cold setup/import; **simulation 1000Y hot path + compact ingestion**; year-wise/100Y-window wall and CPU user/system, core-equivalent, peak resident/process-tree RSS; relevant per-domain kernel vs repeated scans, frame creation, writer/flush, checkpoint export/validation. Collect p50/p95/max, first vs final 100Y, and source final deposit count.
- Compact output logical and allocated bytes, disk file count, payload/event/Deep/metadata/anchor and checkpoint bytes. Include all actual output, not only compressed frames.
- **Separated downstream services**: complete offline source-format reconstruction/materialization and oracle hashing/readback wall/CPU/bytes; selected historic cell/material/Deep queries latency; genuine restart from an R2 checkpoint and end-to-end wall. Sum only disjoint stages and disclose overhead.
- Compare with R1 numerical 1000Y loop 214.125572 s and original 1,916,080,917 B HISTORY only as **historical reference with different physical output service**; never present compact-only vs full-legacy as apples-to-apples end-to-end speedup. Provide like-for-like full-service totals and storage at equal query/restart/compatibility requirements. The bounded five-year full-service benefit and one-year restart penalty are known; test whether amortization persists for 1000Y.
- Provide per-100Y trends and honest remaining five O(D) deposit scans, O(D) queries/checkpoints and full canonical hashes; do not claim full asymptotic O(Y), production durability, or automatic 128-core scaling. R2 historical 162 MB is an offline converted archive, not a run result until new P1 measures it.

## Acceptance and follow-up

Emit one explicit machine marker:
- `R2_1000Y=PASS_FRESH_TRAJECTORY_EXACT_RECONSTRUCTION_AND_MEASURED_RESOURCE_PROFILE` only if actual new R2 numerical trajectory from year 0 generates a closed compact stream, all original **61001 logical records**, all original full snapshots and historic events agree by source canonical SHA and ordering, all five checkpoint/restart milestone conditions pass, and measured resources/costs are disclosed.
- Otherwise `R2_1000Y=BLOCKED_<REASON>`, retain immutable original data and failed-run evidence, no silent partial publication or replay promotion.
- After PASS, propose independently adjudicated **10k integrated synthetic** execution with same physical assumptions and explicit duration/uplift review, runtime/site/job policy, observation contract and source/input hashes. **10k is not authorized by this document**.

```yaml
R2_BOUNDED: PASS_FAIR_OPERATOR_REPORTED_168_TESTS
R2_1000Y_USER_AUTHORIZATION: APPROVED_ONE_FRESH_SYNTHETIC_TRAJECTORY
R2_1000Y_EXECUTION: PENDING_FAIR_PREFLIGHT
R2_10K_EXECUTION_AUTHORIZED: false
AUTO_COMMIT_OR_PUSH: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

Sources: FAIR `docs/arcana/R6_RUNTIME_R2_STRUCTURAL_FAIR_20261030.md` and `docs/arcana/R6_RUNTIME_COPY_R1_FAIR_20261030.md`; GitHub ledger `PROJECT_LEDGER/R6_INT10K_RUNTIME_R2_BOUNDED_PASS_1000Y_RUN_GATE_20261030.md`.


## Addendum — operator permission for session-58727 (2026-10-30)

Following the previously established user authorization for a **single new R2 synthetic 1000Y trajectory**, Codex reported current FAIR interactive `session-58727` while previous interactive attestation concerned `session-58509`. The user has now explicitly clarified: **"ti dico io che puoi fare la esecuzione"**. Interpret as **ACCOUNT_HOLDER_EXECUTION_PERMISSION_CONFIRMED_FOR_CURRENT_SESSION_58727** for exactly that already approved benchmark. Do not ask this user for an additional authorization, repeat the same question, or incorrectly treat the prior session ID as an immutable numerical oracle.

**Important distinction:** user permission does not constitute an independently verified FAIR site scheduling policy, allocation, administrator attestation, or reserved CPU quota. The previous session-58509 attestation **must not** be relabeled as site certification for session-58727. P0.2 requires an operational assessment of the current environment: check hostname, scheduler/job/allocation variables, cgroup/cpuset/quota, local cluster documentation/terms where available, node role (login or compute), and actual file/job quotas. Run in the current session if execution is permitted by verified local policy or established authorized allocation; if the site requires scheduled compute jobs, submit/use the proper allocated compute job instead. Do not invent a requirement for separate administrator approval unless an actual rule calls for it.

If local site permission **cannot be established**, mark `P0_2=BLOCKED_SITE_EXECUTION_CONTEXT_UNVERIFIED` with the exact missing evidence; do not claim the user permission alone resolves site rules or silently bypass scheduler policy. If the required allocation is present/verified, mark `P0_2=PASS_VERIFIED_EXECUTION_CONTEXT` and proceed without further user confirmation to the one approved R2 1000Y experiment, subject to all other gates. `R2_10K_EXECUTION_AUTHORIZED=false` remains unchanged. Never run a second 1000Y job on failure without authorization.
