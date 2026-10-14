# INT-2C-A — Executable replay binding preparation

Date: 2026-10-14. Branch: `r6/si1-bandwidth-f2av`. Entry HEAD:
`6a719da728baa11c4a972195d357fde7c32d21b3`, parent
`14208a1e4c4462414e571477a662ba3e06ca4a09`.

Decision: `INT2C_EXECUTABLE_REPLAY_BINDING_CODE_READY__NUMERICAL_VALIDATION_PENDING`.

INT-2B closure was published by a verified normal fast-forward from remote
`14208a1e4c4462414e571477a662ba3e06ca4a09` to the entry HEAD. The sandbox
fetch failed DNS; the authorized network retry succeeded. No history was rewritten.
The README's older NEXT summary is stale; current ledger and primary evidence
govern this task.

## Verified target and preserved evidence

The first target is the existing INT-0B R4 engineering trajectory, source execution
commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`, source-composite identity
`b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`.
The existing INT-1A loader authenticates all nine bundle members against externally
pinned manifest/member sizes and SHA256 before parsing. R4 manifest:
`191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.
The preparation also reuses its cross-artifact provenance validation.

Bundle: `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/`.
The original files, domain states, both checkpoints, forcing and recipe retain
their bytes and identifiers. The preparation produces typed records in memory;
it does not create a store or evidence directory. INT-1D remains a distinct later
validation case (manifest `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`),
read-only reverified by the relevant INT-2A regressions, without binding it to R4.

R4 uses pair 5:11, boundary `R6BND-T0-3eb57747e6f0a3f3305f`, supports
`R6G1D-R091-C029` and `R6G1D-R091-C028`, two complete 73-node initial states,
including every material property's value and fixed thermal boundaries.
The declared duration is 31,557,600,000 seconds (1,000 engineering years), frozen
Ux is 0.11467052868814648 m/year (3.6336897827511117e-9 m/s), and the reference
maximum kinematic fraction per substep is 0.0005. No parameter was selected anew.

Preserved original typed identities:

| Record | Identity |
|---|---|
| Initial state | `r6state_a4c9f8dc71cc77d52b6e5d54cd82c921e57e9de9f3c4ce740f7de91a98aac127` |
| Candidate state | `r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a` |
| Initial checkpoint | `r6checkpoint_7aa9a77c40f44803580e9ff342c92d25b94f960ca727f2356c529e93af01a70e` |
| Candidate checkpoint | `r6checkpoint_3c02b5fb6742be06172bb07ab9000b0d36700968f3d934ece21e1a916cbf0dc3` |
| Forcing | `r6forcing_f9eeb3808fd447bfb64f07d3ed88758fe840b12ee6d4d244373363389ad82983` |
| Recipe | `r6recipe_ab1ae762b061a097275426ee91efd11cafab37b7e9a9bb6f8e307c3da058abc0` |

The prepared in-memory candidate checkpoint is
`r6checkpoint_79c9e6c7d55cc745bbef746d4c28cbf2f5af625b3e94bb87840740a1d8db5f99`;
recipe is `r6recipe_c420c08f3d2600811bf39ffe9a78d8f8871979c323ce4e3332c0eebc49b5dfc2`;
closed configuration SHA256 is
`856a1e7b3662e64bd60e8d364b708163e356aac5fdc995cdb683ecd6fc6ef075`.
They bind adapter canonical-text SHA256
`3a44e797676ceac3a4764bdaa1311157f57910315ead3ea2e4aa20e740cfc11d`.
These identities describe preparation only, without storage or real replay validation.

## B0 compatibility audit

| Requirement | Existing evidence / source | Finding and prepared treatment |
|---|---|---|
| Typed states and forcing | `b0_domain_states`, `b0_forcing_record`; [state.py](../../src/arcana_worldsim/r6/state.py), [forcing.py](../../src/arcana_worldsim/r6/forcing.py) | Original records parse and retain identities; values, support/frame and source references are reused. Original authority labels describe their existing provider lineage; candidate applicability remains noncanonical and no physical authority is promoted. |
| Checkpoint eligibility | [checkpoint.py](../../src/arcana_worldsim/r6/checkpoint.py), [replay.py](../../src/arcana_worldsim/r6/replay.py) | Existing initial/candidate status is `CANDIDATE_NONCANONICAL`. B0 requires `VALIDATED` and rejects the original. No real validated checkpoint is emitted here. |
| Dependency closure | Original checkpoint/recipe `upstream_dependency_ids`; `validate_replay_inputs` | Lists differ: recipe additionally names the initial state; raw provider digests are not resolvable typed B0 records. A new candidate checkpoint and recipe share the exact typed initial-state, forcing and preparation-provenance dependencies. Raw artifact/provider digests remain source references/attributes on that provenance record. |
| Configuration | Original replay configuration SHA256 `bca2703563b1ca8c48ea5f7ba9363163abb63a0e94f1f533faf535b22e9b5e3b` | Exact historical configuration is reconstructed and rehashed, then nested inside a new closed configuration binding source bytes, runtime versions, support, initial payload identities and forcing ID. Original configuration/descriptor IDs remain unchanged. |
| Initial-state completeness | `CANDIDATE_CHECKPOINT.json`, trajectory initial envelope, `state_from_payload` | Exact side-payload equality, full roundtrip, materials, cardinality, numeric types/finiteness, geometry and material coordinates are verified. No provider reinitialization or reconstruction from expected final values occurs. |
| Numerical oracle | Candidate checkpoint, trajectory candidate envelope, `REPLAY_RESTART.json` | Both reference side payloads have historical pretty-JSON/LF SHA256 `2b4836954e688d7aac6d9e26ccb61aa02fa94e9e40550c395922b30fa1b45d7b`. These recorded hashes are recomputed read-only. B0 compact canonical state identity uses a different serialization; the two digests are not conflated. |
| Expected output / payload | Original state `r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a`; `execute_replay` | Expected state ID binds the complete inline state, including numerical arrays. Original `payload_ref` and recipe `expected_payload_identity` are null. The adapter returns inline state and no external payload; B0 compares the produced state ID. The expected values remain an oracle only. |
| Provenance | [provenance.py](../../src/arcana_worldsim/r6/provenance.py) | New preparation record binds source/member digests, original checkpoint/recipe IDs and provider lineage. It explicitly records no replay execution, canonical publication or authority promotion. Source lineage is not fresh physical qualification. |
| Historical kernel | Local Git blob at R4 execution commit, current imported kernel file | Independently compared after declared CRLF/CR→LF normalization: both SHA256 `bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542`. This covers the actual step, restoration, thermal update and state checks in `functional_development.py`; it is not authentication of every historical dependency binary. |
| Runtime | R4 declared Python 3.12.10 / NumPy 2.3.5 | Adapter requires these exact versions and kernel/adapter source digests. Historical interpreter/NumPy binary identities, platform equivalence and cross-runtime reproducibility remain UNKNOWN. A version match alone does not prove determinism. |

