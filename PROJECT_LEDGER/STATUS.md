# CURRENT — ARCANA WorldSim R6, GEODYN-1G / GEODYN-2 (2026-10-27)

Decision: `GEODYN_1G_FAIR_BLANKENBACH_INDEPENDENT_BENCHMARK_QUALIFIED__ARCANA_FORWARD_NOT_AUTHORIZED`.

Report: `docs/arcana/GEODYN_1G_FAIR_CLOSURE_GEODYN_2_PREPARATION.md`. FAIR operator-reported ASPECT 3.2.0-pre Blankenbach 1a results passed at levels 3 and 4; metric errors, provenance limits and unresolved risks are recorded there. Original FAIR run files were not imported or rehashed on Windows. No further Blankenbach run is planned absent a demonstrated scientific or correctness need.

GEODYN-2 is prepared, not authorized. A synthetic positive-time ASPECT engineering smoke test and an ARCANA forward window are distinct scopes. The ARCANA window remains blocked by source-backed spatial/initial-state closure, EOS/rheology and positive-time forcing/boundary conditions. Do not extrapolate B5 T0 Euler. Any R6 exchange requires mesh/support identity, explicit units/remapping and conservation checks; Deep remains disconnected without an exchange law.

No numerical evolution, ASPECT, MPI, ShellSet or provider read occurred in this closure. Gates remain unchanged: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

---
## Previous current checkpoint — R6 local prototype consolidation

Decision: `R6_LOCAL_WORK_CONSOLIDATED__PROTOTYPE_ENGINEERING_ONLY__SCIENTIFIC_AND_CANONICAL_PROMOTION_NOT_AUTHORIZED`.

Report: `docs/arcana/R6_LOCAL_WORK_CONSOLIDATION_20261025.md`. Local code/tests commit `d723f9d160e1e90cdb679a68ab9ac2596c6b9a6d` and VIEW commit `ec4c8264c7440def7e4da7a88ecd4b06a10169ef` descend from remote ledger commit `ed0140ea962315f8993c1adfceeef23855f93b8b`; documentation closure follows them. The operator reports documentation commit `ddef4263eb53b6b9c041744a54394258e225df2f` as published; no remote query was run during R6-FLEX-1. The original Windows worktree, its dirty ledger changes, untracked evidence, outputs and ignored caches were preserved; no `outputs/` bundle is part of the source publication.

Local Windows validation used Python 3.12.10 / NumPy 2.5.1: 134 passed, 6 skipped, 2 provider-dependent tests deselected. `ARCANA_EXTERNAL_ROOT` was unset; the two tests could not verify `CANONICAL_T0_PHYSICAL_PAYLOAD`. `compileall` passed. Viewer tests: 16 passed; viewer typecheck passed. No Fair/Linux result is inferred from these checks. Regional V2 results remain synthetic engineering evidence; vertical geodynamic response, qualified positive-duration forcing, and physical/global mapping remain UNKNOWN. The ASPECT-style law is a benchmark adapter; no ASPECT solver was integrated or run.

R6-FLEX-1 report: `docs/arcana/R6_FLEX_1_GFLEx_EXPERIMENTAL_INTEGRATION.md`. In an operator-authorized isolated Windows environment (Python 3.12.10 / NumPy 2.5.4 / SciPy 1.18.1 / gFlex 1.3.0), the actual F1D solver matched an independent analytic strip-load reference within 0.0409%; the actual F2D solver was connected to the regional drainage code on a synthetic, resolution-matched 3x3 grid. Focused suite: 41 passed. Final local output bundle `outputs/r6_flex1_gflex_20261026_05/`, manifest SHA256 `7b6435f2880ed3f9b7c98d7ea1b9066726611774803e8ca1c5f1955d26526ceb`; member hashes rechecked locally and source hash matches the current adapter. The surface/load experiment is synthetic and boundary-limited; it does not provide an R6 geographic load or Te. Physical vertical response remains UNKNOWN; no Fair/Linux result or canonical promotion is claimed.

R6-LAND-1 (2026-10-26): `RETAIN_R6_SURFACE_ENGINE_WITH_SELECTED_FASTSCAPE_METHODS`. Report `docs/arcana/R6_LAND_1_FASTSCAPELIB_EXPERIMENTAL_EVALUATION.md`. Fastscapelib Python 0.3.0 ran a synthetic 61×61, 1 km raster SPL incision benchmark in an isolated Python 3.12.10 / NumPy 2.5.4 environment. Focused tests: 29 passed. Baseline K=2e-5 yr⁻¹ lowered the surface by a diagnostic volume integral of 40.550×10⁹ m³ (not sediment mass); K half/double produced 20.377×10⁹ / 81.766×10⁹ m³. Repeat was bitwise equal; elevation-only 10+10 restart matched exactly. Fastscapelib adds a tested 2-D SPL operator, but has no Python sediment inventory/transport/deposition in the selected API. Keep R6 as owner of water and material accounting; no Arcana coupling or geological authority was demonstrated. Bundle `outputs/r6_land1_fastscapelib_20261026_02/` is local external evidence, manifest SHA256 `d94424355f50b42367060a0310a00ed0e05c2e55fccfe5a15434ed52692d198f`; no output is committed.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

Next: define verified spatial IDs/areas and substrate/sediment accounting for any optional Fastscapelib SPL handoff; do not infer mass or gFlex load from elevation lowering. Keep the geodynamic forward-driver inputs (positive-duration forcing, ARCANA material/reology, support and boundary conditions) unresolved until source-backed data are available.

---

# CURRENT — ARCANA WorldSim R6, 2026-10-25

Decision: PROTOTYPE_FIRST_MULTIPHYSICS_INTEGRATION__ENG10K_ARCHIVE_AND_SEGMENT_EXPERIMENT_EVIDENCED__PRODUCTION_NOT_AUTHORIZED.

### Current numerical engineering state
- Published source baseline on the active R6 branch before this ledger-only update: ec79bf8954a4922f84249fbe23e2657bc5beee23. The previously sealed ENG10K without archive is not overwritten.
- Operator-supplied FAIR retest: Python 3.12.10 / NumPy 2.3.5, 57 PASS / 0 SKIP, OBSERVE_ONLY preflight PASS on ec79bf89. Subsequently one independently authorized, noncanonical 10,000-year archive attempt ended NATURAL_EXIT, code 0. Supervisor: 9.30124842748046 s, sampled RSS peak 127025152 bytes, cumulative output 3587499 bytes; 10 samples, telemetry COMPLETE.
- ENG10K archive validator: SEGMENT_ARCHIVE_VALID, 194 actual states from 186 substeps + 8 initial states over 8 complete trajectories. STATES.jsonl 2671282 bytes (SHA256 17293a6b8090083451d4205523a147728034524eb8db146af731d45ab0405012); segment manifest SHA256 754b73597fc8cc353431bc726c3e998df2ac6bd3730a90347342df06c3a11e5b; outer manifest 12 members verified. Four numerical outputs byte-identical to the earlier direct ENG10K. Checkpoint capability of raw archive remains NOT_QUALIFIED_AS_RESTARTABLE.
- Codex Windows continuation experiment reported on uncommitted changes: restored segment checkpoints payload-identical; 5k+5k max thermal endpoint difference 3.9375e-5 K, 5x2k 6.2539e-5 K, both endpoint time +61.0 microseconds. A split on an actual archived substep boundary rejoined the direct endpoint exactly; that raw record is NOT by itself a qualified checkpoint. Windows ordinary tests 9 PASS / 2 NumPy-dependent SKIP; scoped import-shim path 5 PASS. No supported FAIR/Linux verification of those uncommitted changes yet.
- The Windows worktree contains the pre-existing five locally dirty ledger files and uncommitted code/output for segment_continuation and test/streaming-manifest changes. Those bytes were not published by this update. No additional downstream tectonic consumer for the 73-node profile was demonstrated.

### Current project priority
- Finish the already started Codex local prototype: actual short numerical coupling of the existing thermal/tectonic kernel and Deep operators; synthetic inputs allowed when explicitly engineering-only; check exchanges, reservoirs/balances, stability, elapsed/RSS/output, and keep the original archive immutable. No separate legacy recovery/audit as a prerequisite for this prototype.
- Extend one real tool at a time across geology, material/surface processes, hydrology/erosion and necessary climate forcing; classify direct coupling/feedback versus offline historical consumer. Do not invent effects just to make integration appear bidirectional.
- Deep is a physical domain, not merely a later biological modifier: geological inventory/transport/accessibility, mode-resolved energy, independent stellar +5% E/th candidate, and future CHA-1 event have distinct ledgers. Deep-biological energy and viability coupling belongs to the later coupled biology phase when populations are present.
- Only after the integrated prototype functions: benchmark representative spatial/time resolution and numerical cost, close essential scientific driver/physical gaps, then select and authorize a genuine 210 Ma -> present physical history run. Make resulting states, fluxes, events, checkpoints and provenance reusable for climate, vegetation, fauna, resources and civilizations.

### Authority and execution boundaries
- ENG10K is a reduced two-support/73-node, 10,000-year fixed-Euler-forcing engineering slice, not global geology or geological-time authority.
- B4/B5 T0 kinematics/topology do not yet provide qualified positive-duration forcing or event transitions; spatial mapping from the reduced column to a globe is unresolved. ShellSet mechanics/Solver are not authorized; no canonical WORLD_HISTORY publication.
- Development-mode smoke tests may be lightweight and synthetic/noncanonical. Preserve minimum numerical sanity, energy/material balances, input/output identity, new output destinations and measured runtime; formal scientific requalification is deferred to the candidate production model, not erased.
- Preserved blockers: BLOCKED_F2AV_QUALIFICATION; OPERATOR_CLASS_UNVERIFIED; THRESHOLD_UNJUSTIFIED; RESOURCE_2GB_SCOPE_UNRESOLVED; F2B_SOLVER_EXECUTION_AUTHORIZED=false; ARCANA_SI1_MECHANICS_QUALIFIED=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.

The next section is the retained 2026-10-24 historical checkpoint; its F3 pending action is superseded and must not be followed as current.

## Historical presentation milestones — VIEW-1A/B, VIEW-2A/2T

These display-only outcomes were originally tested on their recorded Windows worktrees and remain distinct from scientific qualification. Their reports and static/viewer assets are now included in the consolidated R6 branch. Current regression on this branch: viewer tests 16/16 PASS and strict TypeScript typecheck PASS. The historical report hashes and original test scope are indexed in `EVIDENCE_INDEX.md`; no new epoch, physical simulation or WORLD_HISTORY publication is claimed.

---

# CURRENT — ARCANA WorldSim R6, 2026-10-24

## INT3-ENG10K-F3 — Option B decision prepared; operator selection pending

Decision: `F3_OPTION_B_DECISION_PENDING_OPERATOR_SELECTION`.
Report: `docs/arcana/INT3_ENG10K_F3_OPTION_B_AUTHORIZATION_DECISION.md`. F3 presents
the two choices and required risk acknowledgements; neither is selected. F1 remains
operator-reported read-only evidence for HEAD `1bf06ef0e624723c3722a351496ae3b7c2544f40`,
not a current measurement. Option B, if chosen, permits only preparation of a later
exact-commit binding; it does not authorize preflight commands or ENG10K evolution.
`INT3_ENG10K_EXECUTION_AUTHORIZED=false` remains in force.

## INT3-ENG10K-F — execution authorization review blocked (2026-10-24)

Decision: `INT3F_ENGINEERING_AUTHORIZATION_BLOCKED__REQUIREMENTS_UNRESOLVED`.
Report: `docs/arcana/INT3_ENG10K_F_EXECUTION_AUTHORIZATION_REVIEW.md`. R4's pinned
manifest and members, kernel and engineering-case hashes were reverified locally;
the source execution files are unchanged from FAIR-tested commit
`cb9bd8373eeb028b83c8bc1abb376624e3553adb` through this documentation-only HEAD
`52a73104cdf56fd3db020868a441889a89286ce5`. The FAIR 43/43 synthetic supervisor
result remains operator-reported and scoped to that tested commit.

The current provider audit and HEAD-bound source-composite identity were not
recomputed: `ARCANA_EXTERNAL_ROOT` is unset and the available Python 3.12.10 lacks
NumPy. Exact diffusion-limited steps, ENG10K runtime/RSS, Fair available memory,
disk quota and OS-enforced limits remain UNKNOWN. The 66,715,648-byte output figure
is a serializer projection, not RSS or a disk guarantee. No ENG10K evolution or
Fair access occurred. No execution authorization is issued.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

## INT3-ENG10K-A — Windows implementation checkpoint (2026-10-14)