No B0 core adaptation is currently necessary. B0's checkpoint validation gate is
separate from state authority/applicability. It can express a technically validated,
noncanonical engineering input closure through a **new** checkpoint identity with
an explicit technical-only restart compatibility scope, while preserving candidate
records and scientific limitations. Such a real transition has not been issued.
The tests use `VALIDATED` only for explicitly `FIXTURE_ONLY` records and prove that
the real prepared candidate remains blocked by the unchanged B0 check.

## Focused adapter and data flow

[r6_int2c_replay_adapter.py](../../scripts/r6_int2c_replay_adapter.py) provides
`prepare_r4(repository_root, bundle_root)` and `DeterministicKernelAdapter`.
Preparation authenticates the source bundle and historical/current kernel, parses
all historical typed descriptors and returns nine records: two original states,
forcing, both original checkpoints and recipe, preparation provenance, and the
new candidate checkpoint/recipe. Their input closure is consistent; the original
descriptor incompatibilities are preserved as historical evidence.

The adapter accepts only the exact declared B0 closure and an explicitly
technically validated checkpoint. It checks configuration, source/runtime,
initial payloads, support, forcing, provenance, dependency lists and scope before
kernel entry. It restores states from initial payloads and calls the existing
`pure_shear_thermal_step` for each side with declared duration, Ux converted to
m/s, and reference fraction. It constructs the output from the initial envelope
and predicted payloads. It never uses `expected_state.value` to generate output.
There is no execution CLI, status-promotion routine or alternative storage/query
framework. Canonical path names are rejected before the bundle reader is called.

## Offline verification actually performed

[Tests](../../tests/test_r6_int2c_replay_adapter.py): 24 contract tests. All adapter
dispatch tests replace the numerical kernel with a small test-only mock; a B0
`VERIFIED` result in those tests means fixture wiring only. The real R4 kernel
is never invoked. Coverage includes deterministic record identities/typed
roundtrips, candidate-status rejection, complete synthetic B0 closure, exact
dispatch arguments, poisoned expected oracle, output mismatch, absent/altered
forcing, wrong support/material/source/configuration/scope, invalid duration,
incomplete or malformed initial payload, missing provenance/dependency,
historical/runtime mismatch, immutable configuration and canonical path rejection.

Combined INT-2C-A/INT-1A/INT-2A/INT-2B suite: **58 passed, 0 failed, 0 skipped,
1 deselected**. The deselected test is the existing actual `HistoryStore`
registration/query test; Windows hard-link publication is known restricted and
was not attempted. Python 3.12.10, existing pytest 8.4.2 and existing bundled NumPy
2.3.5 were used through temporary `PYTHONPATH`; no dependency was installed.
`py_compile`, UTF-8/LF, reference and diff checks are part of the final closure.
No new numerical or scientific evidence bundle was produced.

## Remaining conditions and next bounded action

Review and technically attest the new R4 input closure, retaining the original
candidate status/IDs, then authorize one bounded B0-integrated replay separately.
Actual atomic registration/readback and reopened-store dependency resolution must
run on a supported filesystem, such as an already authorized Fair environment,
using the existing `HistoryStore.append_transaction` and `validate_replay_inputs`.
The Windows read-only fixture checks do not qualify persistence or publication.

The known Fair Conda Python 3.12.14 differs from the declared replay version
3.12.10; the adapter will reject that runtime for numerical execution. Resolve the
execution environment or explicitly review/qualify a new runtime binding before
running. Do not silently weaken the check. The later execution must record actual
runtime identities/resources and verify the full inline state ID and historical
per-side output payload hashes, with any mismatch preserved as failure. Reusing
observations or returning the oracle cannot qualify executable replay.

No new engineering trajectory, real numerical replay, provider evaluation, Fair
job, MPI, ShellSet, Solver, mechanics or canonical operation occurred. Gates stay:
`BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`,
`RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