Decision: `INT3_ENG10K_CODE_READY__WINDOWS_PREFLIGHT_PASS__FAIR_PREFLIGHT_PENDING__NO_NUMERICAL_EVOLUTION`.
Implementation baseline `8c75c439ab45a9d4e79930bd506e686e088e151d`, branch
`r6/si1-bandwidth-f2av`; report `docs/arcana/INT3_ENG10K_READINESS_REPORT.md`.
R4's exact nine-member bundle was reverified against manifest SHA256
`191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.
The current provider audit reproduced pair 5:11, boundary, supports, frozen Ux
and both complete T0 profiles. Current source-composite `6d277b08…` differs from
R4 historical `b3aff732…` because the composite definition includes checkout
HEAD. Both identities remain separately recorded; non-source provider identity
components match the R4 forcing references. No 10,000-year evolution or FAIR job ran.

Offline ENG10K tests: 17 PASS; existing functional development/INT-0A/INT-1A/
INT-2C regressions: 113 PASS; py_compile and JSON parsing PASS. Linux supervisor
runtime, Fair resource observations and physical applicability over 10,000 years
remain UNKNOWN/FAIR_PENDING. Next: review and publish the implementation, then
run only the no-evolution FAIR preflight with the exact commit and R4 bundle. A
separate authorization is required before any numerical execution.

Post-commit Windows no-evolution preflight passed on code commit
`1b7f3e967050915d1ffa3d7b058f2571c036ee47`; current source-composite was
`cae5ef5c1b95034474031f716b68dcc0dc54fd9f0a56f97dbec26310f241526f`. Python
3.12.10/NumPy 2.3.5, the R4 bundle, seven non-source provider identities,
boundary/supports/forcing/profiles and absent output paths were verified. No
candidate output or numerical evolution was produced. FAIR preflight and Linux
supervisor runtime remain pending.

All prior gates remain: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.


## INT-2C-C3 — real R4 B0 executable replay closed (2026-10-14)

Decision: `INT2C_B0_EXECUTABLE_R4_REPLAY_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`.
Fair-tested source/Windows entry `9fb4fc0286cc09bcb6b8eef07bb92a19f4ca5963`;
tracked worktree initially clean, remote divergence 0/0. Report
`docs/arcana/INT2C_C3_EXECUTABLE_R4_REPLAY_CLOSURE.md`, SHA256 `462dff6628bed482b23b9e8be815239ba53008b5ef11853f59a073e4f6538c6d`.

Imported `outputs/r6_functional_development/INT2C_C3_REPLAY_20261014_01/` verified
independently on Windows: exact 21 manifest members + manifest, 22 files / 143,807
bytes; manifest `da913ccef5850ae943afadfd90672853db9d1b625eed2ebcc2d508fc599a2852`.
Complete computed state and both original per-support payload digests match R4
exactly; B0 result VERIFIED, zero mismatches. Both supports have 73 nodes and
finite payloads. Eleven typed records, 16-file/78,945-byte C2 read copy, committed
view membership, recorded configuration, twelve source hashes and original R4
inventory reconcile. No HistoryStore constructor or real kernel was run locally.

Authenticated SUPERVISION record: natural child exit 0, 0.7619832679629326 s,
39,845,888 peak sampled process-tree RSS bytes, two samples, zero recorded
overshoot. Linux Python 3.12.10 / NumPy 2.3.5, original 1,000 years/fraction 0.0005.
One authorized genuine real-kernel replay/no retry is operator-reported and
consistent with the imported command/result. Parent log digest and Linux
28 PASS / 1 expected SKIP are OPERATOR_REPORTED, not independently rehashed.
Local focused regressions: 52 PASS, 6 Linux SKIP/NOT_TESTED_WINDOWS; no repeat replay.

This closes only the existing R4 engineering trajectory, forcing, kernel/source
binding and tested Linux runtime. Original C2/R4/INT-1D/history and checkpoint
statuses preserved. No general scientific validity, universal cross-platform
identity, physical refinement, INT-1D executable replay or canonical readiness.
STOP after closure; no further execution or workstream is authorized.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Historical INT-2C-C3 — supervised Linux launcher ready, real replay pending (2026-10-14)

Decision: `INT2C_C3_SUPERVISED_LAUNCHER_READY__REAL_REPLAY_PENDING`.
Entry `7ebbccfa136056b2467ece43fbb7fde51748c531`, clean tracked worktree/index.
Report `docs/arcana/INT2C_C3_SUPERVISED_REPLAY_LAUNCHER_PREFLIGHT.md`, SHA256 `ec49f8e894692c79467f44f32bdd73d109ed9af705ca7cfd93c106ecbcb4c2a6`.
Added one CLI and targeted tests; no changes to adapter, attestor, B0 or kernel.
Default preflight never dispatches the kernel. Numerical CLI mode additionally
requires --execute-authorized, which acknowledges separate operator approval;
it does not grant authority. No real R4 kernel or Fair command executed here.

The existing C2 store is read and byte-copied to fresh evidence before current
HistoryStore is opened, protecting the original from constructor metadata/recovery.
All eleven typed records and fixed checkpoint/recipe IDs must match authenticated
R4 preparation; validate_replay_inputs precedes genuine execute_replay. A transparent
wrapper retains independently computed values; full B0 state and both historical
per-support payload hashes are fixed acceptance targets. Mismatches remain evidence.

Linux monitoring uses /proc PID/executable/start ticks and process-tree RSS,
900 s / 2 GiB / 512 MiB sampled thresholds, SIGTERM/SIGKILL termination, stdout/stderr,
exit status and manifest. These are monitored thresholds, not hard quotas.
Exact isolated Python 3.12.10 / NumPy 2.3.5 prefix required; no fallback. Source
commit/cleanliness and twelve loaded code files are checked against Git blobs.

Windows verification: 86 PASS, 6 Linux runtime tests SKIP/NOT_TESTED_WINDOWS,
1 existing Windows store-publication test deselected; py_compile PASS. Six
Linux supervisor cases must pass on Fair before final preflight/authorization.
C1/C2 remain OPERATOR_REPORTED; no independent Fair import/rehash performed.
Next: operator self-test and provider-free supervised B0 preflight with new paths,
then STOP for separate bounded authorization of one real R4 replay. Full candidate
runtime execution and Linux monitor proof remain pending; all historical evidence preserved.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Historical INT-2C-C1/C2 — Fair prerequisites reported; C3 pending authorization (2026-10-14)

Current decision: `INT2C_C1_C2_FAIR_PREFLIGHT_REPORTED__C3_PENDING_AUTHORIZATION`.
Consolidation entry Windows/GitHub HEAD `3d53ed80ea170d7b0b3d20b3fb4e40ff103a4daa`;
tracked worktree/index clean, no pending commits, remote divergence 0/0.
Report `docs/arcana/INT2C_C1_C2_FAIR_EVIDENCE_RECONCILIATION.md`, SHA256 `df21e291f3b4779fbee90235db0566f34a206261fb92ea67a88e30d64d97a75d`.

Operator-reported C1: isolated Fair Python 3.12.10 / NumPy 2.3.5, Conda install
exit 0, technical attestation PASS and eleven typed records; original checkpoint
remains CANDIDATE_NONCANONICAL, new checkpoint VALIDATED only for
TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY; checkpoint/recipe IDs reportedly match
Windows. Evidence locators: `INT2C_RUNTIME_CHECK_BXFon4Yd`, `INT2C_C1_zC7ONJo8`.
Operator-reported C2: atomic registration of 11 records, reopened-store and typed
readback PASS, validate_replay_inputs PASS; 16 files / 78,945 bytes; no real
numerical kernel execution. Evidence locator: `INT2C_C2_ljWdyPsq`.

C1/C2 files were not identified in the inspected local task paths. Fair outcomes
and hashes are OPERATOR_REPORTED, not independently imported/rehashed on Windows.
Local Windows technical records/manifest and all nine unchanged R4 bytes were
independently rechecked; this does not verify untransferred Fair content.
The historical INT-2C-B runtime blocker and report remain preserved. Full Fair
paths, tested commit, runtime binary identities and C1 digests remain UNKNOWN.
29 local focused INT-2C-A/B tests PASS, 0 FAIL, 0 SKIP; no new numerical execution.

Next: INT-2C-C3, one supervised real R4 B0 replay pending separate final
authorization/preflight, exact source/runtime/store binding and fresh evidence
paths. Persisted input closure does not demonstrate predicted numerical output,
physical validity or canonical authority.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Historical INT-2C-B — technical input closure; Fair runtime blocked (2026-10-14)

Decision: `INT2CB_BLOCKED_FAIR_RUNTIME_IDENTITY_MISMATCH`. Entry source
`f49de047ff560f707428b395b7373d46301fdee9`. Report `docs/arcana/INT2C_B_TECHNICAL_CHECKPOINT_RUNTIME_PREFLIGHT.md`,
SHA256 `35defa80a702d3adea30e3c307c8eb2666bb8b4c8b8023dc1c05780b75db025c`. R4's nine files and original identities were reauthenticated
and retained unchanged. New checkpoint/recipe are VALIDATED only in
`TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY`; no numerical validation or physical
promotion. Existing adapter/kernel/B0 contract unchanged.

Direct read-only SSH observation on Fair: Miniforge base Python 3.14.7 without
NumPy; existing `arcana-r6-linux` Python 3.12.14 / NumPy 2.5.3. Required Python
3.12.10 / NumPy 2.3.5 was not found in the inspected existing environment roots.
No installation, environment recreation, job or numerical replay occurred.
Do not infer global absence of another runtime or historical binary identity.

Final local attestation: `outputs/r6_functional_development/INT2CB_TECHNICAL_ATTESTATION_20261014_02/`,
three-member manifest SHA256 `8b172002968c9fcd7620d78b456054ac7ca0e7a9afa49f2f9e91ca81e9b1731d`.
The `_01` provisional preparation remains preserved. No outputs are committed.
63 offline tests PASS, 0 FAIL, 0 SKIP, 1 actual Windows store-publication test
deselected. Typed `validate_replay_inputs()` passed through a test reader only;
real transactional publication/reopened-store readback and numerical replay
remain unexecuted. Exact runtime check rejects both alternate Fair versions.

Next decision: either separately authorize exact-runtime provisioning, or
review an explicitly new binding for Fair 3.12.14 / 2.5.3 with its own source,
configuration, checkpoint/recipe identities and future numerical equivalence
against the unchanged R4 full-state and per-support payload oracles. No relaxed
runtime check, store-contract weakening, new scenario or execution authorization.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

Historical INT-2C-A priority: prepared a closed typed R4 replay binding and deterministic kernel adapter. Decision: `INT2C_EXECUTABLE_REPLAY_BINDING_CODE_READY__NUMERICAL_VALIDATION_PENDING`. The real derived checkpoint remains `CANDIDATE_NONCANONICAL`; no numerical replay or store publication was executed. Report: `docs/arcana/INT2C_A_EXECUTABLE_REPLAY_BINDING_PREPARATION.md`. INT-2B closure remains evidenced and was published by verified fast-forward to `6a719da728baa11c4a972195d357fde7c32d21b3`.

## COMPLETED PREPARATION — INT-2C-A R4 replay binding preparation (2026-10-14)
- Entry HEAD `6a719da728baa11c4a972195d357fde7c32d21b3`, parent `14208a1e4c4462414e571477a662ba3e06ca4a09`; tracked worktree initially clean. Preserved all pre-existing untracked evidence. Sandbox DNS failure was followed by an authorized network retry: remote `14208a1e` verified and INT-2B closure pushed normally.
- R4 nine-member bundle authenticated through the existing loader, manifest `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`. Exact original states, forcing, two checkpoints and recipe retained. The original checkpoint is not validated; original checkpoint/recipe dependencies differ and raw provider digests are not typed B0 dependencies. A new candidate checkpoint/recipe/provenance closes the typed inputs without changing B0 protections.
- Historical/current `functional_development.py` normalized SHA256 independently matches `bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542` at R4 execution commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`. Adapter binds complete initial states, source bytes, configuration, declared forcing and Python 3.12.10/NumPy 2.3.5. Historical runtime binary identity and cross-runtime equivalence remain UNKNOWN; known Fair Python 3.12.14 will fail the declared numerical runtime check.
- New 24 contract tests use a mock numerical kernel only. Combined INT-2C-A/INT-1A/INT-2A/INT-2B: 58 passed, 0 failed, 0 skipped, 1 deselected (actual store registration test). No B0 store publication was attempted on restricted Windows. `py_compile`, UTF-8/LF, references and diff checks recorded at closure. No new numerical evidence or checkpoint promotion.
- Report SHA256 `0f8d6e9d001d21d3073bea75d23600127bc30e0fc5bee2e1f57b4de9a326b6bc`; adapter SHA256 `3a44e797676ceac3a4764bdaa1311157f57910315ead3ea2e4aa20e740cfc11d`; tests SHA256 `b987756986212e0ca816d1d5e537ec4eea2940a022412d8a985c32787be6528b`.
- Next: review/technically validate the derived closure, resolve the declared replay runtime, and separately authorize one bounded R4 B0-integrated replay on a supported filesystem. Preserve executable replay, scientific and canonical gates as unqualified/unauthorized.

## COMPLETED CHECKPOINT — INT-2B Fair isolated B0 binding (2026-10-14)
- Fair-tested source commit: `14208a1e4c4462414e571477a662ba3e06ca4a09`. Imported result bundle: `outputs/r6_functional_development/INT2B_B0_BINDING_FAIR_20261014_01/`; decision `INT2B_NONCANONICAL_B0_STATE_QUERY_BINDING_EVIDENCED__EXECUTABLE_REPLAY_NOT_QUALIFIED`.
- Windows recalculated result SHA256 `287600535bf787a404d15b0ee383f51a651384b42b6ba58b4b0829b6d91713ee` (5,561 bytes), manifest SHA256 `64b7aad35f7c880ce39939ab3337c29153b1e37037859c3b0724b1193ecfd4ad` (587 bytes), and sidecar-file SHA256 `4746c87bc6d2bf1cbaf11ec253e3a29a7407f0eccd1349e6f95a2a7937f8eb30` (93 bytes). The manifest covers the result only. All 33 imported store files independently hash to a verified inventory totaling 163,086 bytes; all 28 state/provenance records match read-only reconstruction from the pinned inputs.
- Fair result records transactional publication, 26/26 state readbacks, two provenance records, 33 files/163,086 bytes, four query timings (88,782,369–89,818,730 ns), and the expected missing-time/support/ambiguous-query outcomes. Operator reports Linux hard-link PASS, B0 regression 85 PASS, and adapter exit 0. The Fair logs were not transferred, so these execution facts are not independently log-hash verified on Windows. The JSON has a stale `NO_B0_STORE_QUERY_PASS` limitation token contradictory to its success fields; original evidence is preserved and the discrepancy disclosed in the report.
- The Fair result's `volume=NTFS` is not accepted as filesystem identity because the tested adapter hardcoded that label. Hard-link PASS is separate; actual Fair filesystem type remains UNKNOWN. The adapter now detects filesystem type for future runs with a focused regression.
- Windows verification: default project Python 3.12.10 lacked NumPy and initially failed test collection. Using the already installed pytest 8.4.2 and workspace-provided NumPy 2.3.5 through a temporary `PYTHONPATH` (no package installation), the focused module completed 7 passed, 1 skipped. `py_compile`, `git diff --check`, UTF-8/LF and direct filesystem-helper smoke checks passed; the skip is the actual store/query test blocked by Windows hard-link denial.
- Persisted observation records are not diagnostic interpolation and neither establishes executable physics replay. The 4 checkpoint payloads deserialize only as reduced state; replay remains unqualified. The original Windows `WinError 5` attempt remains a valid historical result for that environment. No canonical history or scientific inputs were changed.
- No new evolution, Solver, ShellSet, MPI or `WORLD_HISTORY` access/publication occurred in this consolidation. Scientific and canonical gates remain unchanged.

## CURRENT CHECKPOINT — INT-2A historical query/reconstruction (2026-10-14)
- Checkout: `r6/si1-bandwidth-f2av`, HEAD `5874f6e161aa086f4adbc53647960052ef7e6bf3`. R4 and INT-1D source bundles were each read-only verified for exact nine-file membership, externally pinned manifest/member sizes and SHA256, provenance and rung-specific endpoint binding. Their numerical execution commits remain `91fc83d50ec15d8bb9b826926ac2f2dc859281e8` and `3fa149b7639f59c934a4d722acb388eacc4c9628`.
- Decision: `INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION_EVIDENCED__B0_EXECUTABLE_BINDING_NOT_QUALIFIED`. INT-1A validation/interpolation/retention functions are reused. The two supports within each experiment have identical numerical histories and were not treated as independent.
- Final output `outputs/r6_functional_development/INT2A_HISTORICAL_QUERY_20261014_07/`: result SHA256 `e12c139ddc85d9a29a4edd5bcd03e080b35237df3e03382e5b46e0d0614c849f`; output manifest SHA256 `b613c94c95c41df503abf0a83ed26f817e00ea6de52822b436152cdc1d84b33d`; sidecar file SHA256 `b848dd1d786780714dc20df659d61c8a71fb4056558aaf497b9087b38474af6b`. Three-file membership/readback verified. Previous trial outputs from implementation/test iterations remain untracked and are not the final result.
- Tests: INT-2A + INT-1A focused suite 27 passed; py_compile passed. B0 core/query regression attempt produced 28 passed and 9 failures at existing `HistoryStore` setup because Windows denied the existing `os.link` immutable-write operation (`PermissionError WinError 5`); no B0 code was changed. This platform limitation is not a query-code PASS.
- Temporal interpolation is approximate diagnostic output, not physically evolved state. No general/online retention policy, B0 executable state binding/replay, scientific mechanics or canonical state was qualified. No Fair/MPI/ShellSet/Solver/evolution or `WORLD_HISTORY` access occurred.
- Next bounded work proposed: INT-2B, a minimal noncanonical B0 query adapter contract/prototype with isolated-store tests; this does not authorize canonical writes or executable replay.

## CURRENT CHECKPOINT — INT-1D distinct-boundary trajectory (2026-10-14)
- Source branch/commit: `r6/si1-bandwidth-f2av` / `3fa149b7639f59c934a4d722acb388eacc4c9628`, parent `54c0cce119da9e061545792840f9b7c430159c7c`. Final-source provider audit passed for explicit boundary `R6BND-T0-27e4d497530e681071fb`, pair 5:11, two admitted `CONTINENTAL_NORMAL` supports (`R6G1D-R094-C026`, `R6G1D-R094-C025`), 73 nodes per profile; source-composite identity `a1a4503fe57206750884e454d8a12d778caee38e34b35586805241ad51c01954`.
- One local supervised execution completed naturally, exit 0, in 24.314529 s. PID 37920; peak sampled process-tree working set 173,670,400 bytes; final monitored output 821,761 bytes. Sampling interval 100 ms. Thresholds (900 s, 2 GiB, 512 MiB) were not reached and are monitored thresholds, not OS-enforced quotas.
- Candidate bundle `outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02/`: exactly nine files; manifest SHA256 `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`; all recorded sizes/hashes and cross-file endpoint bindings passed. Nine samples/support at 0, 129.571922625, 259.160041740, 388.764359371, 518.384877540, 648.021598275, 777.674523600, 907.343655540 and 999.9999999999998 years. Finest diagnostic endpoint matches the 0.000125 convergence state; the 0.0005 checkpoint matches its separate trajectory state.
- Per support: width +106.9407427242 m; crust -33.7324888783 m; lithosphere -130.1110285306 m; maximum temperature node change 0.0218113170 K. All temperatures finite; area-relative error max 1.2745363551e-16. Replay/restart hashes reconcile; restart-vs-uninterrupted max temperature difference 2.0189929728e-7 K per side.
- Offline INT-1A evaluator revalidated R4 (manifest `191ee97a…`, 4 samples/support) and evaluated INT-1D (9 samples/support). Endpoint-only JSON subset sizes: R4 58,905/85,583 bytes, INT-1D 60,347/157,705 bytes. One-interior retrospective selection reduces omitted-state errors but uses the complete trajectory; it is not online-policy evidence. Between-case differences combine support/material and forcing, so no single physical cause is inferred.
- Decision: `INT1D_DISTINCT_BOUNDARY_TRAJECTORY_EVIDENCED__GENERAL_RETENTION_POLICY_NOT_QUALIFIED`. The earlier `_01` launch failure remains preserved as a historical failure. No Fair/MPI/ShellSet/Solver/DGBSV or WORLD_HISTORY publication; no scientific or canonical promotion. Full hashes and metrics: `docs/arcana/INT1D_EXECUTION_REPORT.md`.

## HISTORICAL CHECKPOINT — INT-1D provider preflight blocked (2026-10-13)
- Requested boundary `R6BND-T0-27e4d497530e681071fb`; branch/HEAD were `r6/si1-bandwidth-f2av` / `ffeb02e90abc4c3a542ac9a794c57ee8496b211b`.
- Environment had Python 3.12.14 and NumPy 2.3.5, but no configured `ARCANA_EXTERNAL_ROOT`. The read-only provider audit stopped at missing `CANONICAL_T0_PHYSICAL_PAYLOAD`; provider hashes, boundary eligibility and HEAD-dependent source-composite identity were not verified.
- No evolution, supervisor run, candidate directory creation or new numerical evidence. Existing R4 evidence was preserved. The conditional authorization is not consumed by a numerical run, but preflight failure means it cannot be exercised until governed inputs are found and revalidated.
- Scientific/canonical gates are unchanged. No Solver, mechanics qualification, or `WORLD_HISTORY` production is authorized.

## HISTORICAL CHECKPOINT — INT-1C code-ready distinct-regime preparation (2026-10-13)
- Added an exact boundary selector while preserving the prior lower-median default, and runner options for appending factor 0.000125 and explicitly sampling that rung. Checkpoint/trajectory/replay reference remains the original 0.0005 rung; 0.00025 remains in the ladder for same-resolution comparison with R4.
- Existing R4 edge matrix SHA256 `d89bd4d9cca8928f8e6b913ad6bf1955c429ac2e2e1bb4dc6b6263f7165a59c7` records `R6BND-T0-27e4d497530e681071fb`, pair 5:11, supports `R6G1D-R094-C026` / `R6G1D-R094-C025`, admitted extension, no junction, Ux `0.10694074272424924 m/year`. Both profiles were re-materialized locally: 73 nodes each, 35/135 km crust/base, q=0.06 W/m² and matching B6N8-N material tuples. This is not a fresh full provider audit: external root is unset, so candidate HEAD provider/source-composite identity is UNKNOWN pending immediate preflight.
- Read-only initial estimates: width `110852.14113381179 m`; 0.000125 initial kinematic step `4088978905.43 s`; explicit thermal bound `952777777777.78 s`; about 8 substeps and 9 samples/support projected, not observed. Candidate and supervisor destinations are absent. R4 measurements are reference observations only; operational thresholds are not hard quotas.
- Focused offline suite: 87 passed; two external-payload tests deselected. No new evolution or output. Full details and remaining conditions: INT1C report.

Current priority: INT-1B has defined one evidence experiment using the existing provider-backed pair-5:11 normal continental boundary and a finer integration rung. Decision: `INT1B_NEXT_EVIDENCE_EXPERIMENT_DEFINED__EXECUTION_NOT_AUTHORIZED`. No new evolution was run. Full report: `docs/arcana/INT1B_EVIDENCE_DENSITY_AND_DISTINCT_REGIME_DESIGN.md`.

## HISTORICAL CHECKPOINT — INT-1B experiment design (2026-10-13)
- Revalidated the existing R4 nine-file bundle against its manifest and R4 provenance with the offline INT-1A verifier; candidate-manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`, numerical-sample SHA256 `ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad`. The 12 INT-1A tests pass.
- Four samples/support arose from initial + three completed numerical substeps at the middle factor `0.0005`; observer runs on each substep, not on fixed intervals. Only two unique interior times exist and support series are identical. They cannot establish online/event retention or a general policy.
- Selected a distinct audited eligible pair-5:11 candidate `R6BND-T0-27e4d497530e681071fb`: two admitted `CONTINENTAL_NORMAL` cells, 35 km crust, 135 km reference lithosphere, q=0.06 W/m², edge-specific Ux=0.10694074272424924 m/year, no junction adjacency. Full candidate profiles/material tuple must be re-materialized and checked before any future run. This is a provider-supported thermal/geometric contrast, not a demonstrated composition or physical causal contrast.
- Proposed one noncanonical 1,000-engineering-year run with the same T0 initializer, pair 5:11, existing kernel and boundary rules; preserve factors 0.001/0.0005/0.00025, add 0.000125, sample every step on that finest factor, and bind checkpoint/replay to the same factor. Narrow runner boundary selection and fresh provider preflight are prerequisites. Actual sample count and resource use remain unknown.
- B0 replay remains `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`; INT-0B R4 same-kernel restart evidence is not executable HistoryStore replay. No provider-backed execution, Fair, MPI, ShellSet, Solver, or WORLD_HISTORY activity occurred. Preserved gates include `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## HISTORICAL CHECKPOINT — INT-1A empirical retention baseline (2026-10-13)
- Source remains R4 run commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`, source-composite identity `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`; candidate-manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`. The nine-member source bundle was rehashed and provenance/cross-artifact endpoint, checkpoint and replay identities reconciled.
- Output: `outputs/r6_functional_development/INT1_RETENTION_20261013/FINAL/`; analysis-manifest SHA256 `ad2bc118c4c7a15d56a87a3056b4d16ddedcf410f7a65a89c782d8ba41b522ce`; metrics SHA256 `7915d6786d31be3b9d6b7ea19568dbe1982cea87b561bed309d6a9de38430096`; storage CSV SHA256 `47e789aa247b9d06db06f3efea2f5cf77a0d12afebbfcbe491daeecb3dc2931f`. Full diagnostic JSON 85,583 bytes; paired initial/candidate checkpoint 83,624 bytes. Endpoint-only subset 58,905 bytes; one-interior subsets 72,233/72,261 bytes. These are JSON artifact sizes, not HistoryStore/RSS costs.
- Both supports have four samples at 0, 484.6791203689449, 969.6005802980742, 1,000 years. Two distinct interior times only; supports' observed numerical series are identical. Retrospective adaptive selection chose the first interior record and is not an online policy. Error values and field classes are in the INT-1A report/metrics; no tolerance or canonical retention policy was selected.
- Verification: 12 INT-1A synthetic tests PASS. Existing T-F2B sample/INT0A suites could not collect because NumPy is unavailable in the active Windows Python; no dependency was installed. py_compile and diff checks are reported with this checkpoint. Initial and intermediate output folders from this same audit remain preserved; `FINAL/` is the reviewed result.
- B0 replay remains descriptor-only; WORLD_HISTORY was not accessed. Preserved gates: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. Further generalization needs a separately authorized trajectory with denser observations and a distinct regime.

## CURRENT CHECKPOINT - INT-0B-R4 fourth noncanonical attempt completed (2026-10-13)
- Source: branch r6/si1-bandwidth-f2av, HEAD 91fc83d50ec15d8bb9b826926ac2f2dc859281e8, parent 50fbf6dfe1b8068a243ffa60df9ef22e1f5d6876. The source-bound provider audit passed on this HEAD; source-composite SHA256 b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca; Python 3.12.10 / NumPy 2.3.5.
- Decision: CONTINENTAL_ENGINEERING_SLICE_PASS. Candidate bundle outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/; manifest SHA256 191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236. All 7 manifest members and RUN_RESULT passed size/hash reconciliation; the directory contains 9 expected files. Both supports have four finite, strictly ordered samples, matching the 1,000-year endpoint and trajectory. Replay/restart and numerical refinements were checked.
- Supervisor: natural exit 0, 20.633493 s, PID 39408, peak sampled process-tree working set 164,384,768 bytes, final cumulative output 691,140 bytes. Peak sampled output was 0 because final artifacts appeared after the last nonzero sample. Limits were sampled operational thresholds, not OS-enforced quotas. Captured stream lengths and hashes match the supervisor summary.
- Earlier _01-_03 failures remain historical failures. The result is noncanonical engineering only; B0 replay remains descriptor-only and physical/temporal validity is not established. WORLD_HISTORY was not accessed or mutated according to the run record; no canonical publication occurred.
- Next: INT-1 empirical state-retention/reconstruction analysis on the existing trajectory, without another run. Preserved gates: BLOCKED_F2AV_QUALIFICATION, OPERATOR_CLASS_UNVERIFIED, THRESHOLD_UNJUSTIFIED, RESOURCE_2GB_SCOPE_UNRESOLVED, F2B_SOLVER_EXECUTION_AUTHORIZED=false, ARCANA_SI1_MECHANICS_QUALIFIED=false, WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.

## CHECKPOINT — INT-0B-R4 validazione sintetica e preparazione offline (2026-10-13)
- Entry baseline: branch `r6/si1-bandwidth-f2av`, HEAD `f2bfefce7e90d055ad44019ff3bf55cf7ebfe506`, parent `dfceb480554549ae363927f32451dfb2b2e9d72e`; tracked worktree pulito. Gli output storici erano untracked e sono stati preservati.
- Aggiunta una singola regressione end-to-end `SYNTHETIC_FIXTURE_ONLY` che collega kernel, observer, validatore R3, documento campioni, replay/restart, trajectory, writer produzione, manifest-last e verifiche readback/hash/membership; rifiuta endpoint corrotto e overwrite.
- Il writer produzione del runner ora verifica byte count e readback di ciascun artefatto, `RUN_RESULT.json` e manifest prima di dichiarare il completamento; il manifest resta ultimo. Il supervisor redirige stdout/stderr a file raw, riporta dimensioni/SHA256 e conta i log nel limite output campionato. Self-test esercita stderr su exit nonzero e stop da volume stdout.
- Suite mirata finale: 70 PASS, 0 FAIL, 0 SKIP; Python 3.12.10, NumPy 2.3.5. `py_compile` sui moduli/test Python, SelfTest PowerShell effettivo, UTF-8/LF e `git diff --check` PASS. Il provider audit read-only è stato poi eseguito sul commit R4 finale `50fbf6d`, source-composite SHA256 `c20e45ec398e331ae423e63d9387a53d8659a47a5a2bd8efa3b9ea1d17b808d4`; nessuna evoluzione eseguita.
- Stima sintetica schema: 12 campi intermedi, 22 endpoint; cap 10.001/supporto, 20.002 record; endpoint completo contiene 518 valori numerici rispetto ai 226 di un record intermedio. Proiezione serializzata stress conservativa per il campione circa 171.1 MiB; resta una proiezione, non output o RSS misurati. Preflight storico più pessimista 333.657.599 byte rimane sotto il budget monitorato 512 MiB, con circa 203.2 MB residui per altri output/log; il totale reale è ignoto.
- Destinazione proposta `_04` e cartella supervisione `_04` risultavano assenti e non sono state create. Configurazione 5:11, T0 210 Ma, 1.000 anni engineering, forcing/kernel/risoluzioni invariati. Quarta esecuzione: `PENDING_SEPARATE_AUTHORIZATION`; INT-1 resta bloccato.
- Nessun accesso o mutazione di WORLD_HISTORY, nessun provider-backed run, ShellSet, MPI, Solver, DGBSV o post-rift evolution. Gate invariati.

## CHECKPOINT — INT-0B-R3 correzione diagnostica offline (2026-10-13)

## CHECKPOINT — INT-0B-R3 correzione diagnostica offline (2026-10-13)
- Codice aggiornato: observer campiona l'intero `ReducedState.payload()` con `support_id` ed `elapsed_years` derivato; schema campioni V2. Runner verifica supporti, tempi, cardinalità, trasformazioni derivate e uguaglianza esatta di tutti i campi endpoint. Nessun cambiamento a equazioni, forcing, risoluzioni o parametri.
- Test aggiunti riproducono il vecchio primo mismatch (`elapsed_years` assente dal payload finale) e verificano il nuovo helper sul medesimo `ReducedState`; test di alterazione coprono ciascun campo fisico/state, support ID, tempi, cardinalità, derivati e diversa risoluzione.
- Il supervisor gestisce la race processo-terminato/snapshot senza root distinguendola da perdita d'identità reale, aggiunge `termination_classification` e corregge la label futura in `INT0B_R2_THIRD_FINAL_ATTEMPT`. Self-test subprocess sintetico copre exit naturale e processo ancora vivo.
- Suite offline: 62 PASS, 0 FAIL, 0 SKIP; nessuna evoluzione provider-backed eseguita. I byte in-memory del precedente tentativo non sono disponibili; non si afferma che siano stati ispezionati o che il run precedente sia stato validato.
- Nessun quarto run autorizzato; INT-1 bloccato senza una traiettoria completa. Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## CHECKPOINT — INT-0B-R2 terzo tentativo autorizzato, errore endpoint (2026-10-13)
- Unico tentativo finale autorizzato sul branch `r6/si1-bandwidth-f2av`, HEAD `311550d4402f6c2fac422eac1c7f1eed46c58c64`, parent `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`. Il provider audit è stato ripetuto sul medesimo HEAD attraverso il processo figlio sanitizzato: source-composite SHA256 `a19070287adedb0bb009ce5c56380892ca173d4eee30b662c6c1a7d34406b34a`, coppia 5:11, boundary `R6BND-T0-3eb57747e6f0a3f3305f`, supporti ammessi `R6G1D-R091-C029` e `R6G1D-R091-C028`, 73 nodi di profilo per lato.
- Il runner è stato avviato una sola volta con configurazione approvata e output `_03`. Dopo 22.190863 s, PID 33688, 194 campioni di monitoraggio (100 ms), picco working set del tree 151,773,184 byte, output 0 byte, il runner è terminato con exit 1: `DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH:R6G1D-R091-C029:0`. Nessun limite operativo è stato raggiunto. La destinazione numerica `_03` non è stata creata; replay, report, manifest e controlli finali non sono stati prodotti. Il calcolo numerico in memoria è avvenuto, ma non è una traiettoria persistita/validata.
- Il run summary contiene stale label `INT0B_R1_SINGLE_ATTEMPT` e stop_reason `MONITOR_ROOT_IDENTITY_LOST`. Il record NDJSON mostra il processo fino al penultimo polling; il dato è coerente con exit naturale fra il controllo `HasExited` e lo snapshot successivo. Exit code 1 è conservato. Trattare il motivo di stop come errore del monitor, non causa del runner. Hash locali summary `b699666d0c5e33db350b02404b544065f57fda290f49d0721011be02f475a271`, NDJSON `7c2812bbda0daa38d8c228555737c662fb07e385a185984d87391bb01d3ea993`; report INT-0B dettagliato nel documento citato.
- Esito: `INT0B_R2_THIRD_ATTEMPT_FAILED_DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH`. Nessun retry, nessun quarto tentativo, nessuna promozione o accesso/modifica canonica dimostrata. INT-1 bloccato. Next: riproduzione sintetica offline dell'endpoint mismatch e test/correzione minimale della race e label del supervisore; qualsiasi nuova evoluzione richiede distinta autorizzazione.

## CHECKPOINT — INT-0B-R2 correzione d'isolamento (2026-10-13)
- Il difetto R1 era nel processo figlio: `r6-env.ps1` caricata dal supervisor impostava `GIT_OBJECT_DIRECTORY` e `GIT_ALTERNATE_OBJECT_DIRECTORIES`. `ProcessStartInfo.Environment.Remove` ora rimuove solo tali variabili immediatamente prima del lancio Python; `PATH`, `PYTHONPATH`, `ARCANA_EXTERNAL_ROOT` e altre variabili Git non correlate sono conservate.
- Il primo audit R2 ha inoltre rivelato un refuso nel percorso esterno (`corsiiuu`); il supervisor ora deriva `_ARCANA_EXTERNAL_SOURCES` dalla root del checkout e verifica il payload fisico richiesto. Provider audit PASS sul commit finale `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`, source identity `7438690f5b7d59b1ab0177a0ac270deb188fcfc233308131da6d6515998461bd`; gli input/provider SHA sono elencati nel rapporto R2 e nell'audit JSON.
- Self-test sanitizzato PASS: Python 3.12.10, NumPy 2.3.5, Git repository/HEAD/commit verificati nel processo figlio; 41 test offline PASS, `py_compile` e `git diff --check` PASS. Il test verifica anche process tree, limiti campionati, terminazione e propagazione dell'exit code; non sono limiti OS hard.
- Proposta `_03`: `outputs/r6_functional_development/INT0B_TF2B_5_11_R2_20261013_03`, verificata assente. Configurazione 5:11, T0 210 Ma, 1.000 anni engineering, forcing Euler congelato, kernel e risoluzioni precedenti invariati; limiti 900 s / 2 GiB tree working set / 512 MiB output. Nessun run avviato. Attendere separata autorizzazione; output `_01` e prove di fallimento `_02` conservati.

**Base da riusare:** B0 HistoryStore/query/replay, B6K geometria candidata, B6N8-A diagnostica/vista temporale, PRE_ORBDATA/B6N8-O/Q, T-F2B cinematica e termica per coppia **5:11** con forcing ingegneristico congelato per 1.000 anni e replay/restart, upstream ShellSet/OrbData Fair solo nel proprio scope. Rift B6 **1:3** distinto da T-F2B; B6N5 non qualifica la continuazione fisica. B6N8-R roster reale termico ancora incompleto. pyGPlates mapping canonico non qualificato non blocca la prima integrazione con forcing Euler già presente. B6M-R1 documenta un precedente blocco T1, B6N8-A successivamente riporta due epoche geometriche visibili: verificare live view in sola lettura prima di qualsiasi nuova asserzione.

**INT-0A:** test sintetici/offline mirati 20 PASS; nessun run provider-backed o nuovo output. La traiettoria è descritta con record B0 tipizzati in staging, non registrata in `HistoryStore`; il replay è un descriptor non ancora chiuso/eseguibile tramite il servizio B0. T-F2B 5:11 resta un esperimento ingegneristico; B6 rift 1:3 è distinto. `W3C_C_REVIEW_REQUIRES_TARGETED_CORRECTIONS` resta valido come filone parallelo. W4 codec/scala, stop MPI-wide, `dt2` fisico e tutti i gap F2A-V restano aperti.

**Gates invariati:** `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## CHECKPOINT — INT-0B-R1 second authorized attempt (2026-10-13)
- Decisione: INT0B_R1_SECOND_ATTEMPT_FAILED_PRE_OUTPUT_VALIDATION_GIT_OBJECT_ENV_REINSERTED. HEAD 4cc7a78d95ee7e529394173933817a7266db251d, parent e95c7dbf281ede5312512654262b9925fa87eb02. Il provider audit diretto sul commit finale è passato con identità composita c30510e3b743954fd10385f02a6c282448843247db69e1da26de5ae22ac7a25d; runner/test identities e Python 3.12.10/NumPy 2.3.5 corrispondevano.
- Il processo Python 31248 è terminato naturalmente con exit 1 dopo 0.951220 s; supervisore foreground, 7 poll da 100 ms, picco working set del tree 48,848,896 byte e output 0. _02 è rimasto assente; nessun campione, traiettoria o manifest numerico è stato scritto.
- Causa riprodotta: il supervisore ha caricato r6-env.ps1, che ha impostato GIT_OBJECT_DIRECTORY e GIT_ALTERNATE_OBJECT_DIRECTORIES verso store estranei al checkout. Il runner ha fallito nel source identity query di R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json. Lo stesso git rev-parse fallisce con quelle variabili e riesce dopo averle rimosse. Il provider audit precedente era stato eseguito dopo unset; il figlio del run non lo era.
- Self-test supervisor PASS su process tree sintetico e stop campionati per wall-time, working set e output, più propagazione exit code. Soglie 900 s/2 GiB/512 MiB restano monitorate, non limiti OS. Dettagli e hashes: docs/arcana/INT0B_R1_SECOND_ATTEMPT_FAILURE.md e outputs/r6_functional_development/INT0B_R1_SUPERVISION_20261013/.
- Nessun retry o terzo run; INT-1 non avviato. Nessuna evidenza di accesso/modifica a WORLD_HISTORY. Gate scientifici, F2A-V e Solver invariati.

## CHECKPOINT — INT-0B-R1 offline correction (2026-10-13)
- Baseline locale: `e95c7dbf281ede5312512654262b9925fa87eb02`; correction candidate mantiene quel commit nella lineage. Modificati soltanto il controllo diagnostico e il test mirato; report e cinque documenti operativi registrano l'esito.
- Estratto `_validate_diagnostic_sample_sequence()` chiamato dal runner: confronta la sequenza completa con `zip(times, times[1:])`, rifiuta valori malformed/non finiti, tempi non strettamente crescenti e stato endpoint incoerente. La regressione valida a tre campioni fallisce con il vecchio `zip(times, times[1])` e passa con la correzione.
- Test runner/INT0A/functional-development: 40 PASS, 0 FAIL, 0 SKIP con Python 3.12.10/NumPy 2.3.5. Provider audit read-only ripetuto sul checkout `e95c7dbf`: PASS; identità provider invarianti; `source_identity` composita include HEAD e quindi va ricalcolata sul commit corretto.
- Prova sintetica supervisor: processo Python e figlio identificati, working set letto, limite output monitorato, `.Kill(true)` ha terminato entrambi, exit code naturale 23 propagato. Output osservato 81,920 byte a soglia 65,536 per overshoot del polling. CIM parent inspection negata; nessuna PID/image del run storico conservata, perciò il suo picco di 4,509,696 byte resta non corroborato.
- Directory `_02` verificata assente. Nessun run eseguito. Le soglie 900 s / 2 GiB / 512 MiB restano stop operativi campionati, non limiti OS hard. Report `docs/arcana/INT0B_R1_RUNNER_CORRECTION.md`.
- Next: ottenere autorizzazione separata e rieseguire tutte le verifiche immediate sul commit finale prima di considerare la singola esecuzione proposta. Failure directory `_01` e gates scientifici/esecutivi restano invariati.

## CHECKPOINT — INT-0B attempt (2026-10-13)
- Local branch/HEAD/parent matched the authorized published source identity; tracked worktree was clean before run. The repeated provider audit passed on HEAD `683230f5e66397478642c2b8a48550eb1d00cca7` with the expected pair, support, and provider identities. Python 3.12.10 and NumPy 2.3.5 were confirmed, and the destination was absent immediately before execution.
- One authorized execution, exact preflight command, no retry. Foreground PowerShell supervisor (250 ms sampling) recorded 25.427 s, exit 1, peak sampled working set 4,509,696 bytes, output bytes 0, 97 polls. Process-tree kill via `.Kill(true)` was tested on a harmless process; no kill was needed in the run. These are observations, not enforced OS quotas.
- Failure at runner line 114: `zip(times, times[1])` passes a float as the second iterable and raises `TypeError`. No candidate artifacts/manifest, endpoint/replay-restart result, or numerical findings were persisted. Only failure evidence was created after process exit; no WORLD_HISTORY access/change.
- The single-execution authorization is consumed. Next: minimal source correction plus offline regression; seek separate approval before any new trajectory attempt. All scientific/Solver/canonical gates remain closed.

---

# CHECKPOINT STORICI — i precedenti NEXT/HEAD/verdetti sono riferiti alle evidenze del loro tempo, non alla priorità corrente

## F2B-N2C-W3-C-C — review avversariale offline (2026-10-11)
- Decisione: `W3C_C_REVIEW_REQUIRES_TARGETED_CORRECTIONS`. Report `docs/arcana/SI1_BW1_F2B_N2C_W3C_ADVERSARIAL_PROTOCOL_REVIEW.md`.
- Due controesempi riprodotti: `pure_call_sequence=2` passa `validate_decision()` con `DECISION_FROZEN`; `solver_dispatch_boundary()` rifiuta incondizionatamente e non consulta il latch, perciò le prove sul callback non attestano un gate FEM integrato. Inoltre `worker_rank=True` viene accettato come rank 1.
- Test offline: W3-C 21 PASS; W3-C + W3-B 43 PASS. I test verdi non chiudono questi gap perché non includono le sequenze contraddittorie. Nessun runtime MPI/Fair/ShellSet/Solver.
- Remoto non verificato: `git ls-remote` fallito per DNS GitHub; HEAD locale `68b423e96b95b2ccfbe769fcb6d635234616844e` è il perimetro della review.
- Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2C-W3-C-A — runtime authority e stop coordinato, design statico (2026-10-11)
- Decisione di design: `W3C_A_DESIGN_COMPLETE__RUNTIME_AUTHORITY_AND_MPI_STOP_UNPROVEN`. Rapporto: `docs/arcana/SI1_BW1_F2B_N2C_W3C_RUNTIME_AUTHORITY_AND_MPI_STOP_DESIGN.md`.
- Il call graph storico mostra coordinator rank 0 e worker nonzero (`ShellSetMain.f90:88-98,553-575`), dispatch per tag/`ModNum` (`:244-260,427-433`), cicli SH/SF (`:690-700,783-794`), `Pure` → FEM (`MOD_Shells.f90:6940,6996-7010`) e `BuildF/BuildK/AddFSt/VBCs` → Solver (`:3707-3734`). Questi sono produttori di valori locali, non un'autorità completa di run/assignment/state.
- Il contratto SI1 diagnostico non fornisce il provider owner-backed run/attempt/modello/assegnazione richiesto. Restano UNKNOWN: identità del run/job e del communicator, stable model/dispatch sequence, effective input/state/constraints, eseguibile collegato e processo eseguito, DOF ordering runtime, A0/b0 per invocazione e binding indipendente del payload. D1A resta `DOF_MAPPING_PARTIAL`; attribuzione geografica delle anomalie `DOF_MAPPING_UNVERIFIED`.
- Raccomandato un record CAPTURE_ONLY immutabile prima del dispatch, identico e ACKato da tutti i rank; dispatch singolo verso un worker e target limitato al primo FEM raggiungibile. Il job-wide latch nega Solver su ogni worker e ogni FEM. Coordinamento successo tramite stato terminale per rank e stop coordinator; guasto/timeout richiede fail-stop/launcher policy da provare sul runtime esatto. W2 `ERROR STOP 86` e test W3-B sintetici non provano MPI-wide termination.
- Nessuna modifica di sorgenti scientifici/lock e nessun test, compile, Fair, MPI o ShellSet in questo audit. Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- Prossimo gate proposto: F2B-N2C-W3-C-B, solo modello offline del record decisione e coordinatore; non autorizza overlay/runtime.

## F2B-N2C-W3-B — validator sintetico offline (2026-10-11)
- Decisione: `W3B_SYNTHETIC_OWNER_BINDING_VALIDATOR_PASS__RUNTIME_AUTHORITY_UNKNOWN`; implementazione isolata in `scripts/r6_si1_bandwidth_f2b_n2c_w3b_provenance.py` e fixture `tests/test_r6_si1_bandwidth_f2b_n2c_w3b_provenance.py`.
- Stato di pubblicazione: W3-B è già pubblicato nel baseline `2bb34525c4098eded5ee65eca02428c92d5c68b3`; B1 è la successiva riconciliazione semantica. `WINDOWS_WORKTREE_ONLY` è un'etichetta storica ormai obsoleta per W3-B.
- Identità tipizzate coprono run/attempt/job, processo/communicator/role, assignment/model, call SH/SF e sequence Shells/Pure/iter/FEM, input/state/constraints, source/build/executable, DOF e system A0/b0. Le evidence record sono esclusivamente sintetiche; UUID/SHA sintattici non sono autorità. Nessun provider di trust runtime è implementato.
- B1 separa assignment identity da FEM invocation coordinates: call distinte per una assignment master immutabile sono ammesse; coordinate ripetute falliscono anche se cambiano stato o digest A0/b0; riuso della sequence con model/worker/owner binding differente fallisce. Ciò segue `Pure` (`MOD_Shells.f90:6940`), che chiama FEM nel loop (`:6996`). La guardia di stato capture accetta soltanto esiti terminali tipizzati e rifiuta stati sconosciuti o già entrati in Solver.
- Riutilizzati decoder N2A e verificatore indipendente N2C contro l'oracolo sintetico. Rank 0 è ruolo coordinator valido, ma non worker FEM; `rpeat=0` è accettato soltanto per SF con `MaxIter=0`. Il coordinatore multi-worker resta simulato e non dimostra stop MPI-wide.
- Verifiche Windows offline W3-B + N2A + N2C writer + W2 overlay: **41 passed, 1 skipped, 0 failed**. Skip: writer runtime Fortran, `gfortran` predefinito assente. `py_compile`, UTF-8/LF e diff-check PASS; nessuna prova Fair/Fortran/ShellSet/MPI/Solver.
- Rapporto: `docs/arcana/SI1_BW1_F2B_N2C_W3B_OFFLINE_INVOCATION_BINDING.md`. W1 synthetic caps ancora escludono SI1; W4 scale/I/O resta separato.
- Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## W3-B1 — riconciliazione unicità invocation (2026-10-11)
- Esito circoscritto: `W3B1_SYNTHETIC_INVOCATION_UNIQUENESS_RECONCILED__RUNTIME_AUTHORITY_UNKNOWN`. La modifica copre validator, regressioni e report W3-B; aggiornato anche il ledger operativo.
- La ledger consente call FEM distinte per assignment master immutabile e rifiuta coordinate fisiche duplicate separatamente dai digest di stato/sistema/payload. Fixture negative coprono sequence riusata con model o worker diverso e mutazioni owner-backed dello stato/system che non mascherano coordinate duplicate.
- La capture gate applica la transizione terminale tipizzata `RETURN_BEFORE_SOLVER`; il caller sintetico verifica success/failure terminali e il rifiuto di stati sconosciuti/solver-entered senza invocare Solver.
- Suite richiesta W3-B/N2A/N2C/W2: 41 PASS, 1 SKIP (compiler-dependent Fortran test; `gfortran` unavailable on Windows), 0 FAIL. Nessuna nuova evidenza Fair. Gli output untracked preesistenti restano preservati e fuori staging.
- Il baseline W3-B già pubblicato è `2bb34525c4098eded5ee65eca02428c92d5c68b3`; B1 è il successivo delta semantico verificato in questo aggiornamento. Next: W3-C owner authority/runtime binding e coordinated-stop contract, offline/static only.

## F2B-N2C-W3-A — contratto identità/provenance reintegrato (2026-10-11)
- **Decisione:** `W3A_IDENTITY_CONTRACT_DEFINED__RUNTIME_BINDING_AND_MPI_WIDE_STOP_UNPROVEN`. Contratto integrale `docs/arcana/SI1_BW1_F2B_N2C_W3A_IDENTITY_PROVENANCE_CONTRACT.md`, SHA256 `6f94d4cbcda52eab351e1aa106bcd7d2c1c25f00b78834d2b2b7f3f8d41e2df9`. Recuperato dalla patch esatta del commit locale Windows `f6d0ff2f17547d530ae8a37145c94e788732ef2e` (parent `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`) e riconciliato sulla storia GitHub successiva W2 compile-only / E1.
- **Ambito:** audit dei sorgenti e contratto offline; nessuna compilazione/test nuova, linking, esecuzione ShellSet, MPI, Solver, accesso Fair o modifica ai source lock. W2/E1 preservati come risultati precedenti nei loro precisi scope: `N2C_W2_E1_FAIR_OPERATOR_REPORTED_INTEGRITY_PASS__RUNTIME_NOT_QUALIFIED`.
- **Riscontri:** `ModNum` è coordinata derivata da `MPI_TAG`, non identità modello stabile; `rpeat=0` ammesso nella chiamata finale SF con `MaxIter=0`; ordinale FEM W2 azzerato per ogni `Pure`. Rank 0 MPI valido ma coordinatore nel path storico. `ERROR STOP 86` è evidenza di flusso sorgente locale, NON di stop coordinato MPI-wide.
- **Ancora UNKNOWN:** binding owner-backed run/job/assignment/model, input e stato effettivi, vincoli, eseguibile/build, permutazione DOF, digest A0/b0 indipendente, verifica payload e comportamento multiworker. Non inferire identità da stringhe/hash presentati dal solo writer.
- **NEXT:** F2B-N2C-W3-B, prima implementazione/prove **solo sintetiche e offline**, isolate dall'upstream ShellSet; coordinamento MPI-wide è un requisito da progettare/testare separatamente, NON già provato. W4 codec e risorse SI1 resta distinto. Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2C-W2-E1 — checksum, manifest e oggetti Fair riconciliati (2026-10-11)
- **Decisione:** `N2C_W2_E1_FAIR_OPERATOR_REPORTED_INTEGRITY_PASS__RUNTIME_NOT_QUALIFIED`. Evidenza riferita dall'operatore Fair, non acquisita né rehashata autonomamente nel PC Windows. `sha256sum -c --status SHA256SUMS.txt` ha prodotto `CHECKSUM_EXIT=0` su 103 record; `MANIFEST_ENTRIES=103` e `ACTUAL_FILES=103` (auto-manifest escluso). Non sono state modificate le evidenze preesistenti.
- **Prove di struttura:** script read-only eseguito su Fair ha restituito `E1_SOURCE_AND_OBJECT_INTEGRITY_PASS`; `RESULT.txt`: commit sorgente previsto, bridge/full compile exit 0, linking/runtime dichiarati non eseguiti; JSON stdout builder uguale al manifest candidato; SHA256 source lock verificato contro file nel checkout; 15 membri candidati con SHA conformi; verificati writer, bridge, MOD_Shells, SHELLS_v5.0 e ShellSetMain; 14 oggetti candidati esatti e 2 oggetti bridge presenti.
- **Identità del run compilato:** commit sorgente `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`, MPI wrapper NVHPC 25.11, `nvfortran`, OpenMPI 4.1.9a1; `FAIR_EXTERNAL_EVIDENCE` in `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W2_COMPILE_ONLY/W2_NV_20261011T132801Z_juuO3l`. `bridge.log` è vuoto e ha SHA del file vuoto; `full_compile.log` non vuoto. Gli SHA riportati sono in `EVIDENCE_INDEX.md`.
- **Vincolo di autorità:** integrità locale attestata dall'operatore tramite console; non prova readback indipendente su Windows, linking, `mpiexec`, esecuzione FEM/ShellSet, stop runtime prima di Solver, autenticazione A0/b0, matrix SI1, qualificazione operatore o World History. Il `SOURCE_LOCK` originale resta invariato; `CAPTURE_ONLY` non autorizzato.
- **NEXT:** W3 — design/review offline del binding di identità e provenance autorevole, con casi negativi (rank MPI 0, digest, identity collision, incompletezza), sidecar e contratto d'integrazione. W4 codec e dimensionamento SI1 resta un gate distinto. Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. `RESOURCE_2GB_SCOPE_UNRESOLVED` permane.

## F2B-N2C-W2 — prova NVFORTRAN compile-only Fair (2026-10-11; evidence operator-reported)
- **Decisione di scope:** `N2C_W2_NVFORTRAN_COMPILE_ONLY_OPERATOR_REPORTED_PASS__RUNTIME_NOT_QUALIFIED`. Operatore Fair riporta marker `PASS_N2C_W2_NVFORTRAN_COMPILE_ONLY_CANDIDATE`; `BRIDGE_COMPILE_EXIT=0`, `FULL_COMPILE_EXIT=0`, `FULL_OBJECT_COUNT=14`, `EXPECTED_FULL_OBJECTS=14`. Non è una nuova prova runtime, scientifica, o di linking.
- **Identità:** checkout Fair dedicato `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV`, HEAD `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`; branch remoto con ledger separato. Ambiente Conda `arcana-r6-linux`, wrapper `/opt/nvidia/hpc_sdk/Linux_x86_64/25.11/comm_libs/mpi/bin/mpifort`, backend `nvfortran` 25.11-0, OpenMPI `mpiexec (OpenRTE) 4.1.9a1` (identificato senza MPI run). PATH inizialmente privo di MPI wrapper, poi aggiornato nella sola sessione.
- **Scope compilato:** builder W2 riuscito in nuova directory esterna al repo; writer e bridge in `build-bridge`, più 14 oggetti del call graph candidato in `build-full`, con `mpifort -c` e flag `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds -Mbackslash`. Il report della shell dichiara `LINK_PERFORMED=false` e `SHELLSET_MPI_SOLVER_RUNTIME_EXECUTED=false`. Nessuna modifica al codice canonico o ai source lock mediante questo passaggio.
- **Evidenza:** `FAIR_EXTERNAL_EVIDENCE` in `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W2_COMPILE_ONLY/W2_NV_20261011T132801Z_juuO3l`, comprendente `PREFLIGHT.txt`, `builder.log`, `bridge.log`, `full_compile.log`, `RESULT.txt`, `SHA256SUMS.txt` e `candidate/N2C_W2_CANDIDATE_OVERLAY.json`. Percorso e risultati riferiti dall'operatore tramite transcript; hash e byte dei membri NON trasferiti né ricalcolati indipendentemente. `SHA256SUMS.txt` è stato generato dal comando, ma il suo contenuto resta non acquisito.
- **Limiti:** oggetti compilati, non linked; nessun `mpiexec`, ShellSet runtime, FEM runtime, A0/b0 SI1, snapshot autorevole, Solver/DGBSV, benchmark o verifica scientifica. W3 identity/provenance e W4 codec/scala/I/O sono ancora bloccati; rank MPI 0 è legittimo ma il bridge candidato controlla `process_rank < 1`: verifica e correzione progettuale in W3, non dedurre dal compile PASS una corretta identità runtime.
- **Prossimo:** acquisizione mirata read-only di `RESULT.txt`, `SHA256SUMS.txt`, manifest e log già prodotti, senza ripetere la compilazione; in seguito W3 su Windows/Codex. Nessun nuovo job, esecuzione o modifica Fair implicita. Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2C-W2 — overlay candidato e trasporto Fair (2026-10-11)
- Decisione: `N2C_W2_CANDIDATE_OVERLAY_IMPLEMENTED__RUNTIME_CAPTURE_BLOCKED_BY_IDENTITY_AND_CODEC_BOUNDS`. Overlay builder, bridge Fortran, test e report committati come `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e` (parent `8645a48f7ca716c2e3c4b3cee087e7e6f7333262`), push GitHub e checkout Fair detached al medesimo SHA confermati.
- Windows W2: 13 passed, 1 skipped (compilatore Fortran assente); py_compile, UTF-8/LF, whitespace, diff-check PASS secondo report operatore. Compilazione W2 su Fair **non ancora eseguita**, così come nessun run ShellSet/MPI/Solver. Distinguere dal W1: 25/25 PASS GNU e 25/25 PASS NVFORTRAN, solo fixture sintetiche.
- Fair preflight: worktree dedicato `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV`, ambiente Conda `arcana-r6-linux`, Python 3.12.14, GNU Fortran 13.3.0, NVFORTRAN 25.11-0; CLI builder `--source-package` e `--output` rilevata. Warning `git-lfs` assente non ha impedito il checkout; non modificare hook alla cieca. Nessuna candidate directory o build-manifest generati nel preflight.
- Overlay verifica SHA256 fissato del source lock `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2`, tutti i 15 membri e parametro referenziato. Il commit vendored nel lock è un claim non attestato come oggetto Git. Il bridge porta ModNum, rank ThID da MPI_COMM_RANK, rpeat, iter e ordinale FEM locale al gate dopo VBCs e prima di Solver. Identità autorevole run/input/stato/build/DOF rimane UNKNOWN: CAPTURE_ONLY fail-closed; DEFAULT_OFF non autorizza run del Solver.
- SI1: n=128884, KL=KU=727, LDAB=2182, AB=281224888 elementi / 2249799104 byte. W1 limita n<=2048 e MAX_STORAGE=2000000 elementi **per fixture**, NON 2 GB RAM. Nessun limite RAM globale di 2 GB ratificato: riferimento richiesto dall'utente registrato `RESOURCE_2GB_SCOPE_UNRESOLVED`; nessun tetto arbitrario applicato. RAM libera Fair riportata ~512 GB non sostituisce la memoria effettivamente assegnata al job.
- Prossimo: generare copia candidata nuova fuori dal checkout tramite builder; verificare manifest/hash; compilare (compile-only) writer+bridge **e call graph candidato completo** con toolchain/flag realmente verificati. Niente esecuzione di eseguibili ShellSet, MPI, DGBSV, Solver o SI1. W3 identity e W4 scale restano gate distinti.
- Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2C-W1 — qualifica sintetica cross-compiler (2026-10-11)
- Decisione: `N2C_W1_SYNTHETIC_FORTRAN_CAPTURE_CROSS_COMPILER_PASS__SI1_INTEGRATION_NOT_QUALIFIED` per il writer standalone e le fixture sintetiche; GNU Fortran 13.3 e NVFORTRAN 25.11 hanno ciascuno 25 passed, 0 failed, 0 skipped sul commit testato `7a4119112a16e32c8cbdae5248ebd91f4020a458`.
- Gli esiti Fair e gli SHA dei log sono riferiti dall'operatore, non letti o ricalcolati da Codex Windows. I due run precedenti sul commit `57b2bd1f` restano 24 passed / 1 failed ciascuno; il failure era il cwd inesistente dell'harness, corretto in `7a411911` e poi superato dai rerun distinti.
- Questo PASS non attesta cattura post-VBCs reale, identity FEM/run/model/rank/input, autenticazione autonoma del digest nel writer, durabilità/atomicità, acquisibilità della matrice SI1, validità numerica/fisica o Solver.
- Prossimo gate proposto: F2B-N2C-W2, overlay candidato separato dal source lock, dopo aver risolto le cinque precondizioni descritte in `NEXT_ACTION.md`.
- Gate invariati: `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2B-V — interoperabilità sintetica GNU/NVFORTRAN consolidata (2026-10-11)
- Decisione: `N2B_SYNTHETIC_CROSS_LANGUAGE_INTEROP_PASS__SI1_CAPTURE_NOT_QUALIFIED`. I due esiti Fair sono riferiti dall'operatore; Codex Windows non ha letto né ricalcolato gli SHA dei log remoti.
- GNU Fortran 13.3.0: commit testato `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`; Conda `arcana-r6-linux`, Python 3.12.14, pytest 9.1.1; 21 passed, 0 failed, 0 skipped, exit 0. Log e SHA256 riportato `b7a953072d9b142a8836190454cccbebb5399f3fc8b71b50057c6998a94cf0ef` in `EVIDENCE_INDEX.md`.
- NVFORTRAN 25.11-0: commit testato `2d6021ff0036d350b12a583d9eff1d03e32a7239`; flag `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`; 29 passed, 0 failed, 0 skipped, exit 0. Log SHA256 riportato `b219f790e1c45369a55c12cf60a635d71068a05bda774e5a1577116cb02c945b`. La precedente attestazione NVFORTRAN di sola compilazione resta un record distinto e storico.
- Scope: fixture sintetiche, entrambi i versi writer/reader, controlli negativi, integrità bitwise e metriche rispetto a oracle indipendente secondo i test eseguiti. Il precedente skip locale Windows resta una fase storica; non è lo stato corrente dell'interoperabilità fixture.
- Non dimostrati: cattura A0/b0 del runtime ShellSet reale, identità di invocazione FEM/iterazione, snapshot SI1 durevole, budget memoria/I/O, qualificazione Solver o accettazione numerica/scientifica.
- Prossima azione storica, completata da W1: implementare la foundation sintetica N2C disabilitata per default. La next action corrente è F2B-N2C-W2, riportata nel blocco in cima e in `NEXT_ACTION.md`.
- Gate invariati: `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2B — stato preliminare prima del test runtime NVFORTRAN (storico; superato dal riepilogo N2B-V sopra)
- Esito GNU Fortran riportato dall'operatore: `N2B_SYNTHETIC_CROSS_LANGUAGE_INTEROP_PASS__SI1_CAPTURE_NOT_QUALIFIED`; commit testato `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`, ambiente Conda Fair `arcana-r6-linux`, Python 3.12.14, pytest 9.1.1, GNU Fortran 13.3.0; 21 passed, 0 failed, 0 skipped, exit 0. Log Fair dichiarato: `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_GFORTRAN/N2B_GFORTRAN_TEST_20261010T233835Z.log`, SHA256 riportato `b7a953072d9b142a8836190454cccbebb5399f3fc8b71b50057c6998a94cf0ef`. Il log resta su Fair: questa registrazione Windows non afferma di averne ricalcolato l'hash.
- Stato NVFORTRAN in quella revisione preliminare: `N2B_NVFORTRAN_FIXTURE_COMPILE_PASS` (solo compilazione; superato per lo scope runtime dal test sintetico successivo N2B-V), NVFORTRAN 25.11-0, exit 0, flag `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`; eseguibile Fair riportato `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_NVFORTRAN/build.NAyMuU/n2b_interop.exe`, SHA256 riportato `72aadbf9eb9c953816c8816bbe1050f1afdcc08302a3d1bb9313c3e022759719`. La fixture NVFORTRAN non è stata eseguita come interoperabilità Python↔Fortran.
- I risultati sono prove di fixture sintetiche e provengono dal resoconto dell'operatore Fair; non attestano cattura SI1, A0/b0 reale, assembly o qualifica numerica/scientifica. La compilazione NVFORTRAN non equivale a runtime PASS; non è stata dichiarata una verifica Windows indipendente dei file Fair non trasferiti.
- Prossima azione proposta: `F2B-N2B-V`, selezione esplicita del compilatore nel runner Windows (GNU Fortran o NVFORTRAN) con flag distinti, test/review e commit/push GitHub prima del fetch Fair e della prova NVFORTRAN runtime autorizzata per fixture. Nessun nuovo framework o formato.
- Gate preservati: `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2A-R1 — review tecnica dello snapshot sparso sintetico (2026-10-11)
- Decisione: `N2A_SPARSE_SNAPSHOT_SYNTHETIC_VERIFIED__SI1_INTEGRATION_NOT_QUALIFIED`. Review limitata al prototipo Python e a fixture sintetiche; non è una cattura o qualificazione di A0/b0 SI1.
- Confermati gli SHA256 del prototipo (`90c6707f48dcb1bec35097b25b9e0f317463d4a08d28d54c4611e3cebf463156`), test (`faf456601864b38da0c55d3496c84f62a3e2d14d280004156f66eeb9db9b9389`) e rapporto (`f9fb44697f2aea551f962ef35a2cbf0110abee8dee295a0575d6f9429d663520`). Suite snapshot + D3B numerica: 15 passed; py_compile, UTF-8/LF e diff-check PASS.
- La codifica round-trip preserva coefficienti binari64, subnormali e -0.0; +0.0 è implicito. Validazione rifiuta indici non validi, duplicati, record non canonici, non-finiti, padding/fill non nullo, lunghezza errata e digest incoerenti. Il digest interno controlla coerenza ricostruita, non autentica da solo l'assembly originale; il digest esterno deve essere ancorato indipendentemente e la cattura deve essere provata al punto corretto.
- Audit del sorgente storico: `FEM` esegue `BuildF`, `BuildK`, `AddFSt`, `VBCs`, poi `Solver`; `Solver` assegna solo parametri locali prima di `DGBSV`, che sovrascrive AB e RHS. Punto candidato: post-`VBCs`, pre-`Solver`/DGBSV, con identità per singola invocazione/iterazione. Nessuna modifica Fortran né esecuzione ShellSet/Solver.
- Gap: formato e prototipo non includono identità di invocazione/iterazione autorevole, non hanno writer durevole/streaming né prova NVFORTRAN/Fortran, e non qualificano memoria, I/O o identità del sistema SI1. Un diverso ordine di matvec può cambiare arrotondamenti; nessuna soglia numerica è derivata.
- Restano `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- Prossimo lavoro proposto: F2B-N2B, specifica offline del contratto d'integrazione/cattura (identità invocazione e iterazione, completezza, hash indipendente, scrittura e fail-before-Solver) prima di qualsiasi modifica Fortran o prova su SI1.

# ARCANA WorldSim R6 — Stato operativo corrente

## F2B-N1 / N1-T1 — precondizioni numeriche e isolamento sintetico (2026-10-11)
- N1 resta `N1_NUMERICAL_PRECONDITIONS_DEFINED__ACCEPTANCE_NOT_YET_ATTESTED`: il contratto di verifica A0/b0 e delle metriche è definito, ma non esiste una soglia numerica SI1 giustificata; `THRESHOLD_UNJUSTIFIED` permane.
- Il test T1 in `tests/test_r6_si1_bandwidth_f2b_d3b_numerical.py` (SHA256 `95c6bfe54f70f37f685dc1add355f9bb8d83b47e25500fba35ccdfe2eabdac3e`) ha esito `N1_T1_SYNTHETIC_DESTRUCTIVE_BUFFER_ISOLATION_PASS`: 9 passed, 0 failed, 0 skipped. Con matrice sintetica non simmetrica KL=1/KU=2, snapshot A0/b0 distinti e buffer operativi sovrascritti, le metriche sugli snapshot concordano con un oracolo denso indipendente; i buffer mutati producono metriche differenti.
- Il test dimostra soltanto il percorso sintetico. Non prova che ShellSet preservi A0/b0, non sceglie la strategia per il caso SI1 e non autentica la matrice storica o il runtime.
- Report N1 `docs/arcana/SI1_BW1_F2B_N1_NUMERICAL_ACCEPTANCE_PRECONDITIONS.md`, SHA256 `88790af7a35f0cb58568d7d69afd27664b5a2b1fdeeff5a4ef807dfcca87f978`; rimosso un blank line finale ridondante per `git diff --check`, nessun cambiamento semantico.
- Prossimo lavoro proposto: F2B-N2, scelta e qualificazione progettuale della strategia di preservazione del sistema lineare originale senza presumere memoria HPC disponibile. Nessun Solver autorizzato.
- Gate invariati: `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-D3D-RO6 — consolidamento evidenza Fair trasferita (2026-10-10)
- Attestazione trasferita: `outputs/r6_si1_bandwidth_f2b_d3d_ro6_fair_attestation/D3D_FAIR_RO6_ATTESTATION.json`, 4.133 byte, SHA256 `320344b6cfb74042e450bac4347f5a8b820e5702fa4b15c3bf4ff240ec764ec0`; sidecar SHA verificato. JSON valido, schema identifier `ARCANA_D3D_FAIR_RO6_ATTESTATION_V1`; non è stata trovata una definizione schema separata nel repository.
- Report consolidato `docs/arcana/SI1_BW1_F2B_D3D_RO6_FAIR_EVIDENCE_CONSOLIDATION.md`, SHA256 `1b9c46b43079fbc5002d3719bc935175cd6f1bea5489f6026abe7d870e1a4579`. Distingue verifiche locali del JSON/sidecar dalle osservazioni Fair registrate nel JSON.
- RO6 riferisce cinque membri selezionati (incluso il binary compile-only): i due binary copies del run coincidono tra loro e con i digest manifest registrati; compile-only è distinto; build/MPI logs selezionati corrispondono. Non è un controllo dei 79 membri del manifest run (`full_manifest_membership_verified=false`). I raw artifacts non accompagnano l'attestazione trasferita.
- Il JSON registra NVFORTRAN 25.11-0, OpenRTE 4.1.9a1 e due rank. Identità delle librerie effettivamente caricate, ABI completa e linkage storico restano non attestati.
- Codice storico 75, stop pre-Solver; decisione originale `BLOCKED_F2AV_QUALIFICATION` immutata. Limiti 32 GiB/processo e 80 GiB aggregati restano dichiarati, cgroup non verificato; nessun RSS/PSS. L'assenza di accounting nei percorsi RO5 circoscritti non prova assenza globale.
- Esito `D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE`. Il precedente report D3D bloccato resta immutato come record del tentativo Windows. Nessun originale modificato; nessun Solver, MPI, build o job eseguito in questa consolidazione.
- Nessun originale o output Fair è stato modificato; nessuna nuova esecuzione HPC. Pubblicazione immutabile JSON+sidecar+manifest di bundle sul branch evidence è proposta separata e non eseguita. Gate preservati: `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-D3D — acquisizione evidenze Fair preesistenti (2026-10-10)
- Esito bloccato: `D3D_BLOCKED_EXISTING_EVIDENCE_UNAVAILABLE`; `REMOTE_EVIDENCE_ACCESS_UNAVAILABLE`. Report `docs/arcana/SI1_BW1_F2B_D3D_EXISTING_FAIR_EVIDENCE_ACQUISITION.md`; SHA256 aggiornato registrato in `EVIDENCE_INDEX.md`.
- Nessun accesso Fair è stato effettuato e nessun artefatto Fair è stato acquisito. L'esistenza o assenza dei file remoti non è stata verificata; il blocco riguarda esclusivamente l'accesso in questo ambiente.
- Prossimo task resta acquisire in sola lettura le evidenze Fair preesistenti da un operatore con accesso già autorizzato, usando i due locator in `NEXT_ACTION.md`. Non è un nuovo run HPC.
- Preservati `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-D3C — Fair runtime/resource authority reconnaissance (2026-10-10)
- Decisione `D3C_RECONNAISSANCE_COMPLETE__EXECUTION_AUTHORITY_GAPS_REMAIN`; report `docs/arcana/SI1_BW1_F2B_D3C_FAIR_RUNTIME_RESOURCE_RECONNAISSANCE.md`, SHA256 `76a5a65adbbc7d6a9b6a64b35497ee9cd3f4642f286d672579d2779f7f53d058`.
- L'identità upstream storicamente qualificata non prova l'identità F2A-V. Il binario del run F2A-V non ha SHA256 verificato; ABI, linkage dinamico e toolchain effettiva non sono attestati. Nessun eseguibile candidato F2B è stato identificato.
- RSS/PSS/cgroup, headroom Fair e limiti memoria/tempo effettivamente imposti non sono dimostrati. Le formule D3A restano stime condizionali alle ipotesi ABI e non rappresentano RSS o un limite superiore. Due test symlink restano `NOT_TESTED_RUNTIME_WINDOWS`.
- D3C è stata ricognizione delle sole evidenze locali: nessun accesso Fair, job, MPI, ShellSet o Solver. Prossimo gate proposto `F2B-D3D — FAIR_EXISTING_EVIDENCE_ACQUISITION`, acquisizione read-only di evidenze preesistenti; non autorizza job, build o diagnostici.
- Preservati `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-D3B-P0 — bounded offline validator consolidation (2026-10-10)
- Esito della review indipendente: `D3B_P0_REVIEW_PASS_WITH_BOUNDED_SCOPE`; commit sorgente/consolidamento: questo checkpoint documentale, parent baseline `f571516ce09c726bffd262d172a922968bdab944`.
- Validatori e test: `scripts/r6_si1_bandwidth_f2b_d3b_resource.py`, `scripts/r6_si1_bandwidth_f2b_d3b_numerical.py`, `tests/test_r6_si1_bandwidth_f2b_d3b_resource.py`, `tests/test_r6_si1_bandwidth_f2b_d3b_numerical.py`; SHA256 rispettivi `cae86cd5d16d3f4633d45a9ae4ffb6a9808838c41fd2c8ac6e3bf317f5c548ae`, `275714d7615cffa062c8ac1d4a992edd5a2070744653a6b4cf0cfec914e7b46e`, `7e2ddf108836229e79475ffe47b2f2cd19d256beaa8459bd51451b93b1c2fec1`, `5b00d4a6b4220b0675183e43a1f028572a437825bfc383ce55d3b9cd1a8ce8aa`.
- D3B-P0: 24 test PASS, 2 SKIPPED, 0 FAIL. I quattro rilievi della prima review e il rilievo HIGH TOCTOU sono chiusi nel perimetro statico/sintetico. Il parser usa i byte dello snapshot autenticato; manifest e membri sono verificati, con identità Git storica separata e non autenticata dal validatore.
- Limiti: i due test runtime symlink sono `NOT_TESTED_RUNTIME_WINDOWS` perché Windows ha negato la creazione; WSL non era accessibile. La protezione POSIX con dir-fd/O_NOFOLLOW non è stata eseguita. Su Windows non è attestata atomicità contro sostituzioni concorrenti. ABI NVHPC reale, memoria/RSS e limiti Fair restano non attestati; nessuna qualificazione dell'operatore SI1.
- Preservati `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. Rapporti D3/D3A e SHA256 invariati.
- Prossimo gate proposto: `F2B-D3C — FAIR_RUNTIME_AND_RESOURCE_AUTHORITY_RECONNAISSANCE`, read-only; nessun job o Solver.

## F2B-D1A — publication of derived evidence (2026-10-10)
- Code branch `r6/si1-bandwidth-f2av`, attestor/tests + five ledger documents published at commit `d539a9ffa281d3dac8489db4820715cb136e9ae6`; code commit contains no output artifacts.
- Evidence branch `evidence/r6-bw1-f2av-20261010` at commit `c6bc94c0cac134146722b0c751f55255c68f03dc` adds `evidence/F2B_D1A_ATTESTATION_d539a9ff_20261010.tar.gz` through Git LFS and the matching tracked `.sha256` sidecar. Archive digest `b9fc3a7053e5c18a3d38e67ae367f418e5041f018d3ac9eafe82fa3dce1e9f9d`, verified against remote sidecar and local operator log.
- Internal D1A manifest SHA256 `5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a`; D1A result SHA256 `74328b449f41fbf7b467582adb53715c518a09327807401a1dbb4a789aff07a9` (according to Windows independent verification and reproducibility report). This session verified the GitHub pointer/sidecar, not the downloaded LFS payload. Preserved `DOF_MAPPING_PARTIAL` and geographic basis `DOF_MAPPING_UNVERIFIED`; original F2AV remains `BLOCKED_F2AV_QUALIFICATION`.
- Provenance nuance: recorded D1A execution checkout HEAD `f7b66b2276ef9c33af7012f453b0f01902575cd6` was before committing the attestor; revised attestor rerun on the same worktree reproduced exact output hashes, and code was subsequently committed at `d539a9ffa281d3dac8489db4820715cb136e9ae6`. Do not falsely label the result as executed from the committed `d539a9ffa281d3dac8489db4820715cb136e9ae6` checkout.
- Current next scientific-engineering task is F2B-D1B static geographic basis provenance audit; F2B-D2/D3 distinct. `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; no canonical evolution.

**Data ricognizione:** 2026-10-10. **Authority:** questa pagina è un indice operativo, non un seal scientifico. In caso di conflitto prevalgono result, manifest, source lock e contratti originali verificati.

## Aggiornamento corrente — F2B-D3 (2026-10-10)
- Report: `docs/arcana/SI1_BW1_F2B_D3_RESOURCE_RESIDUAL_PREFLIGHT_DESIGN.md`; SHA256 `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF`. Static design review against historical ShellSet source `df670c8c4faaed641997f5c4bdb701e2ba0afc7d` and the existing SI1/F2A-V evidence; no new measurements or execution were performed.
- Esito: `D3_DESIGN_COMPLETE_PENDING_RESOURCE_AND_NUMERICAL_ATTESTATION`. Formula source-derived: `8*nKRows*nRank = 2,249,799,104` bytes for the band array at the recorded dimensions. Explicit-array subtotal is conditional on stated ABI assumptions; total RSS/job memory, Fair-enforced limits, and runtime/library overhead remain unknown. DGBSV overwrites band A and RHS, so exact A0/b0 identity must be preserved or reproducibly re-established before any residual validation.
- Residual/backward-error definitions are proposed, not qualified acceptance criteria. `THRESHOLD_UNJUSTIFIED` remains. `INFO=0` is not a residual, conditioning, or scientific-validity result. No Solver execution or numerical result is authorized.
- Preserved: `DOF_MAPPING_PARTIAL`; `DOF_COMPONENT_BASIS_SOURCE_VERIFIED__F2AV_GEOGRAPHIC_ATTRIBUTION_UNADJUDICATED`; `OPERATOR_CLASS_UNVERIFIED`; original `BLOCKED_F2AV_QUALIFICATION`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`.
- Next proposed gate: F2B-D3A, preliminary non-executing resource/numerical attestation and control verification only. It does not authorize Fair MPI/ShellSet, Solver, factorization, assembly, mechanics, gauge, simulation, or canonical evolution.

## Aggiornamento corrente — F2B-D3A (2026-10-10)
- Audit: `docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md`; SHA256 `CA2FF09491BBDCB995FC79FB9E4CF66B461C519A2FC67F652E09099C70884989`. Decisione `D3A_AUDIT_COMPLETE__SOLVER_PREFLIGHT_NOT_ATTESTABLE_FROM_CURRENT_EVIDENCE`; audit offline e non esecutivo. Il report D3 originario, SHA256 `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF`, rimane invariato.
- Erratum aritmetico: D3 riportava circa `4.82684 GiB` per la variante con A0/b0. D3A corregge il totale a `5,183,806,076 byte + 112 × (LRn+1)` (circa `4.82780 GiB` più il termine LR). La differenza è la contabilizzazione completa della copia RHS b0 (`1,031,072 byte`); nessuna copia è stata allocata né la strategia selezionata.
- D3A ha verificato offline formule e array nominati sotto assunzioni ABI esplicite; il subtotal non è un limite superiore della memoria reale. RSS/PSS/cgroup, limiti Fair effettivi, temporanei e identità runtime/binari restano non attestati. Nessun test o comando Fair/MPI/Solver è stato eseguito in D3A.
- Preservati `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- Prossimo workpack proposto: F2B-D3B-P0, validatori Python offline e sintetici più procedura Fair read-only separata; nessuna autorizzazione Solver.

## Aggiornamento corrente — F2B-D1B (2026-10-10)
- Checkout: branch `r6/si1-bandwidth-f2av`, HEAD `d539a9ffa281d3dac8489db4820715cb136e9ae6`. Audit source read-only del commit ShellSet storico `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`; report `docs/arcana/SI1_BW1_F2B_D1B_GEOGRAPHIC_BASIS_AUDIT.md`, SHA256 `baa9e450f866f29a42230ad01bd490de6ed6c96f02df3d901e6af77388a41546`.
- Esito limitato: component basis ShellSet dimostrata nel proprio frame sferico: slot 1 = +South/+theta (North = −slot 1); slot 2 = +East/+phi. Source ordering, angular-velocity projection, boundary transform e output concordano nelle routine citate.
- Non adjudicato: autorità del frame per ARCANA, policy globale completa al meridiano, geografia/placche/causa delle dieci asimmetrie. `DOF_MAPPING_UNVERIFIED` resta obbligatorio per anomaly-to-geography/plate attribution; F2A-V resta `BLOCKED_F2AV_QUALIFICATION`.
- Nessun test scientifico/runtime eseguito; solo audit statico e `git diff --check`. Output D1A e F2A-V esistenti preservati. Prossimo gate proposto: F2B-D2 operator semantics; D3 risorse/residuo resta separato. Solver/Fair/MPI/fattorizzazione non autorizzati.

## Aggiornamento corrente — F2B-D1A (2026-10-10)
- Checkout verificato: branch `r6/si1-bandwidth-f2av`, HEAD `f7b66b2276ef9c33af7012f453b0f01902575cd6`; gli otto output recovery preesistenti sono stati preservati.
- Attestazione offline ripetibile: `outputs/r6_si1_bandwidth_f2b_d1a_attestation/`, decisione `DOF_MAPPING_PARTIAL`; manifest SHA256 `5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a`, result SHA256 `74328b449f41fbf7b467582adb53715c518a09327807401a1dbb4a789aff07a9`.
- PASS nello scope attestato: bijezione/inversa dei 64.442 nodi; 128.880 triangoli e 386.640 riferimenti; 64.442 record runtime / 3.222.100 campi; FEG/runtime staged byte-identici ai derivati BW1; 128.884 righe raw DOF mappate in due slot per nodo. La ripetizione in una directory distinta ha prodotto identità byte-for-byte uguali.
- Limite: mapping geografico delle componenti resta `DOF_MAPPING_UNVERIFIED`; le 10 coppie census sono ricondotte agli indici matrice/raw DOF ma attribuzione geografica o a placche è `PROHIBITED`. Il risultato originale `BLOCKED_F2AV_QUALIFICATION` e tutti i divieti Solver/mechanics/evoluzione restano invariati.
- Review finale D1A: output manifest/result SHA riprodotti esattamente dopo il rerun; attestatore ora ancora FEG/runtime agli SHA indipendenti del BW1 report e ai manifest identici ai blob Git HEAD, e limita output nuovi a `outputs/` fuori dagli alberi protetti. Regressioni: 11 passed; `py_compile`, JSON/manifest/membership, UTF-8/LF e `git diff --check` PASS.
- Prossimo gate: F2B-D1B, audit separato della provenienza della base geografica dei componenti; nessuna autorizzazione Solver/Fair/MPI/fattorizzazione.

## Aggiornamento corrente — F2B-D1 (2026-10-10)
- Repository branch `r6/si1-bandwidth-f2av`; sincronizzato in fast-forward a `595ed74788c3fa06cb4371affef121aacefb6670` dopo verifica di ascendenza e assenza di collisioni con i nove file non tracciati (documento D1 + otto recovery output). Dopo le correzioni di riferimenti e scope D1A, SHA256 finale D1 `7d8125bc40edaa0476a13e1dc03fc6c0a82c3fe48b23acdded0845ed18fe2ea0`; SHA iniziale prima della review `319eb9de615537ddd6abed09180dd04a83b654c02cad875a66d3d433835c93e4`.
- `F2B-D1 = DESIGN_COMPLETE_PENDING_ATTESTATION`, registrato in `docs/arcana/SI1_BW1_F2B_D1_DOF_PROVENANCE_CONTRACT.md`. È un design documentale; non attesta l'esecuzione dei controlli di contenuto e non cambia `DOF_MAPPING_UNVERIFIED`.
- `F2B-D1A` è la prossima azione: attestazione esaustiva offline della mappa nodo/permutazione/DOF, distinta dalla verifica della base geografica. Il design F2B di riferimento è `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md`.
- Restano invariati il risultato storico `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `FORWARD_EVOLUTION_AUTHORIZED=false` e `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Repositories / sincronizzazione
- Repo: `siegmound/ARCANA_WORLD`; branch di codice `r6/si1-bandwidth-f2av`, baseline codice `61dad0fabaa4f2bb72c386d85a77564894a91ce2` (fix writer e recovery) e ultimo checkpoint documentale `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`; rilevare HEAD live tramite Git, non inferirlo da questa pagina. Il run F2A-V originale resta vincolato a `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`.
- `WINDOWS_WORKTREE_ONLY`: le 4 modifiche writer/recovery/test **sono state committate e pubblicate** al commit `61dad0fabaa4f2bb72c386d85a77564894a91ce2`. Sul worktree Windows rimane non tracciato soltanto `outputs/r6_si1_bandwidth_f2av_offline_recovery/`, che è evidenza derivata, non codice. Backup del codice precedente confermato. Prima di qualsiasi sincronizzazione ricontrollare `git status` e l'eventuale collisione con file untracked.
- `MERGED_DEV_BRANCH`: PR #1 della bitacora **merged il 2026-10-10**, commit merge `a388e567aa48c3376da7d4a72b0c2c3e8d64f533`; verificata presenza di `PROJECT_LEDGER/`, `AGENTS.md` e script di recovery nel branch scientifico. Il code fix originale rimane nel commit `61dad0fa`; la recovery completa è ora pubblicata separatamente in Git LFS; la directory output locale resta untracked ed è da preservare.
- `EVIDENCE_LFS`: branch `evidence/r6-bw1-f2av-20261010` HEAD `2b03fa558b02cb865c4f234e45f0386fab678822` contiene original F2A-V, companion F2-A sealed e archivio recovery F2A-V completo; push LFS verificato tramite metadati remoti, intake/source integrity attestati dal run Windows.
- Fair: originali HPC immutabili, non serve pull del codice durante audit offline.

## Gate scientifico attuale
**Decisione della review offline Windows (resoconto Codex, 2026-10-10):** `GO_FOR_F2B_SOLVER_PREFLIGHT_DESIGN_ONLY` (etichetta operativa del ledger, NON un nuovo seal/contract di authorità). Sono ammessi lo studio del preflight e i test statici non-esecutivi; **Solver/F2-B execution non autorizzata**.

### Evidenze e risultati
- Originale F2A-V Fair: `BLOCKED_F2AV_QUALIFICATION` su parser `invalid saturation indicator` dopo MPI stop deliberato 75 prima del Solver; l'originale NON viene riscritto.
- Recovery completa Windows `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/`: `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`; result e 3 artefatti riconciliati nella review; manifest SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`. F2-A sealed manifest SHA256 `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`.
- Review: original F2A-V 79 membri manifest + manifest (80 file) intatti; CSV normalizzato solo swap colonne 6/7; cross-reference F2-A sealed passato. `139 passed, 2 skipped`, `py_compile`, JSON e `git diff --check` PASS; pytest primo lancio basetemp default fallito, rerun con --basetemp repository PASS. SciPy/BW0/BW1 non ancora interamente ricontrollati nel medesimo ambiente.
- Matrice: n=128884; kl=ku=727; nKRows=2182; 186996964 valid, 1804327 nonzero, 185192637 zero, nonfinite 0. REAL*8 band array 2249799104 byte stimati, non RSS globale. 93434040 coppie upper confrontate, 10 anomalie (1 zero/nonzero e 9 nonzero mismatch) a threshold rel `1e-12`. Max coefficient abs `3.6508239112970148E+032`; min nonzero `1.4073748835532800E+014`, circa 18.41 decadi. Dominanza strict 0, near 0, nonstrict 128884.
- Le 10 anomalie non hanno causa dimostrata; la simmetria teorica dell'operatore non è ancora provata. `DOF_MAPPING_UNVERIFIED`. Non esistono stime qualificate di condizionamento, spettro, singolarità o gauge. IEEE `underflow/inexact` inherited, cause ignote; nessun overflow/underflow per fase osservati nel report.

### Rischi che rimangono aperti
1. Correzione del writer F2A-V non ancora ricompilata/qualificata su Fair/NVHPC; il CSV recovery proviene dal writer precedente.
2. Manca test positivo automatico E2E recovery con F2-A sealed (run reale controllato dalla review).
3. IEEE intrinsics/sticky flag comportamento da qualificare dove richiesto prima di fare affidamento su nuova instrumentation NVHPC.
4. Mappatura DOF raw -> permutation/node/component/geografia incompleta e classe dell'operatore/asimmetria/gauge non accertate.
5. R6 B6N5 post-rift è un **blocco di autorità fisica separato**; ShellSet engineering case usa parametri di riferimento NON ARCANA science authority.

## Autorizzazioni
`F2B_PREFLIGHT_DESIGN_ALLOWED=true` (solo design; decisione operativa);
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`FORWARD_EVOLUTION_AUTHORIZED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
L'esecuzione parallela ShellSet su upstream ListEx1 9/9 è già evidenziata: non ripetere come nuovo gate. **Prossima attività:** `NEXT_ACTION.md`.

## Integrazione documentale — 2026-10-10
`PROJECT_LEDGER/` è presente nel branch `r6/si1-bandwidth-f2av` dopo merge PR #1 (SHA `a388e567aa48c3376da7d4a72b0c2c3e8d64f533`). Lo stato di questo file è quello successivo al merge; nuove chat leggono `AGENTS.md` e `PROJECT_LEDGER/NEW_CHAT.md` senza recuperare una branch docs separata. Windows ha confermato `PASS_R6_LEDGER_SYNC` fino al checkpoint `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`; aggiornamenti successivi richiedono nuovo fetch/fast-forward non distruttivo. Nessun nuovo dato numerico pubblicato da questa integrazione.

## F2A-V recovery complete — published derived evidence (2026-10-10)
- Evidence commit: `2b03fa558b02cb865c4f234e45f0386fab678822` on `evidence/r6-bw1-f2av-20261010`.
- Git LFS archive: `evidence/F2AV_OFFLINE_RECOVERY_F2AV_WITH_F2A_REFERENCE_V1.tar.gz`, archive SHA256 `bdde8d4320b1fa6de577988bf911817918e910373bdbff9922c9d9c98f646562` matched remote sidecar and reported Windows digest.
- Derived recovery manifest SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`; 3 artifact members plus manifest, source integrity PASS in Windows procedure. Binary payload not independently downloaded in this session.
- Transport `PASS_F2AV_RECOVERY_EVIDENCE_PUSH`; original Fair decision `BLOCKED_F2AV_QUALIFICATION` unchanged; no new solver authority.
- NEXT: F2-B preflight **design only**, see `NEXT_ACTION.md`.

## F2-B design reconnaissance received — 2026-10-10
- Codex read-only reconnaissance eseguita sul **checkout Windows HEAD `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`** (il remoto era già `bb3b6c781e6d8dac20c446ab9b0e97fe634cb61d`). Stato locale report: nessuna modifica tracciata, 8 file untracked nelle recovery output; nessun test o run eseguito.
- Fonte: report operatore/Codex, **non sealed artifact**. La ricognizione individua due componenti DOF per nodo, permutazioni candidate `new_to_old/old_to_new` e stage FEG/runtime, ma il collegamento end-to-end a raw F2A-V e base geografica resta `DOF_MAPPING_UNVERIFIED`.
- `DGBSV` generale a banda, matrix+RHS overwritten; `INFO=0` non verifica residuo. Zero BC velocity e zero fault; nullspace/gauge `UNKNOWN`; nessuna simmetrizzazione, nessuna stima condizionamento.
- **Disponibile su GitHub:** `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` (design derivato, non gate solver).
- **NEXT:** `F2B-D1` DOF/permutation provenance attestation design; F2B-E solve/fattorizzazione ancora `NOT_AUTHORIZED`. Nessun nuovo run Fair/MPI/Solver autorizzato.

## F2B-D2 operator classification audit — 2026-10-10
- Report: docs/arcana/SI1_BW1_F2B_D2_OPERATOR_CLASSIFICATION_AUDIT.md; static audit on historical ShellSet df670c8c4faaed641997f5c4bdb701e2ba0afc7d and existing F2A-V original/recovered evidence.
- Decision: OPERATOR_CLASS_UNVERIFIED; theoretical SI1 symmetry INDETERMINATE. BuildK exposes sufficient alpha reciprocity conditions, but effective tangent values at integration points were not retained. The ten asymmetries remain unexplained; absolute, pair-relative, and row-scaled measures are distinguished.
- BLOCKED_F2AV_QUALIFICATION remains unchanged. DOF_MAPPING_UNVERIFIED remains for geographic/plate attribution. Diagonal dominance is not used to infer nullspace or singularity.
- No assembly, Solver, factorization, Fair/MPI, gauge, simulation, or canonical/WORLD_HISTORY change; F2B_SOLVER_EXECUTION_AUTHORIZED=false.
- Next gate: F2B-D3 resource/residual acceptance design, without Solver execution.
## F2B-N2C-W3-C-B — stato corrente (2026-10-11)
- Decisione circoscritta: `W3C_B_SYNTHETIC_COORDINATOR_PROTOCOL_PASS__MPI_WIDE_STOP_AND_RUNTIME_AUTHORITY_UNPROVEN`.
- Modello immutabile CAPTURE_ONLY e test sintetici implementati nei file W3C-B; suite focalizzata Windows: 21 passed, 0 failed, 0 skipped. Il risultato riguarda soltanto transizioni del modello Python.
- Provenienza del modello: riusa `CallIdentity` W3-B e scope `SYNTHETIC_FIXTURE_ONLY`; nessuna authority owner-backed viene promossa. Source reachability del target first-FEM codificata come precondizione; guardia SF e semantica runtime restano da dimostrare.
- Stato runtime/scientifico invariato: `BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- MPI-wide agreement/stop, launcher behavior, real owner identities, SI1 capture e W4 scala/risorse non dimostrati. Prossimo gate limitato: review indipendente offline W3-C-C.
